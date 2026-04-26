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
    mode: str = "rag"
    model: str = "qwen-3.5-0.8b"
    documents: list[dict[str, str]] = []
    accordion_value: str = "documents"  # Por defecto abierto

    def toggle_accordion(self, value: str | list[str]):
        """Actualiza el estado del item abierto del acordeón."""
        self.accordion_value = value if isinstance(value, str) else (value[0] if value else "")

    def reset_chat(self):
        """Reinicia el historial de chat a su estado inicial."""
        self.chat_history = [
            {"role": "assistant", "content": "¡Hola! Soy **JARVIS Mini**. Sube documentos en el panel lateral y pregúntame lo que necesites saber."}
        ]
        self.current_question = ""

    def set_current_question(self, value: str):
        self.current_question = value

    async def load_documents(self):
        """Carga la lista de documentos indexados desde el backend."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:8000/api/index/documents")
                if response.status_code == 200:
                    self.documents = response.json()
        except Exception:
            pass

    async def delete_document(self, source: str):
        """Elimina un documento del índice y recarga la lista."""
        import urllib.parse
        try:
            safe_source = urllib.parse.quote(source)
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(f"http://localhost:8000/api/index/documents/{safe_source}")
                if response.status_code == 200:
                    yield rx.toast.success(f"'{source}' eliminado del índice.", duration=10000)
                else:
                    yield rx.toast.error(f"Error eliminando: {response.text}", duration=10000)
        except Exception as e:
            yield rx.toast.error(f"Error: {str(e)}", duration=10000)
        await self.load_documents()
        yield

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
                    yield rx.toast.success(f"{chunks} fragmentos indexados.", duration=10000)
                else:
                    yield rx.toast.error(f"Fallo: {response.text}", duration=10000)
        except Exception as e:
            yield rx.toast.error(f"Error: {str(e)}", duration=10000)
        self.is_processing = False
        await self.load_documents()
        yield

    async def handle_submit_query(self, form_data: dict = None):
        """Envía la pregunta al backend con streaming SSE."""
        if not self.current_question.strip():
            return

        question = self.current_question
        self.current_question = ""
        self.chat_history.append({"role": "user", "content": question})
        self.chat_history.append({"role": "assistant", "content": ""})
        self.is_processing = True
        yield

        history_payload = []
        # Enviar últimos 6 mensajes válidos ignorando el saludo inicial[0] y los 2 recién añadidos[-2]
        for msg in self.chat_history[1:-2][-6:]:
            if "⚠️ Error" in msg["content"]: continue
            # Limpiamos la firma automática de las fuentes para no marear al bot
            clean_content = msg["content"].split("\n\n*Fuentes:")[0].replace("📡 Base de Conocimiento Interna (LLM)", "")
            history_payload.append({"role": msg["role"], "content": clean_content})

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                async with client.stream(
                    "POST",
                    "http://localhost:8000/api/query/stream",
                    json={
                        "query": question, 
                        "mode": self.mode, 
                        "model": self.model,
                        "history": history_payload
                    }
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
