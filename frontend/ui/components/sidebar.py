"""Componente de la barra lateral (sidebar)."""
import reflex as rx
from ..state import State


def _document_item(doc: dict) -> rx.Component:
    """Fila individual de documento: icono + nombre truncado + badge chunks + botón eliminar."""
    return rx.hstack(
        rx.icon("file-text", size=14, color=rx.color("blue", 9), flex_shrink="0"),
        rx.tooltip(
            rx.text(
                doc["display_name"],
                size="1",
                weight="medium",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
                flex="1",
                min_width="0",
            ),
            content=doc["source"],
        ),
        rx.badge(doc["chunks"], color_scheme="blue", variant="soft", size="1", flex_shrink="0"),
        rx.icon_button(
            rx.icon("trash-2", size=12),
            size="1",
            variant="ghost",
            color_scheme="red",
            cursor="pointer",
            on_click=State.delete_document(doc["source"]),
            flex_shrink="0",
        ),
        align_items="center",
        spacing="2",
        width="100%",
        padding_x="4px",
        padding_y="3px",
        border_radius="6px",
        _hover={"bg": rx.color("gray", 4)},
    )


def _documents_section() -> rx.Component:
    """Sección acordeón de documentos indexados."""
    return rx.accordion.root(
        rx.accordion.item(
            rx.accordion.header(
                rx.accordion.trigger(
                    rx.hstack(
                        rx.text("Documentos Indexados", size="3", weight="bold"),
                        rx.icon(
                            "chevron-down",
                            style={
                                "transform": rx.cond(
                                    State.accordion_value == "documents", 
                                    "rotate(180deg)", 
                                    "rotate(0deg)"
                                ),
                                "transition": "transform 250ms ease",
                            },
                        ),
                        justify="between",
                        width="100%",
                    ),
                    padding="8px",
                    border_radius="8px",
                    _hover={"bg": rx.color("gray", 4)},
                    cursor="pointer",
                    width="100%",
                ),
            ),
            rx.accordion.content(
                rx.box(
                    rx.cond(
                        State.documents.length() > 0,
                        rx.vstack(
                            rx.foreach(State.documents, _document_item),
                            spacing="1",
                            width="100%",
                        ),
                        rx.text(
                            "No hay documentos indexados",
                            size="1",
                            color=rx.color("gray", 9),
                            font_style="italic",
                            padding="8px",
                        ),
                    ),
                    max_height="30vh",
                    overflow_y="auto",
                    width="100%",
                    padding_top="4px",
                ),
            ),
            value="documents",
        ),
        value=State.accordion_value,
        on_value_change=State.toggle_accordion,
        type="single",
        collapsible=True,
        width="100%",
        variant="ghost",
    )


def _watch_folder_row(path: str) -> rx.Component:
    """Fila individual con 3 opciones: Pausar, Desindexar, Eliminar."""
    return rx.hstack(
        rx.icon("folder-open", size=14, color=rx.color("green", 9), flex_shrink="0"),
        rx.tooltip(
            rx.text(
                path,
                size="1",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
                flex="1",
                min_width="0",
            ),
            content=path,
        ),
        # 1. Destrackear (Pausar)
        rx.tooltip(
            rx.icon_button(
                rx.icon("pause", size=11),
                size="1",
                variant="ghost",
                color_scheme="gray",
                cursor="pointer",
                on_click=State.untrack_watcher(path),
            ),
            content="Pausar vigilancia (mantener docs)",
        ),
        # 2. Desindexar
        rx.tooltip(
            rx.icon_button(
                rx.icon("file-minus", size=11),
                size="1",
                variant="ghost",
                color_scheme="yellow",
                cursor="pointer",
                on_click=State.unindex_watcher(path),
            ),
            content="Desindexar (borrar chunks)",
        ),
        # 3. Eliminar
        rx.tooltip(
            rx.icon_button(
                rx.icon("trash-2", size=11),
                size="1",
                variant="ghost",
                color_scheme="red",
                cursor="pointer",
                on_click=State.remove_watcher(path),
            ),
            content="Eliminar completamente",
        ),
        align_items="center",
        spacing="1",
        width="100%",
        padding_x="4px",
        padding_y="3px",
        border_radius="6px",
        _hover={"bg": rx.color("gray", 4)},
    )


def _watch_folder_section() -> rx.Component:
    """Sección de watch folders colapsable."""
    return rx.vstack(
        rx.hstack(
            rx.icon("folder-sync", size=14, color=rx.color("gray", 10)),
            rx.text("Watch Folder", size="3", weight="bold"),
            rx.cond(
                State.watch_running,
                rx.badge("● Activo", color_scheme="green", variant="soft", size="1"),
                rx.badge("● Inactivo", color_scheme="gray", variant="soft", size="1"),
            ),
            align_items="center",
            spacing="2",
            width="100%",
        ),
        # Lista de carpetas vigiladas activas
        rx.cond(
            State.watch_folders.length() > 0,
            rx.vstack(
                rx.foreach(State.watch_folders, _watch_folder_row),
                spacing="1",
                width="100%",
            ),
            rx.text(
                "Ninguna carpeta vigilada",
                size="1",
                color=rx.color("gray", 9),
                font_style="italic",
            ),
        ),
        # Input + botón para añadir nueva ruta
        rx.hstack(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("folder-search", size=14),
                    on_click=State.select_folder_dialog,
                    size="1",
                    color_scheme="gray",
                    cursor="pointer",
                ),
                content="Seleccionar carpeta",
            ),
            rx.input(
                placeholder="Ruta...",
                value=State.new_watch_path,
                on_change=State.set_new_watch_path,
                size="1",
                flex="1",
            ),
            rx.icon_button(
                rx.icon("plus", size=14),
                on_click=State.start_watcher,
                size="1",
                color_scheme="blue",
                cursor="pointer",
                type="button",
            ),
            spacing="2",
            width="100%",
        ),
        spacing="2",
        width="100%",
        padding_x="2px",
    )


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

        rx.separator(size="4", margin_y="4"),

        # Documentos indexados (acordeón colapsable)
        _documents_section(),

        rx.separator(size="4", margin_y="4"),

        # Watch Folder
        _watch_folder_section(),

        rx.separator(size="4", margin_y="4"),

        rx.heading("Modelo Activo", size="3", padding_x="1"),
        rx.hstack(
            rx.badge("Qwen 3.5 · 0.8B", color_scheme="blue", variant="soft"),
            rx.badge("RAG", color_scheme="green", variant="soft"),
            spacing="2",
            padding_x="1",
        ),

        rx.spacer(),
        rx.text("TFM · Local RAG Project", size="1", color=rx.color("gray", 8),
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
        on_mount=[State.load_documents, State.load_watch_status, State.update_loop],
    )
