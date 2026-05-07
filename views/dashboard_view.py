import flet as ft
from database.report_queries import get_dashboard_stats
from utils.theme import (
    BG, PRIMARY, SUCCESS, WARNING, DANGER, PURPLE,
    TEXT_DARK, TEXT_MUTED, BORDER_COL,
    stat_card, section_title, primary_btn
)


def dashboard_view(page: ft.Page) -> ft.Container:
    row1 = ft.Row(expand=False)
    row2 = ft.Row(expand=False)
    row3 = ft.Row(expand=False)

    def refresh(e=None):
        s = get_dashboard_stats()
        row1.controls = [
            stat_card("🚙 Total Vehículos",    s["total_vehicles"],       PRIMARY),
            stat_card("✅ Disponibles",         s["available_vehicles"],   SUCCESS),
            stat_card("🔑 Rentados",            s["rented_vehicles"],      WARNING),
        ]
        row2.controls = [
            stat_card("📅 Reservados",          s["reserved_vehicles"],    PURPLE),
            stat_card("🔧 Mantenimiento",       s["maintenance_vehicles"], DANGER),
            stat_card("👥 Clientes",            s["total_customers"],      "#2980b9"),
        ]
        row3.controls = [
            stat_card("📋 Rentas Activas",      s["active_rentals"],       "#16a085"),
            stat_card("🗓 Reservas Pendientes", s["pending_reservations"], "#d35400"),
            stat_card("💵 Ingresos Totales",    f"${s['total_revenue']:,.2f}", "#1abc9c"),
        ]
        page.update()

    refresh()

    return ft.Container(
        content=ft.Column([
            ft.Row([
                section_title("🚗  Dashboard"),
                primary_btn("⟳ Actualizar", refresh),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=1, color=BORDER_COL),
            ft.Text("Resumen de la flota", size=14, color=TEXT_MUTED),
            row1, row2, row3,
        ], spacing=16, scroll=ft.ScrollMode.AUTO),
        bgcolor=BG, padding=24, expand=True,
    )
