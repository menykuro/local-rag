"""Componente de la barra lateral (sidebar)."""

import reflex as rx

from ..state import State


def _document_item(doc: dict) -> rx.Component:
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
    is_open = State.active_sidebar_section == "watch"
    has_watch_folders = State.watch_folders.length() > 0
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
                        rx.badge("Activo", color_scheme="green", variant="soft", size="1", on_click=State.toggle_all_watchers),
                        rx.badge("Inactivo", color_scheme="gray", variant="soft", size="1", on_click=State.toggle_all_watchers),
                    ),
                    rx.cond(
                        State.watch_running,
                        rx.badge("Activo", color_scheme="green", variant="soft", size="1"),
                        rx.badge("Inactivo", color_scheme="gray", variant="soft", size="1"),
                    ),
                ),
                rx.icon("chevron-down", style={"transform": rx.cond(is_open, "rotate(180deg)", "rotate(0deg)")}),
                spacing="2",
                align_items="center",
            ),
            justify="between",
            width="100%",
            padding="8px",
            border_radius="8px",
            overflow="hidden",
            _hover={"bg": rx.color("gray", 4)},
            cursor="pointer",
            on_click=State.toggle_watch_section,
        ),
        rx.box(
            rx.vstack(
                rx.box(
                    rx.cond(
                        has_watch_folders,
                        rx.vstack(rx.foreach(State.watch_folders, _watch_folder_row), spacing="1", width="100%"),
                        rx.text("Ninguna carpeta vigilada", size="1", color=rx.color("gray", 9), font_style="italic", padding="8px"),
                    ),
                    width="100%",
                    overflow_y="auto",
                    flex="1",
                    min_height="0",
                ),
                rx.hstack(
                    rx.tooltip(
                        rx.icon_button(rx.icon("folder-search", size=14), on_click=State.select_folder_dialog, size="1", color_scheme="gray"),
                        content="Seleccionar carpeta",
                    ),
                    rx.input(placeholder="Ruta...", value=State.new_watch_path, on_change=State.set_new_watch_path, size="1", flex="1"),
                    rx.icon_button(rx.icon("plus", size=14), on_click=State.start_watcher, size="1", color_scheme="blue", type="button"),
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
            flex="1",
            min_height="0",
            overflow="hidden",
        ),
        width="100%",
        height=rx.cond(is_open, "100%", "fit-content"),
        min_height="0",
        overflow="hidden",
    )


def _documents_section() -> rx.Component:
    is_open = State.active_sidebar_section == "documents"
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.icon("file-text", size=14, color=rx.color("gray", 10)),
                rx.text("Documentos Indexados", size="3", weight="bold", color="white"),
                spacing="2",
                align_items="center",
            ),
            rx.icon("chevron-down", style={"transform": rx.cond(is_open, "rotate(180deg)", "rotate(0deg)")}),
            justify="between",
            width="100%",
            padding="8px",
            border_radius="8px",
            overflow="hidden",
            _hover={"bg": rx.color("gray", 4)},
            cursor="pointer",
            on_click=State.toggle_documents_section,
        ),
        rx.box(
            rx.cond(
                State.documents.length() > 0,
                rx.vstack(rx.foreach(State.documents, _document_item), spacing="1", width="100%"),
                rx.text("No hay documentos indexados", size="1", color=rx.color("gray", 9), font_style="italic", padding="8px"),
            ),
            overflow_y="auto",
            width="100%",
            display=rx.cond(is_open, "block", "none"),
            flex="1",
            min_height="0",
        ),
        width="100%",
        height=rx.cond(is_open, "100%", "fit-content"),
        min_height="0",
        overflow="hidden",
    )


def _accordion_block() -> rx.Component:
    return rx.vstack(
        _watch_folder_section(),
        rx.separator(size="4", margin_y="4"),
        _documents_section(),
        width="100%",
        height="42%",
        min_height="0",
        overflow="hidden",
        spacing="2",
        padding_x="2px",
        padding_bottom="2px",
    )


def _system_stats_panel() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.badge(f"CPU Proc: {State.system_stats['process_cpu_percent']}%", color_scheme="orange", variant="soft", size="1"),
            rx.badge(f"RAM Proc: {State.system_stats['process_memory_percent']}%", color_scheme="purple", variant="soft", size="1"),
            spacing="2",
            wrap="wrap",
            width="100%",
        ),
        rx.recharts.line_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke=rx.color("gray", 6)),
            rx.recharts.x_axis(data_key="sample", hide=True),
            rx.recharts.y_axis(width=26, domain=[0, 100]),
            rx.recharts.tooltip(),
            rx.recharts.line(data_key="cpu_proc", type_="monotone", stroke=rx.color("orange", 9), stroke_width=2, dot=True, name="CPU Proc %"),
            rx.recharts.line(data_key="ram_proc", type_="monotone", stroke=rx.color("blue", 9), stroke_width=2, dot=False, name="RAM Proc %"),
            rx.recharts.line(
                data_key="cpu_system",
                type_="monotone",
                stroke=rx.color("gray", 8),
                stroke_width=1,
                dot=False,
                stroke_dasharray="4 4",
                name="CPU Sistema %",
            ),
            rx.recharts.line(
                data_key="ram_system",
                type_="monotone",
                stroke=rx.color("gray", 9),
                stroke_width=1,
                dot=False,
                stroke_dasharray="2 4",
                name="RAM Sistema %",
            ),
            data=State.system_chart_data,
            height=120,
            width="100%",
            border=f"1px solid {rx.color('gray', 5)}",
            border_radius="8px",
            bg=rx.color("gray", 3),
        ),
        spacing="2",
        width="100%",
        padding_x="1",
        height="24%",
        min_height="0",
    )


def _delete_document_modal() -> rx.Component:
    return rx.cond(
        State.delete_document_modal_open,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.text("Eliminar documento", size="4", weight="bold", color="white"),
                    rx.text("Esta accion eliminara el documento del indice y no se puede deshacer.", size="2", color=rx.color("gray", 10)),
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
                        rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=State.close_delete_document_modal),
                        rx.button("Eliminar", color_scheme="red", on_click=State.confirm_delete_document),
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
                        rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=State.close_remove_watch_modal),
                        rx.button("Eliminar", color_scheme="red", on_click=State.confirm_remove_watch),
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
    return rx.fragment(
        rx.vstack(
            rx.hstack(
                rx.icon("bot", size=26, color=rx.color("blue", 10)),
                rx.heading("JARVIS Mini", size="5", weight="bold", color=rx.color("blue", 10)),
                align_items="center",
                spacing="2",
                padding_x="1",
            ),
            rx.text("Qwen 3.5 0.8B · RAG", size="1", color=rx.color("gray", 10), padding_x="1"),
            rx.separator(size="4", margin_y="4"),
            rx.vstack(
                rx.hstack(
                    rx.icon("upload", size=14, color=rx.color("gray", 10)),
                    rx.text("Ingesta Documental", size="3", weight="bold", color="white"),
                    spacing="2",
                    align_items="center",
                    padding_x="1",
                ),
                rx.text("Sube PDFs, Word o TXT para indexarlos en FAISS.", size="2", color=rx.color("gray", 10), padding_x="1"),
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
                    height="100%",
                    padding="4px",
                    width="100%",
                    on_drop=State.handle_upload(rx.upload_files(upload_id="upload_dropzone")),
                    bg=rx.color("gray", 3),
                ),
                spacing="2",
                width="100%",
                height="30%",
                min_height="0",
            ),
            rx.separator(size="4", margin_y="4"),
            _accordion_block(),
            rx.separator(size="4", margin_y="4"),
            rx.heading("Estadisticas de Uso", size="3", padding_x="1"),
            _system_stats_panel(),
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
            on_mount=[State.load_documents, State.load_watch_status, State.load_system_stats, State.update_loop],
            position="relative",
        ),
        _delete_document_modal(),
        _remove_watch_modal(),
    )
