"""Estado global de la aplicación Reflex."""
import reflex as rx
import httpx
import json
import asyncio

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
    # Watch folder
    watch_folders: list[str] = []
    watch_running: bool = False
    new_watch_path: str = ""

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

    def set_new_watch_path(self, value: str):
        self.new_watch_path = value

    async def load_documents(self):
        """Carga la lista de documentos indexados desde el backend."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:8000/api/index/documents")
                if response.status_code == 200:
                    self.documents = response.json()
        except Exception:
            pass

    async def load_watch_status(self):
        """Carga el estado del watcher desde el backend."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:8000/api/index/watch/status")
                if response.status_code == 200:
                    data = response.json()
                    self.watch_running = data.get("running", False)
                    self.watch_folders = data.get("paths", [])
        except Exception:
            pass

    async def select_folder_dialog(self):
        """Abre el diálogo de selección de carpeta en el servidor."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get("http://localhost:8000/api/index/watch/select-folder")
                if response.status_code == 200:
                    path = response.json().get("path", "")
                    if path:
                        self.new_watch_path = path
        except Exception as e:
            yield rx.toast.error(f"Error al abrir selector: {str(e)}")

    async def start_watcher(self):
        """Activa la vigilancia de la carpeta introducida."""
        path = self.new_watch_path.strip()
        if not path:
            yield rx.toast.warning("Introduce una ruta de carpeta.", duration=5000)
            return
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "http://localhost:8000/api/index/watch/start",
                    json={"path": path}
                )
                if response.status_code == 200:
                    self.new_watch_path = ""
                    yield rx.toast.success(f"Watch Folder activado: {path}", duration=8000)
                else:
                    detail = response.json().get("detail", response.text)
                    yield rx.toast.error(f"Error: {detail}", duration=10000)
        except Exception as e:
            yield rx.toast.error(f"Error de conexión: {str(e)}", duration=10000)
        await self.load_watch_status()
        await self.load_documents()
        yield

    async def untrack_watcher(self, path: str):
        """Deja de vigilar pero mantiene en la lista."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post("http://localhost:8000/api/index/watch/untrack", json={"path": path})
                yield rx.toast.info(f"Vigilancia pausada: {path}")
        except Exception as e:
            yield rx.toast.error(str(e))
        await self.load_watch_status()

    async def unindex_watcher(self, path: str):
        """Detiene y elimina documentos del índice."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post("http://localhost:8000/api/index/watch/unindex", json={"path": path})
                yield rx.toast.warning(f"Carpeta desindexada: {path}")
        except Exception as e:
            yield rx.toast.error(str(e))
        await self.load_watch_status()
        await self.load_documents()

    async def remove_watcher(self, path: str):
        """Elimina completamente de la configuración."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post("http://localhost:8000/api/index/watch/remove", json={"path": path})
                yield rx.toast.error(f"Watch Folder eliminado: {path}")
        except Exception as e:
            yield rx.toast.error(str(e))
        await self.load_watch_status()
        await self.load_documents()

    @rx.event(background=True)
    async def update_loop(self):
        """Tarea en segundo plano para actualizar documentos en tiempo real."""
        while True:
            await asyncio.sleep(5)
            async with self:
                # Actualizar lista de documentos y estado de watchers
                async with httpx.AsyncClient() as client:
                    try:
                        doc_resp = await client.get("http://localhost:8000/api/index/documents")
                        watch_resp = await client.get("http://localhost:8000/api/index/watch/status")
                        
                        if doc_resp.status_code == 200:
                            self.documents = doc_resp.json()
                        if watch_resp.status_code == 200:
                            data = watch_resp.json()
                            self.watch_running = data.get("running", False)
                            self.watch_folders = data.get("paths", [])
                    except Exception:
                        pass
            yield

    async def stop_watcher(self, path: str):
        # Mantenemos este por compatibilidad si se usa en otros sitios, 
        # pero ahora preferimos untrack/unindex/remove
        await self.untrack_watcher(path)

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
