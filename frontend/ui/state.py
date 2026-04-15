"""Estado global de la aplicación Reflex."""
import reflex as rx
import httpx
import json

# JS para hacer scroll al fondo del contenedor de chat
SCROLL_BOTTOM_JS = """
setTimeout(function() {
    var el = document.getElementById('chat-container');
    if (el) { el.scrollTop = el.scrollHeight; }
}, 100);
"""


class State(rx.State):
    """Estado reactivo principal de JARVIS Mini."""
    chat_history: list[dict[str, str]] = [
        {"role": "assistant", "content": "¡Hola! Soy **JARVIS Mini**. Sube documentos en el panel lateral y pregúntame lo que necesites saber."}
    ]
    current_question: str = ""
    is_processing: bool = False
    stats: str = ""
    mode: str = "rag"
    model: str = "qwen-3.5-0.8b"

    def set_current_question(self, value: str):
        self.current_question = value

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Sube archivos al backend y los indexa en FAISS."""
        self.is_processing = True
        yield
        upload_data = []
        for file in files:
            content = await file.read()
            upload_data.append(('files', (file.filename, content, file.content_type)))
        if not upload_data:
            self.is_processing = False
            return
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post("http://localhost:8000/api/ingest", files=upload_data)
                if response.status_code == 200:
                    data = response.json()
                    chunks = data.get('indexed_chunks', 0)
                    self.stats = f"✅ {chunks} fragmentos indexados."
                else:
                    self.stats = f"❌ Fallo: {response.text}"
        except Exception as e:
            self.stats = f"⚠️ Error: {str(e)}"
        self.is_processing = False
        yield

    async def handle_key_down(self, key: str):
        """Captura Enter para scrollear y enviar la pregunta."""
        if key == "Enter":
            return [rx.call_script(SCROLL_BOTTOM_JS), State.handle_submit_query]

    async def handle_submit_query(self):
        """Envía la pregunta al backend con streaming SSE."""
        if not self.current_question.strip():
            return

        question = self.current_question
        self.current_question = ""
        self.chat_history.append({"role": "user", "content": question})
        self.chat_history.append({"role": "assistant", "content": ""})
        self.is_processing = True
        yield

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                async with client.stream(
                    "POST",
                    "http://localhost:8000/api/query/stream",
                    json={"query": question, "mode": self.mode, "model": self.model}
                ) as response:
                    sources = []
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = json.loads(line[6:])
                        token = payload.get("token", "")
                        done = payload.get("done", False)
                        if token:
                            self.chat_history[-1]["content"] += token
                            yield
                        if done:
                            sources = payload.get("sources", [])
                    if sources:
                        self.chat_history[-1]["content"] += f"\n\n*Fuentes: {', '.join(sources)}*"
        except Exception as e:
            self.chat_history[-1]["content"] = f"⚠️ Error de conexión: {str(e)}"

        self.is_processing = False
        yield
