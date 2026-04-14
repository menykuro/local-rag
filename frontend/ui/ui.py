import reflex as rx
import httpx

class State(rx.State):
    """The app state keeping reactivity for chat and settings."""
    chat_history: list[dict[str, str]] = [
        {"role": "assistant", "content": "¡Hola! Soy **JARVIS Mini**. Sube documentos en el panel lateral y pregúntame lo que necesites saber. Analizaré los datos estrictamente en mi base vectorial."}
    ]
    current_question: str = ""
    is_processing: bool = False
    stats: str = ""
    mode: str = "rag"
    model: str = "qwen-3.5-0.8b"

    def set_current_question(self, value: str):
        self.current_question = value

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Sube el archivo desde Reflex a nuestro backend (FastAPI) de forma transparente."""
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
            # Enviamos el multipart/form-data idéntico a usar curl
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post("http://localhost:8000/api/ingest", files=upload_data)
                
                if response.status_code == 200:
                    data = response.json()
                    chunks = data.get('indexed_chunks', 0)
                    self.stats = f"✅ Documento Inyectado con éxito en Base Vectorial FAISS ({chunks} divisiones)."
                else:
                    self.stats = f"❌ Fallo al indexar: {response.text}"
        except Exception as e:
            self.stats = f"⚠️ Error subiendo el archivo: {str(e)}"
            
        self.is_processing = False
        yield

    async def answer_query(self):
        """Dispara la llamada asíncrona a Qwen al darle Enter al chat."""
        if not self.current_question.strip():
            return
            
        user_text = self.current_question
        self.chat_history.append({"role": "user", "content": user_text})
        self.current_question = ""
        self.is_processing = True
        yield
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                # El context timeout lo subimos a 180s para que Qwen tenga tiempo en modo CPU puro
                response = await client.post(
                    "http://localhost:8000/api/query", 
                    json={"query": user_text, "mode": self.mode, "model": self.model}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ans = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    if sources:
                        ans += f"\n\n*Recuperado del contexto local: {', '.join(sources)}*"
                    
                    self.chat_history.append({"role": "assistant", "content": ans})
                else:
                    self.chat_history.append({"role": "assistant", "content": "⚠️ Error del backend: " + response.text})
        except Exception as e:
            self.chat_history.append({"role": "assistant", "content": f"⚠️ Fallo de red con Backend: {str(e)}"})
            
        self.is_processing = False
        yield


def message_box(message: dict[str, str]) -> rx.Component:
    """Renderiza individualmente cada burbuja de charla (User o JARVIS)."""
    is_user = message["role"] == "user"
    return rx.flex(
        rx.box(
            rx.markdown(message["content"]),
            bg=rx.cond(is_user, rx.color("blue", 5), rx.color("gray", 3)),
            color=rx.cond(is_user, "white", "inherit"),
            border_radius="xl",
            padding="4",
            max_width="85%",
            box_shadow="0 10px 15px -3px rgb(0 0 0 / 0.1)",
        ),
        width="100%",
        justify=rx.cond(is_user, "end", "start"),
        margin_bottom="3"
    )

def chat_interface() -> rx.Component:
    """Contenedor masivo de los paneles de conversación."""
    return rx.vstack(
        # Lista de mensajes
        rx.box(
            rx.foreach(State.chat_history, message_box),
            width="100%",
            flex="1",
            overflow_y="auto",
            padding="6",
            # Scroll behavior smooth (Reflex no expone esto nativamente siempre, pero flex funciona ideal)
        ),
        # Zona de Input Inferior
        rx.hstack(
            rx.input(
                placeholder="Haz a JARVIS cualquier pregunta de tu temario local...",
                value=State.current_question,
                on_change=State.set_current_question,
                on_key_down=rx.cond(
                    State.current_question.length() > 0,
                    rx.call_script("if(event.key === 'Enter' && !event.shiftKey) { document.getElementById('super_send_btn').click(); }"),
                    rx.call_script("")
                ),
                width="100%",
                size="3",
                radius="large"
            ),
            rx.button(
                rx.icon("send"),
                id="super_send_btn",
                on_click=State.answer_query,
                loading=State.is_processing,
                size="3",
                radius="large",
                cursor="pointer",
            ),
            width="100%",
            padding="4",
            bg=rx.color("gray", 2),
            border_top=f"1px solid {rx.color('gray', 4)}",
        ),
        width="100%",
        height="100vh",
        justify="between",
        position="relative"
    )

def sidebar() -> rx.Component:
    """La Sidebar Lateral donde se anidan comandos de administración."""
    return rx.vstack(
        rx.hstack(
            rx.icon("bot", size=32, color=rx.color("blue", 11)),
            rx.heading("JARVIS Mini", size="6", weight="bold", color=rx.color("blue", 11)),
            width="100%",
            align_items="center"
        ),
        rx.text("RAG Architecture Dashboard", size="2", color=rx.color("gray", 11), margin_bottom="4"),
        
        rx.divider(),
        
        rx.heading("Ingesta Documental", size="4", margin_top="4", margin_bottom="2"),
        rx.text("Alimenta la red neuronal añadiendo PDFs o TXTs. Se segmentarán automáticamente in FAISS.", size="2", color=rx.color("gray", 11)),
        
        # Super Dropzone Component (Upload)
        rx.box(
            rx.upload(
                rx.vstack(
                    rx.icon("upload", size=24, color=rx.color("blue", 11)),
                    rx.text("Arrastra tus archivos aquí", size="2", weight="bold"),
                    rx.text("o pulsa para navegar", size="1"),
                    align_items="center",
                    justify="center",
                    height="100%",
                ),
                id="upload_dropzone",
                multiple=True,
                accept={"text/plain": [".txt"], "text/markdown": [".md", ".markdown"], "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"]},
                max_files=10,
                border=f"2px dashed {rx.color('gray', 7)}",
                border_radius="xl",
                padding="4",
                height="150px",
                width="100%",
                on_drop=State.handle_upload(rx.upload_files(upload_id="upload_dropzone")),
                bg=rx.color("gray", 3),
            ),
            width="100%",
            margin_top="2"
        ),
        
        # Spinner visual para subidas / info estatus
        rx.cond(
            State.stats != "",
            rx.box(
                rx.text(State.stats, size="2", color=rx.color("green", 11), weight="medium"),
                bg=rx.color("green", 3),
                padding="3",
                border_radius="md",
                margin_top="3",
                width="100%"
            ),
            rx.box()
        ),
        
        rx.divider(margin_top="6", margin_bottom="4"),
        
        rx.heading("Ajustes del Modelo LLM", size="4"),
        rx.text("Modelo Base: Qwen 3.5 0.8B", size="2", color=rx.color("gray", 11)),
        rx.text("Modo Lógico: Solo-RAG", size="2", color=rx.color("gray", 11)),
        
        rx.spacer(),
        rx.text("TFG Project", size="1", color=rx.color("gray", 9), align="center", width="100%"),
        
        width=["100%", "100%", "30%"],
        min_width="320px",
        max_width="400px",
        height="100vh",
        padding="6",
        bg=rx.color("gray", 2),
        border_right=f"1px solid {rx.color('gray', 4)}",
        align_items="start"
    )

def index() -> rx.Component:
    """Ensamblado Arquitectónico."""
    return rx.hstack(
        sidebar(),
        chat_interface(),
        width="100vw",
        height="100vh",
        spacing="0"
    )

app = rx.App(
    theme=rx.theme(
        appearance="dark", 
        has_background=True, 
        radius="large", 
        accent_color="blue",
        gray_color="slate"
    )
)
app.add_page(index, title="JARVIS RAG - Chat")
