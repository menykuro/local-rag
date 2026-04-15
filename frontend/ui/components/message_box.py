"""Componente de burbuja de mensaje individual."""
import reflex as rx
from ..state import State


def message_box(message: dict[str, str]) -> rx.Component:
    """Renderiza una burbuja de chat (usuario o asistente)."""
    is_user = message["role"] == "user"
    is_empty = message["content"] == ""
    return rx.flex(
        rx.box(
            rx.cond(
                is_empty,
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text("Buscando...", size="2",
                            color=rx.color("gray", 10), font_style="italic"),
                    align_items="center",
                    spacing="2",
                ),
                rx.markdown(message["content"]),
            ),
            bg=rx.cond(is_user, rx.color("blue", 9), rx.color("gray", 3)),
            color=rx.cond(is_user, "white", rx.color("gray", 12)),
            border_radius=rx.cond(
                is_user,
                "16px 4px 16px 16px",
                "4px 16px 16px 16px",
            ),
            padding_x="16px",
            max_width="80%",
            box_shadow=rx.cond(
                is_user,
                "0 2px 12px rgba(59,130,246,0.25)",
                "0 2px 8px rgba(0,0,0,0.15)",
            ),
        ),
        width="90%",
        justify=rx.cond(is_user, "end", "start"),
        padding_x="20px",
    )
