"""Punto de entrada de la aplicación Reflex - JARVIS Mini RAG."""
import reflex as rx
from .state import State  # noqa: F401 — Reflex necesita que State esté importado
from .components import chat_interface, sidebar


def index() -> rx.Component:
    """Página principal: sidebar + chat."""
    return rx.hstack(
        sidebar(),
        chat_interface(),
        width="100vw",
        height="100vh",
        spacing="0",
        overflow="hidden",
        align_items="stretch",
    )


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        radius="medium",
        accent_color="blue",
        gray_color="slate",
    )
)
app.add_page(index, title="JARVIS RAG - Chat")
