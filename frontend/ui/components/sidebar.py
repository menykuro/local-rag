"""Componente de la barra lateral (sidebar)."""
import reflex as rx
from ..state import State


def sidebar() -> rx.Component:
    """Sidebar de administración: ingesta de documentos y ajustes del modelo."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.icon("bot", size=26, color=rx.color("blue", 10)),
            rx.heading("JARVIS Mini", size="5", weight="bold", color=rx.color("blue", 10)),
            align_items="center",
            spacing="2",
            padding_x="1",
        ),
        rx.text("RAG · Local Knowledge Base", size="1",
                color=rx.color("gray", 10), padding_x="1"),

        rx.separator(size="4", margin_y="4"),

        # Ingesta documental
        rx.heading("Ingesta Documental", size="3", padding_x="1"),
        rx.text(
            "Sube PDFs, Word o TXT para indexarlos en FAISS.",
            size="2", color=rx.color("gray", 10), padding_x="1",
        ),
        rx.upload(
            rx.vstack(
                rx.icon("upload", size=20, color=rx.color("blue", 10)),
                rx.text("Arrastra archivos aquí", size="2", weight="medium"),
                rx.text("o pulsa para navegar", size="1", color=rx.color("gray", 10)),
                align_items="center",
                justify="center",
                height="100%",
                spacing="1",
            ),
            id="upload_dropzone",
            multiple=True,
            accept={
                "text/plain": [".txt"],
                "text/markdown": [".md", ".markdown"],
                "application/pdf": [".pdf"],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
            },
            max_files=10,
            border=f"2px dashed {rx.color('blue', 6)}",
            border_radius="12px",
            height="120px",
            padding="4px",
            width="100%",
            on_drop=State.handle_upload(rx.upload_files(upload_id="upload_dropzone")),
            bg=rx.color("gray", 3),
        ),
        rx.cond(
            State.stats != "",
            rx.callout(State.stats, size="1", width="100%", margin_top="2"),
            rx.box(),
        ),

        rx.separator(size="4", margin_y="4"),

        # Modelo activo
        rx.heading("Modelo Activo", size="3", padding_x="1"),
        rx.hstack(
            rx.badge("Qwen 3.5 · 0.8B", color_scheme="blue", variant="soft"),
            rx.badge("RAG", color_scheme="green", variant="soft"),
            spacing="2",
            padding_x="1",
        ),

        rx.spacer(),
        rx.text("TFG · Local RAG Project", size="1", color=rx.color("gray", 8),
                align="center", width="100%"),

        width="15%",
        min_width="280px",
        height="100vh",
        padding="16px",
        bg=rx.color("gray", 2),
        border_right=f"1px solid {rx.color('gray', 4)}",
        align_items="start",
        spacing="0",
        flex_shrink="0",
        gap="5px",
    )
