"""
Custom modal implementation for Flet 0.27.
AlertDialog bgcolor is broken in 0.27 — this uses a Stack overlay instead.
"""
import flet as ft
from utils.theme import CARD_BG, BORDER_COL, TEXT_DARK, TEXT_MUTED, PRIMARY, HEADER_BG


def show_modal(page: ft.Page, title: str, content: ft.Control,
               actions: list, width: int = 500, height: int = None):
    """
    Display a modal dialog using Stack overlay.
    Returns the modal container so caller can close it.
    """
    modal_ref = {"container": None}

    def close():
        if modal_ref["container"] and modal_ref["container"] in page.overlay:
            page.overlay.remove(modal_ref["container"])
            page.update()

    # Build action row
    action_row = ft.Row(
        [a for a in actions],
        alignment=ft.MainAxisAlignment.END,
        spacing=8,
    )

    inner = ft.Container(
        bgcolor=CARD_BG,
        border_radius=12,
        border=ft.border.all(1, BORDER_COL),
        padding=24,
        width=width,
        content=ft.Column([
            # Title bar
            ft.Row([
                ft.Text(title, size=17, weight="bold", color=TEXT_DARK),
                ft.IconButton(
                    icon=ft.icons.CLOSE,
                    icon_color=TEXT_MUTED,
                    icon_size=18,
                    on_click=lambda e: close(),
                    tooltip="Cerrar",
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=1, color=BORDER_COL),
            # Scrollable content area
            ft.Container(
                content=content,
                height=height,
            ) if height else content,
            ft.Divider(height=1, color=BORDER_COL),
            action_row,
        ], spacing=14, tight=True),
    )

    # Dark semi-transparent backdrop + centered card
    backdrop = ft.Container(
        expand=True,
        bgcolor="#80000000",   # semi-transparent black
        alignment=ft.alignment.center,
        content=inner,
    )

    modal_ref["container"] = backdrop
    page.overlay.append(backdrop)
    page.update()
    return close   # caller can call close() to dismiss


