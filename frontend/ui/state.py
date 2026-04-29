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
    active_sidebar_section: str = "watch"
    # Watch folder
    watch_folders: list[dict] = []
    watch_running: bool = False
    system_stats: dict = {
        "process_cpu_percent": 0.0,
        "process_memory_mb": 0.0,
        "process_memory_percent": 0.0,
        "system_cpu_percent": 0.0,
        "system_memory_percent": 0.0,
        "disk_percent": 0.0,
        "threads": 0,
    }
    system_stats_history: list[dict] = []
    system_chart_data: list[dict[str, float | int]] = []
    new_watch_path: str = ""
    delete_document_modal_open: bool = False
    remove_watch_modal_open: bool = False
    pending_document_source: str = ""
    pending_watch_path: str = ""

    def toggle_documents_accordion(self, value: str | list[str]):
        self.active_sidebar_section = "documents"

    def toggle_documents_section(self):
        self.active_sidebar_section = "documents"

    def toggle_watch_accordion(self, value: str | list[str]):
        self.active_sidebar_section = "watch"

    def toggle_watch_section(self):
        self.active_sidebar_section = "watch"

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

    def open_delete_document_modal(self, source: str):
        self.pending_document_source = source
        self.delete_document_modal_open = True

    def close_delete_document_modal(self):
        self.delete_document_modal_open = False
        self.pending_document_source = ""

    def open_remove_watch_modal(self, path: str):
        self.pending_watch_path = path
        self.remove_watch_modal_open = True

    def close_remove_watch_modal(self):
        self.remove_watch_modal_open = False
        self.pending_watch_path = ""

    def confirm_delete_document(self):
        source = self.pending_document_source
        self.close_delete_document_modal()
        if source:
            return State.delete_document(source)
        return None

    def confirm_remove_watch(self):
        path = self.pending_watch_path
        self.close_remove_watch_modal()
        if path:
            return State.remove_watcher(path)
        return None

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
                    self.watch_folders = data.get("folders", [])
        except Exception:
            pass

    def _push_system_stats_sample(self, sample: dict):
        """Guarda muestra de consumo manteniendo las ultimas 5 lecturas."""
        self.system_stats = sample
        history = list(self.system_stats_history)
        history.append(sample)
        self.system_stats_history = history[-5:]
        self.system_chart_data = [
            {
                "sample": idx + 1,
                "cpu_proc": float(item.get("process_cpu_percent", 0.0)),
                "ram_proc": float(item.get("process_memory_percent", 0.0)),
                "cpu_system": float(item.get("system_cpu_percent", 0.0)),
                "ram_system": float(item.get("system_memory_percent", 0.0)),
            }
            for idx, item in enumerate(self.system_stats_history)
        ]

    async def load_system_stats(self):
        """Carga metricas de consumo del backend."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:8000/api/stats/system")
                if response.status_code == 200:
                    self._push_system_stats_sample(response.json())
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
                    json={"path": path, "recursive": True}
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

    async def pause_watcher(self, path: str):
        """Pausa vigilancia de una ruta configurada."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post("http://localhost:8000/api/index/watch/pause", json={"path": path})
                if response.status_code == 200:
                    yield rx.toast.info(f"Vigilancia pausada: {path}")
                else:
                    detail = response.json().get("detail", response.text)
                    yield rx.toast.error(f"Error: {detail}")
        except Exception as e:
            yield rx.toast.error(str(e))
        await self.load_watch_status()

    async def resume_watcher(self, path: str):
        """Reanuda vigilancia de una ruta pausada."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post("http://localhost:8000/api/index/watch/resume", json={"path": path})
                if response.status_code == 200:
                    yield rx.toast.success(f"Vigilancia reanudada: {path}")
                else:
                    detail = response.json().get("detail", response.text)
                    yield rx.toast.error(f"Error: {detail}")
        except Exception as e:
            yield rx.toast.error(str(e))
        await self.load_watch_status()
        await self.load_documents()

    async def unindex_watcher(self, path: str):
        """Detiene y elimina documentos del índice."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post("http://localhost:8000/api/index/watch/unindex", json={"path": path})
                if response.status_code == 200:
                    yield rx.toast.warning(f"Carpeta desindexada: {path}")
                else:
                    detail = response.json().get("detail", response.text)
                    yield rx.toast.error(f"Error: {detail}")
        except Exception as e:
            yield rx.toast.error(str(e))
        await self.load_watch_status()
        await self.load_documents()

    async def remove_watcher(self, path: str):
        """Elimina completamente de la configuración."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post("http://localhost:8000/api/index/watch/remove", json={"path": path})
                if response.status_code == 200:
                    yield rx.toast.error(f"Watch Folder eliminado: {path}")
                else:
                    detail = response.json().get("detail", response.text)
                    yield rx.toast.error(f"Error: {detail}")
        except Exception as e:
            yield rx.toast.error(str(e))
        await self.load_watch_status()
        await self.load_documents()

    async def toggle_all_watchers(self):
        """Atajo global para pausar/reanudar todas las rutas."""
        endpoint = "pause-all" if self.watch_running else "resume-all"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"http://localhost:8000/api/index/watch/{endpoint}")
                if response.status_code == 200:
                    if endpoint == "pause-all":
                        yield rx.toast.info("Vigilancia pausada en todas las carpetas.")
                    else:
                        yield rx.toast.success("Vigilancia reanudada en todas las carpetas.")
                else:
                    detail = response.json().get("detail", response.text)
                    yield rx.toast.error(f"Error: {detail}")
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
                        system_resp = await client.get("http://localhost:8000/api/stats/system")
                        
                        if doc_resp.status_code == 200:
                            self.documents = doc_resp.json()
                        if watch_resp.status_code == 200:
                            data = watch_resp.json()
                            self.watch_running = data.get("running", False)
                            self.watch_folders = data.get("folders", [])
                        if system_resp.status_code == 200:
                            self._push_system_stats_sample(system_resp.json())
                    except Exception:
                        pass
            yield

    async def stop_watcher(self, path: str):
        # Compatibilidad hacia atrás.
        await self.pause_watcher(path)

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

