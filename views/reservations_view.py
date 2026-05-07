import flet as ft
from datetime import datetime
from database.rental_queries import get_all_reservations, add_reservation, cancel_reservation
from database.customer_queries import get_all_customers
from database.vehicle_queries import get_available_vehicles
from utils.theme import (
    BG, PRIMARY, SUCCESS, DANGER,
    CARD_BG, CARD_SEL, HEADER_BG, BORDER_COL,
    TEXT_DARK, TEXT_LIGHT, TEXT_GREY, TEXT_MUTED,
    RES_LABELS, mk_field, mk_dropdown,
    section_title, primary_btn, danger_btn,
    tbl_header, status_chip, info_banner, snack
)
from utils.modal import show_modal

RES_FILTER = ["Todos", "pending", "converted", "completed", "cancelled"]
COLS   = ["ID", "Cliente",   "Vehículo",   "Inicio",  "Fin",    "Estado"]
WIDTHS = [45,   180,          180,           110,       110,      130]


def _valid_date(s):
    try: datetime.strptime(s, "%Y-%m-%d"); return True
    except: return False


def reservations_view(page: ft.Page) -> ft.Container:
    selected  = {"data": None}
    filter_dd = mk_dropdown("Estado",
                            [ft.dropdown.Option(s, RES_LABELS.get(s, s.capitalize())) for s in RES_FILTER],
                            "Todos", width=180)
    table_body = ft.Column(spacing=1, scroll=ft.ScrollMode.AUTO, expand=True)

    def make_row(r):
        is_sel = selected["data"] and selected["data"]["id"] == r["id"]
        def on_click(e): selected["data"] = r; load()
        return ft.Container(
            content=ft.Row([
                ft.Text(str(r["id"]),       width=WIDTHS[0], size=12, color=TEXT_GREY),
                ft.Text(r["customer_name"], width=WIDTHS[1], size=12, color=TEXT_DARK, weight="bold"),
                ft.Text(r["vehicle"],       width=WIDTHS[2], size=12, color=TEXT_GREY),
                ft.Text(r["start_date"],    width=WIDTHS[3], size=12, color=TEXT_MUTED),
                ft.Text(r["end_date"],      width=WIDTHS[4], size=12, color=TEXT_MUTED),
                status_chip(r["status"], RES_LABELS.get(r["status"], r["status"]), WIDTHS[5]),
            ]),
            bgcolor=CARD_SEL if is_sel else CARD_BG,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_click=on_click, ink=True,
            border=ft.border.all(1, PRIMARY if is_sel else BORDER_COL),
        )

    def load(e=None):
        key = filter_dd.value or "Todos"
        filters = None if key == "Todos" else {"status": key}
        table_body.controls = [make_row(r) for r in get_all_reservations(filters)]
        page.update()

    def open_form(e=None):
        customers = get_all_customers()
        vehicles  = get_available_vehicles()
        if not customers:
            snack(page, "No hay clientes. Agrega uno primero.", error=True); return
        if not vehicles:
            snack(page, "No hay vehículos disponibles.", error=True); return

        f_cust  = mk_dropdown("Cliente *",
                              [ft.dropdown.Option(str(c["id"]), f"{c['id']} — {c['full_name']}") for c in customers],
                              width=420)
        f_veh   = mk_dropdown("Vehículo *",
                              [ft.dropdown.Option(str(v["id"]), f"{v['id']} — {v['brand']} {v['model']} (${v['rate_per_day']:.2f}/día)") for v in vehicles],
                              width=420)
        f_start = mk_field("Fecha Inicio (YYYY-MM-DD) *", width=200)
        f_end   = mk_field("Fecha Fin   (YYYY-MM-DD) *", width=200)
        err     = ft.Text("", color=DANGER, size=13)
        close_fn = {"fn": None}

        def save(e):
            if not f_cust.value:
                err.value = "⚠ Selecciona un cliente."; page.update(); return
            if not f_veh.value:
                err.value = "⚠ Selecciona un vehículo."; page.update(); return
            start = (f_start.value or "").strip()
            end   = (f_end.value   or "").strip()
            if not start or not _valid_date(start):
                err.value = "⚠ Fecha inicio inválida. Formato: YYYY-MM-DD"; page.update(); return
            if not end or not _valid_date(end):
                err.value = "⚠ Fecha fin inválida. Formato: YYYY-MM-DD"; page.update(); return
            if end <= start:
                err.value = "⚠ La fecha fin debe ser posterior al inicio."; page.update(); return

            ok, msg = add_reservation(int(f_cust.value), int(f_veh.value), start, end)
            if ok:
                if close_fn["fn"]: close_fn["fn"]()
                snack(page, msg); load()
            else:
                err.value = f"⚠ {msg}"; page.update()

        content = ft.Column([
            f_cust, f_veh,
            ft.Row([f_start, f_end], spacing=12),
            info_banner("ℹ️ Al crear una renta con este vehículo y fechas,\nla reserva se convertirá automáticamente."),
            err,
        ], spacing=14, tight=True)

        actions = [
            ft.ElevatedButton("💾 Guardar", on_click=save, bgcolor=SUCCESS, color=TEXT_LIGHT),
            ft.ElevatedButton("Cancelar",
                              on_click=lambda e: close_fn["fn"]() if close_fn["fn"] else None,
                              bgcolor=HEADER_BG, color=TEXT_MUTED),
        ]
        close_fn["fn"] = show_modal(page, "📅 Nueva Reservación", content, actions, width=480)

    def cancel_res(e):
        if not selected["data"]:
            snack(page, "Selecciona una reserva primero.", error=True); return
        r = selected["data"]
        if r["status"] != "pending":
            snack(page, f"Solo puedes cancelar reservas Pendientes. Esta está: {RES_LABELS.get(r['status'], r['status'])}.", error=True); return

        close_fn = {"fn": None}
        def do_cancel(e):
            ok, msg = cancel_reservation(r["id"])
            if close_fn["fn"]: close_fn["fn"]()
            snack(page, msg, error=not ok)
            if ok: selected["data"] = None; load()

        content = ft.Text(f"¿Cancelar reserva #{r['id']} de {r['customer_name']}?",
                          color=TEXT_GREY, size=14)
        actions = [
            ft.ElevatedButton("❌ Cancelar Reserva", on_click=do_cancel, bgcolor=DANGER, color=TEXT_LIGHT),
            ft.ElevatedButton("Volver",
                              on_click=lambda e: close_fn["fn"]() if close_fn["fn"] else None,
                              bgcolor=HEADER_BG, color=TEXT_MUTED),
        ]
        close_fn["fn"] = show_modal(page, "⚠️ Confirmar Cancelación", content, actions, width=380)

    load()

    return ft.Container(
        content=ft.Column([
            ft.Row([section_title("📅 Reservaciones")]),
            ft.Divider(height=1, color=BORDER_COL),
            ft.Row([filter_dd, primary_btn("Filtrar", load)], spacing=8),
            ft.Row([primary_btn("➕ Nueva Reserva",   open_form,  SUCCESS),
                    danger_btn("❌ Cancelar Reserva", cancel_res)], spacing=8),
            tbl_header(COLS, WIDTHS),
            ft.Container(
                content=table_body, expand=True, bgcolor=CARD_BG,
                border=ft.border.all(1, BORDER_COL),
                border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
            ),
        ], spacing=12, expand=True),
        bgcolor=BG, padding=24, expand=True,
    )
