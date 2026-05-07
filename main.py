import flet as ft
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import initialize_db
from views.dashboard_view    import dashboard_view
from views.vehicles_view     import vehicles_view
from views.customers_view    import customers_view
from views.reservations_view import reservations_view
from views.rentals_view      import rentals_view
from views.reports_view      import reports_view
from utils.theme import SIDEBAR_BG, DARK_CARD, TEXT_LIGHT, TEXT_MUTED

NAV_ITEMS = [
    ("Dashboard",     "🏠", dashboard_view),
    ("Vehículos",     "🚙", vehicles_view),
    ("Clientes",      "👥", customers_view),
    ("Reservaciones", "📅", reservations_view),
    ("Rentas",        "🔑", rentals_view),
    ("Reportes",      "📊", reports_view),
]


def main(page: ft.Page):
    page.title          = "Car Rental Management System"
    page.bgcolor        = "#0f1117"
    page.padding        = 0
    page.window_width   = 1200
    page.window_height  = 720
    page.window_min_width  = 960
    page.window_min_height = 600

    initialize_db()

    content_area = ft.Container(expand=True, bgcolor="#f0f2f5")

    nav_refs = {}  # name -> (container, text_widget)

    def show_view(name: str, builder):
        content_area.content = builder(page)
        for n, (c, lbl) in nav_refs.items():
            active    = (n == name)
            c.bgcolor = DARK_CARD if active else SIDEBAR_BG
            lbl.color = TEXT_LIGHT if active else "#ccccee"
            lbl.weight = ft.FontWeight.BOLD if active else ft.FontWeight.NORMAL
        page.update()

    nav_col = ft.Column(spacing=4, tight=True)

    for name, emoji, builder in NAV_ITEMS:
        lbl = ft.Text(f"  {name}", size=13, color="#ccccee",
                      weight=ft.FontWeight.NORMAL)
        c = ft.Container(
            content=ft.Row([
                ft.Text(emoji, size=16),
                lbl,
            ], spacing=8, tight=True),
            bgcolor=SIDEBAR_BG,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            width=192,
            ink=True,
            on_click=lambda e, n=name, b=builder: show_view(n, b),
        )
        nav_refs[name] = (c, lbl)
        nav_col.controls.append(c)

    sidebar = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("🚗", size=38, text_align=ft.TextAlign.CENTER),
                        ft.Text("Car Rental", size=14,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT_LIGHT,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text("Management System", size=9,
                                color=TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                       spacing=2, tight=True),
                    padding=ft.padding.only(top=20, bottom=14),
                ),
                ft.Divider(height=1, color="#2a2a4e"),
                ft.Container(height=10),
                nav_col,
            ],
            spacing=0,
            tight=True,
        ),
        bgcolor=SIDEBAR_BG,
        width=210,
        padding=ft.padding.symmetric(horizontal=6),
    )

    page.add(
        ft.Row(
            controls=[
                sidebar,
                ft.VerticalDivider(width=1, color="#2a2a4e"),
                content_area,
            ],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )
    )

    show_view("Dashboard", dashboard_view)


ft.app(target=main)
