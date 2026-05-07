import flet as ft

# ── Dark Palette ──────────────────────────────────────────────────────────────
BG          = "#0f1117"
SIDEBAR_BG  = "#1a1a2e"
PRIMARY     = "#4a90d9"
SUCCESS     = "#2ecc71"
WARNING     = "#f39c12"
DANGER      = "#e74c3c"
PURPLE      = "#9b59b6"
DARK_CARD   = "#16213e"
CARD_BG     = "#1e2130"
CARD_SEL    = "#1e3a5f"
HEADER_BG   = "#252a3a"
BORDER_COL  = "#2e3347"
TEXT_DARK   = "#e8eaf6"
TEXT_LIGHT  = "#ffffff"
TEXT_MUTED  = "#8892b0"
TEXT_GREY   = "#a8b2d8"
PANEL_BLUE  = "#1a2744"

VEHICLE_TYPES    = ["Sedan", "SUV", "Pickup", "Van", "Convertible", "Hatchback"]
VEHICLE_STATUSES = ["available", "reserved", "rented", "maintenance"]

STATUS_COLORS = {
    "available":   SUCCESS,
    "rented":      WARNING,
    "reserved":    PURPLE,
    "maintenance": DANGER,
    "active":      SUCCESS,
    "late":        DANGER,
    "completed":   "#546e7a",
    "pending":     PURPLE,
    "converted":   PRIMARY,
    "cancelled":   DANGER,
}

RES_LABELS = {
    "pending":   "Pendiente",
    "converted": "Convertida",
    "completed": "Completada",
    "cancelled": "Cancelada",
    "Todos":     "Todos",
}

RENT_LABELS = {
    "active":    "Activo",
    "completed": "Completado",
    "late":      "Vencido",
    "Todos":     "Todos",
}


# ── Field factory ─────────────────────────────────────────────────────────────
def mk_field(label, value="", kb=None, width=None) -> ft.TextField:
    f = ft.TextField(
        label=label,
        value=str(value) if value else "",
        bgcolor=HEADER_BG,
        color=TEXT_DARK,
        label_style=ft.TextStyle(color=TEXT_MUTED),
        border_color=BORDER_COL,
        focused_border_color=PRIMARY,
        cursor_color=TEXT_DARK,
        keyboard_type=kb or ft.KeyboardType.TEXT,
        text_size=13,
    )
    if width:
        f.width = width
    return f


def mk_dropdown(label, options, value=None, width=None) -> ft.Dropdown:
    d = ft.Dropdown(
        label=label,
        options=options,
        value=value,
        bgcolor=HEADER_BG,
        color=TEXT_DARK,
        text_size=13,
    )
    if width:
        d.width = width
    return d


# ── UI helpers ────────────────────────────────────────────────────────────────

def stat_card(label: str, value, color: str) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(str(value), size=26, weight="bold", color=TEXT_LIGHT),
                ft.Text(label, size=11, color="#ddddee"),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=color,
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
        expand=True,
    )


def primary_btn(text: str, on_click, color=PRIMARY, icon=None) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text=text, icon=icon, on_click=on_click,
        bgcolor=color, color=TEXT_LIGHT,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )


def danger_btn(text: str, on_click) -> ft.ElevatedButton:
    return primary_btn(text, on_click, color=DANGER)


def section_title(text: str) -> ft.Text:
    return ft.Text(text, size=22, weight="bold", color=TEXT_DARK)


def status_chip(status: str, label: str = None, width: int = None) -> ft.Container:
    color = STATUS_COLORS.get(status, "#546e7a")
    return ft.Container(
        content=ft.Text(label or status.capitalize(), size=11, color=TEXT_LIGHT, weight="bold"),
        bgcolor=color, border_radius=20,
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
        width=width,
    )


def tbl_header(cols, widths) -> ft.Container:
    return ft.Container(
        content=ft.Row([
            ft.Text(c, width=w, weight="bold", size=12, color=TEXT_LIGHT)
            for c, w in zip(cols, widths)
        ]),
        bgcolor=HEADER_BG,
        border_radius=ft.border_radius.only(top_left=8, top_right=8),
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        border=ft.border.only(bottom=ft.BorderSide(2, PRIMARY)),
    )


def info_banner(text: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(text, size=12, color="#90caf9", italic=True),
        bgcolor=PANEL_BLUE, border_radius=8, padding=10,
        border=ft.border.all(1, PRIMARY),
    )


def snack(page: ft.Page, message: str, error=False):
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color=TEXT_LIGHT),
        bgcolor=DANGER if error else SUCCESS,
    )
    page.snack_bar.open = True
    page.update()


# ── Dialog helpers ────────────────────────────────────────────────────────────

def open_dialog(page: ft.Page, dlg: ft.AlertDialog):
    page.overlay.append(dlg)
    dlg.open = True
    page.update()


def close_dialog(page: ft.Page, dlg: ft.AlertDialog):
    dlg.open = False
    try:
        page.overlay.remove(dlg)
    except Exception:
        pass
    page.update()


def confirm_dialog(page: ft.Page, message: str, on_confirm):
    def yes(e):
        close_dialog(page, dlg)
        on_confirm()

    def no(e):
        close_dialog(page, dlg)

    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=CARD_BG,
        title=ft.Text("¿Confirmar?", color=TEXT_DARK),
        content=ft.Text(message, color=TEXT_GREY, size=14),
        actions=[
            ft.ElevatedButton("Sí",   on_click=yes, bgcolor=DANGER,   color=TEXT_LIGHT),
            ft.ElevatedButton("No",   on_click=no,  bgcolor=HEADER_BG, color=TEXT_MUTED),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    open_dialog(page, dlg)
