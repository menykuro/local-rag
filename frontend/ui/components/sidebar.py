"""Componente de la barra lateral (sidebar)."""
import reflex as rx
from ..state import State


def _document_item(doc: dict) -> rx.Component:
    """Fila individual de documento."""
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
            on_click=State.open_delete_document_modal(doc["source"]),
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


def _watch_folder_row(folder: dict) -> rx.Component:
    """Fila individual de watch folder con acciones."""
    return rx.hstack(
        rx.icon("folder-open", size=14, color=rx.color("green", 9), flex_shrink="0"),
        rx.tooltip(
            rx.text(
                folder["path"],
                size="1",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
                flex="1",
                min_width="0",
            ),
            content=folder["path"],
        ),
        rx.cond(
            folder["active"],
            rx.badge("Activa", color_scheme="green", variant="soft", size="1", flex_shrink="0"),
            rx.badge("Pausada", color_scheme="gray", variant="soft", size="1", flex_shrink="0"),
        ),
        rx.tooltip(
            rx.cond(
                folder["active"],
                rx.icon_button(
                    rx.icon("pause", size=11),
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                    cursor="pointer",
                    on_click=State.pause_watcher(folder["path"]),
                ),
                rx.icon_button(
                    rx.icon("play", size=11),
                    size="1",
                    variant="ghost",
                    color_scheme="green",
                    cursor="pointer",
                    on_click=State.resume_watcher(folder["path"]),
                ),
            ),
            content=rx.cond(folder["active"], "Pausar vigilancia", "Reanudar vigilancia"),
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon("file-minus", size=11),
                size="1",
                variant="ghost",
                color_scheme="yellow",
                cursor="pointer",
                on_click=State.unindex_watcher(folder["path"]),
            ),
            content="Desindexar carpeta",
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon("trash-2", size=11),
                size="1",
                variant="ghost",
                color_scheme="red",
                cursor="pointer",
                on_click=State.open_remove_watch_modal(folder["path"]),
            ),
            content="Eliminar carpeta",
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
    """Seccion colapsable de watch folders sin animacion de height."""
    has_watch_folders = State.watch_folders.length() > 0
    is_open = State.watch_accordion_value == "watch"

    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.icon("folder-sync", size=14, color=rx.color("gray", 10)),
                rx.text("Watch Folder", size="3", weight="bold", color="white"),
                spacing="2",
                align_items="center",
            ),
            rx.hstack(
                rx.cond(
                    has_watch_folders,
                    rx.cond(
                        State.watch_running,
                        rx.badge(
                            "● Activo",
                            color_scheme="green",
                            variant="soft",
                            size="1",
                            cursor="pointer",
                            on_click=State.toggle_all_watchers,
                        ),
                        rx.badge(
                            "● Inactivo",
                            color_scheme="gray",
                            variant="soft",
                            size="1",
                            cursor="pointer",
                            on_click=State.toggle_all_watchers,
                        ),
                    ),
                    rx.cond(
                        State.watch_running,
                        rx.badge("● Activo", color_scheme="green", variant="soft", size="1", cursor="default"),
                        rx.badge("● Inactivo", color_scheme="gray", variant="soft", size="1", cursor="default"),
                    ),
                ),
                rx.icon(
                    "chevron-down",
                    style={
                        "transform": rx.cond(is_open, "rotate(180deg)", "rotate(0deg)"),
                        "transition": "transform 250ms ease",
                    },
                ),
                spacing="2",
                align_items="center",
            ),
            justify="between",
            width="100%",
            padding="8px",
            border_radius="8px",
            _hover={"bg": rx.color("gray", 4)},
            cursor="pointer",
            on_click=State.toggle_watch_section,
        ),
        rx.box(
            rx.vstack(
                rx.box(
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
                            padding="8px",
                        ),
                    ),
                    width="100%",
                    padding_top="4px",
                    overflow_y="auto",
                    flex="1",
                    min_height="0",
                ),
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
                height="100%",
                min_height="0",
            ),
            display=rx.cond(is_open, "block", "none"),
            width="100%",
            overflow="hidden",
            flex="1",
            min_height="0",
        ),
        width="100%",
        height="fit-content",
        max_height="30%",
        overflow="hidden",
        min_height="0",
    )


def _documents_section() -> rx.Component:
    """Seccion colapsable de documentos indexados sin animacion de height."""
    is_open = State.documents_accordion_value == "documents"
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.icon("file-text", size=14, color=rx.color("gray", 10)),
                rx.text("Documentos Indexados", size="3", weight="bold", color="white"),
                spacing="2",
                align_items="center",
            ),
            rx.icon(
                "chevron-down",
                style={
                    "transform": rx.cond(is_open, "rotate(180deg)", "rotate(0deg)"),
                    "transition": "transform 250ms ease",
                },
            ),
            justify="between",
            width="100%",
            padding="8px",
            border_radius="8px",
            _hover={"bg": rx.color("gray", 4)},
            cursor="pointer",
            on_click=State.toggle_documents_section,
        ),
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
            overflow_y="auto",
            width="100%",
            padding_top="4px",
            display=rx.cond(is_open, "block", "none"),
            flex="1",
            min_height="0",
        ),
        width="100%",
        height="fit-content",
        max_height="30%",
        overflow="hidden",
        min_height="0",
    )


def _delete_document_modal() -> rx.Component:
    """Modal de confirmacion para eliminar documento indexado."""
    return rx.cond(
        State.delete_document_modal_open,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.text("Eliminar documento", size="4", weight="bold", color="white"),
                    rx.text(
                        "Esta accion eliminara el documento del indice y no se puede deshacer.",
                        size="2",
                        color=rx.color("gray", 10),
                    ),
                    rx.text(
                        State.pending_document_source,
                        size="1",
                        color=rx.color("gray", 9),
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancelar",
                            variant="soft",
                            color_scheme="gray",
                            on_click=State.close_delete_document_modal,
                            cursor="pointer",
                        ),
                        rx.button(
                            "Eliminar",
                            color_scheme="red",
                            on_click=State.confirm_delete_document,
                            cursor="pointer",
                        ),
                        justify="end",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                    align_items="start",
                ),
                width="420px",
                max_width="92vw",
                bg=rx.color("gray", 2),
                border=f"1px solid {rx.color('gray', 6)}",
                border_radius="12px",
                padding="16px",
                box_shadow="0 18px 48px rgba(0,0,0,0.45)",
            ),
            position="fixed",
            inset="0",
            bg="rgba(0, 0, 0, 0.55)",
            display="flex",
            align_items="center",
            justify_content="center",
            z_index="9999",
        ),
        rx.fragment(),
    )


def _remove_watch_modal() -> rx.Component:
    """Modal de confirmacion para eliminar watch folder."""
    return rx.cond(
        State.remove_watch_modal_open,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.text("Eliminar Watch Folder", size="4", weight="bold", color="white"),
                    rx.text(
                        "Se pausara la observacion, se desindexaran sus documentos y se eliminara la ruta guardada.",
                        size="2",
                        color=rx.color("gray", 10),
                    ),
                    rx.text(
                        State.pending_watch_path,
                        size="1",
                        color=rx.color("gray", 9),
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancelar",
                            variant="soft",
                            color_scheme="gray",
                            on_click=State.close_remove_watch_modal,
                            cursor="pointer",
                        ),
                        rx.button(
                            "Eliminar",
                            color_scheme="red",
                            on_click=State.confirm_remove_watch,
                            cursor="pointer",
                        ),
                        justify="end",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                    align_items="start",
                ),
                width="420px",
                max_width="92vw",
                bg=rx.color("gray", 2),
                border=f"1px solid {rx.color('gray', 6)}",
                border_radius="12px",
                padding="16px",
                box_shadow="0 18px 48px rgba(0,0,0,0.45)",
            ),
            position="fixed",
            inset="0",
            bg="rgba(0, 0, 0, 0.55)",
            display="flex",
            align_items="center",
            justify_content="center",
            z_index="9999",
        ),
        rx.fragment(),
    )


def sidebar() -> rx.Component:
    """Sidebar de administracion: ingesta de documentos y ajustes del modelo."""
    return rx.fragment(
        rx.vstack(
            rx.hstack(
                rx.icon("bot", size=26, color=rx.color("blue", 10)),
                rx.heading("JARVIS Mini", size="5", weight="bold", color=rx.color("blue", 10)),
                align_items="center",
                spacing="2",
                padding_x="1",
            ),
            rx.text("RAG · Local Knowledge Base", size="1", color=rx.color("gray", 10), padding_x="1"),

            rx.separator(size="4", margin_y="4"),

            rx.hstack(
                rx.icon("upload", size=14, color=rx.color("gray", 10)),
                rx.text("Ingesta Documental", size="3", weight="bold", color="white"),
                spacing="2",
                align_items="center",
                padding_x="1",
            ),
            rx.text(
                "Sube PDFs, Word o TXT para indexarlos en FAISS.",
                size="2",
                color=rx.color("gray", 10),
                padding_x="1",
            ),
            rx.upload(
                rx.vstack(
                    rx.icon("upload", size=20, color=rx.color("blue", 10)),
                    rx.text("Arrastra archivos aqui", size="2", weight="medium"),
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

            _watch_folder_section(),

            rx.separator(size="4", margin_y="4"),

            _documents_section(),

            rx.separator(size="4", margin_y="4"),

            rx.heading("Modelo Activo", size="3", padding_x="1"),
            rx.hstack(
                rx.badge("Qwen 3.5 · 0.8B", color_scheme="blue", variant="soft"),
                rx.badge("RAG", color_scheme="green", variant="soft"),
                spacing="2",
                padding_x="1",
            ),

            rx.spacer(),
            rx.text("TFM · Local RAG Project", size="1", color=rx.color("gray", 8), align="center", width="100%"),

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
            overflow="hidden",
            on_mount=[State.load_documents, State.load_watch_status, State.update_loop],
            position="relative",
        ),
        _delete_document_modal(),
        _remove_watch_modal(),
    )
