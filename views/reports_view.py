import flet as ft
from database.report_queries import get_vehicles_by_status, get_rentals_by_month, get_top_customers
from utils.theme import (
    BG, PRIMARY, SUCCESS, TEXT_LIGHT, TEXT_DARK, TEXT_GREY, TEXT_MUTED,
    CARD_BG, HEADER_BG, BORDER_COL, STATUS_COLORS,
    section_title, primary_btn, tbl_header
)


def reports_view(page: ft.Page) -> ft.Container:
    tab_content = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    def tbl_row(cells, widths, i=0):
        return ft.Container(
            content=ft.Row([
                ft.Text(str(v), width=w, size=12, color=TEXT_GREY)
                for v, w in zip(cells, widths)
            ]),
            bgcolor=CARD_BG if i % 2 == 0 else HEADER_BG,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )

    def show_status(e=None):
        rows = get_vehicles_by_status()
        tab_content.controls = [
            ft.Text("Resumen de Flota por Estado", size=15, weight="bold", color=TEXT_DARK),
            tbl_header(["Estado", "Cantidad"], [200, 200]),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(r["status"].capitalize(), size=12,
                                                color=TEXT_LIGHT, weight="bold"),
                                bgcolor=STATUS_COLORS.get(r["status"], "#546e7a"),
                                border_radius=20, width=200,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            ),
                            ft.Text(str(r["count"]), width=200, size=16,
                                    weight="bold", color=TEXT_DARK),
                        ]),
                        bgcolor=CARD_BG, border_radius=6,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    )
                    for r in rows
                ], spacing=2),
                bgcolor=CARD_BG,
                border=ft.border.all(1, BORDER_COL),
                border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
            ),
        ]
        page.update()

    def show_monthly(e=None):
        cols = ["Mes", "Total Rentas", "Ingresos"]; widths = [160, 160, 160]
        rows = get_rentals_by_month()
        tab_content.controls = [
            ft.Text("Ingresos por Mes", size=15, weight="bold", color=TEXT_DARK),
            tbl_header(cols, widths),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Text(r["month"],             width=widths[0], size=12, color=TEXT_GREY),
                            ft.Text(str(r["total_rentals"]),width=widths[1], size=12, color=TEXT_GREY),
                            ft.Text(f"${r['revenue']:,.2f}",width=widths[2], size=12,
                                    color=SUCCESS, weight="bold"),
                        ]),
                        bgcolor=CARD_BG if i % 2 == 0 else HEADER_BG,
                        border_radius=6,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    )
                    for i, r in enumerate(rows)
                ], spacing=2),
                bgcolor=CARD_BG,
                border=ft.border.all(1, BORDER_COL),
                border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
            ),
        ]
        page.update()

    def show_customers(e=None):
        cols = ["Cliente", "Rentas", "Total Gastado"]; widths = [240, 120, 180]
        rows = get_top_customers()
        tab_content.controls = [
            ft.Text("Top Clientes por Rentas", size=15, weight="bold", color=TEXT_DARK),
            tbl_header(cols, widths),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Text(r["full_name"],              width=widths[0], size=12, color=TEXT_DARK, weight="bold"),
                            ft.Text(str(r["total_rentals"]),     width=widths[1], size=12, color=TEXT_GREY),
                            ft.Text(f"${r['total_spent']:,.2f}", width=widths[2], size=12, color=SUCCESS, weight="bold"),
                        ]),
                        bgcolor=CARD_BG if i % 2 == 0 else HEADER_BG,
                        border_radius=6,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    )
                    for i, r in enumerate(rows)
                ], spacing=2),
                bgcolor=CARD_BG,
                border=ft.border.all(1, BORDER_COL),
                border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
            ),
        ]
        page.update()

    show_status()

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(text="Flota por Estado"),
            ft.Tab(text="Ingresos Mensuales"),
            ft.Tab(text="Top Clientes"),
        ],
        on_change=lambda e: [show_status, show_monthly, show_customers][e.control.selected_index](),
    )

    return ft.Container(
        content=ft.Column([
            ft.Row([section_title("📊 Reportes"),
                    primary_btn("⟳ Actualizar", show_status)],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=1, color=BORDER_COL),
            tabs,
            tab_content,
        ], spacing=12, expand=True),
        bgcolor=BG, padding=24, expand=True,
    )
