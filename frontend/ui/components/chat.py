"""Componente de la interfaz de chat (mensajes + input)."""
import reflex as rx
from ..state import State, SCROLL_BOTTOM_JS
from .message_box import message_box


def chat_interface() -> rx.Component:
    """Panel de chat: zona de mensajes con scroll + input fijo abajo."""
    return rx.flex(
        # ── Zona de mensajes: únicamente ESTA caja hace scroll ────────
        rx.vstack(
            rx.foreach(State.chat_history, message_box),
            padding_bottom="50vh",
            padding_top="20px",
            width="100%",
            id="chat-container",
            flex="1",
            overflow_y="auto",
            align_items="center",
        ),
        # ── Input fijo en la parte inferior, FUERA del área de scroll ─
        rx.box(
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Pregunta algo sobre tus documentos...",
                        value=State.current_question,
                        on_change=State.set_current_question,
                        width="100%",
                        size="3",
                        radius="full",
                        disabled=State.is_processing,
                    ),
                    rx.button(
                        rx.cond(
                            State.is_processing,
                            rx.spinner(size="3"),
                            rx.icon("send", size=18),
                        ),
                        type="submit",
                        size="3",
                        radius="full",
                        cursor="pointer",
                        disabled=State.is_processing,
                    ),
                    align_items="center",
                    spacing="3",
                    width="80%",
                    margin_x="auto",
                ),
                on_submit=[rx.call_script(SCROLL_BOTTOM_JS), State.handle_submit_query],
                reset_on_submit=False,
                width="100%",
            ),
            padding_x="20px",
            padding_y="16px",
            border_top=f"1px solid {rx.color('gray', 4)}",
            bg=rx.color("gray", 2),
            width="100%",
            flex_shrink="0",
        ),
        direction="column",
        flex="1",
        height="100vh",
        overflow="hidden",
    )
