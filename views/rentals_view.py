import flet as ft
from datetime import datetime
from database.rental_queries import (
    get_all_rentals, start_rental, complete_rental,
    calculate_rental_cost, get_all_reservations
)
from database.customer_queries import get_all_customers
from database.vehicle_queries import get_all_vehicles
from utils.theme import (
    BG, PRIMARY, SUCCESS, WARNING, DANGER, PURPLE, PANEL_BLUE,
    CARD_BG, CARD_SEL, HEADER_BG, BORDER_COL,
    TEXT_DARK, TEXT_LIGHT, TEXT_GREY, TEXT_MUTED, RENT_LABELS,
    section_title, primary_btn, tbl_header, mk_field, mk_dropdown,
    status_chip, snack, info_banner
)
from utils.modal import show_modal

RENT_FILTER = ["Todos", "active", "completed", "late"]
COLS   = ["ID", "Cliente",   "Vehículo",   "Inicio",  "Fin",    "Costo",   "Estado"]
WIDTHS = [45,   160,          155,           105,       105,      95,        110]


def _valid_date(s):
    try: datetime.strptime(s, "%Y-%m-%d"); return True
    except: return False


def rentals_view(page: ft.Page) -> ft.Container:
    selected  = {"data": None}
    filter_dd = mk_dropdown("Estado",
                            [ft.dropdown.Option(s, RENT_LABELS.get(s, s.capitalize())) for s in RENT_FILTER],
                            "Todos", width=180)
    table_body = ft.Column(spacing=1, scroll=ft.ScrollMode.AUTO, expand=True)

    def make_row(r):
        is_sel = selected["data"] and selected["data"]["id"] == r["id"]
        cost   = f"${r['total_cost']:.2f}" if r["total_cost"] else "—"
        def on_click(e): selected["data"] = r; load()
        return ft.Container(
            content=ft.Row([
                ft.Text(str(r["id"]),        width=WIDTHS[0], size=12, color=TEXT_GREY),
                ft.Text(r["customer_name"],  width=WIDTHS[1], size=12, color=TEXT_DARK, weight="bold"),
                ft.Text(r["vehicle"],        width=WIDTHS[2], size=12, color=TEXT_GREY),
                ft.Text(r["start_date"],     width=WIDTHS[3], size=12, color=TEXT_MUTED),
                ft.Text(r["end_date"],       width=WIDTHS[4], size=12, color=TEXT_MUTED),
                ft.Text(cost,                width=WIDTHS[5], size=12, color=SUCCESS, weight="bold"),
                status_chip(r["rental_status"],
                            RENT_LABELS.get(r["rental_status"], r["rental_status"]),
                            WIDTHS[6]),
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
        table_body.controls = [make_row(r) for r in get_all_rentals(filters)]
        page.update()

    def open_form(e=None):
        customers    = get_all_customers()
        all_vehicles = (get_all_vehicles({"status": "available"}) +
                        get_all_vehicles({"status": "reserved"}))
        pending_res  = get_all_reservations({"status": "pending"})
        vehicle_map  = {str(v["id"]): v for v in all_vehicles}

        if not customers:
            snack(page, "No hay clientes registrados.", error=True); return
        if not all_vehicles:
            snack(page, "No hay vehículos disponibles o reservados.", error=True); return

        res_opts = [ft.dropdown.Option(str(r["id"]),
                     f"#{r['id']} {r['customer_name']} | {r['vehicle']} | {r['start_date']}→{r['end_date']}")
                    for r in pending_res]

        f_res   = mk_dropdown("Cargar desde reserva pendiente (opcional)", res_opts, width=500)
        f_cust  = mk_dropdown("Cliente *",
                              [ft.dropdown.Option(str(c["id"]), f"{c['id']} — {c['full_name']}") for c in customers],
                              width=340)
        f_veh   = mk_dropdown("Vehículo *",
                              [ft.dropdown.Option(str(v["id"]), f"{v['id']} — {v['brand']} {v['model']} (${v['rate_per_day']:.2f}/día)") for v in all_vehicles],
                              width=340)
        f_start = mk_field("Fecha Inicio (YYYY-MM-DD) *", width=190)
        f_end   = mk_field("Fecha Fin   (YYYY-MM-DD) *", width=190)

        cost_txt  = ft.Text("— Llena los campos y presiona Calcular —", size=12, color=TEXT_MUTED)
        total_txt = ft.Text("", size=15, weight="bold", color=SUCCESS)
        conv_txt  = ft.Text("", size=11, color=PURPLE, italic=True)
        err_txt   = ft.Text("", color=DANGER, size=13)
        cost_ok   = {"value": False, "rate": 0.0}
        close_fn  = {"fn": None}

        confirm_btn = ft.ElevatedButton(
            "✅ Confirmar Renta", bgcolor=HEADER_BG, color=TEXT_MUTED, disabled=True,
        )

        def load_from_res(e):
            if not f_res.value: return
            res = next((r for r in pending_res if str(r["id"]) == f_res.value), None)
            if not res: return
            f_cust.value = str(res["customer_id"])
            f_veh.value  = str(res["vehicle_id"])
            f_start.value = res["start_date"]
            f_end.value   = res["end_date"]
            cost_ok["value"] = False
            confirm_btn.disabled = True; confirm_btn.bgcolor = HEADER_BG; confirm_btn.color = TEXT_MUTED
            cost_txt.value = "— Datos cargados. Presiona Calcular —"
            total_txt.value = ""
            conv_txt.value  = f"⚡ Reserva #{res['id']} — {res['customer_name']}"
            page.update()

        f_res.on_change = load_from_res

        def clear_res(e):
            f_res.value = f_cust.value = f_veh.value = f_start.value = f_end.value = ""
            cost_ok["value"] = False
            confirm_btn.disabled = True; confirm_btn.bgcolor = HEADER_BG; confirm_btn.color = TEXT_MUTED
            cost_txt.value = "— Llena los campos y presiona Calcular —"
            total_txt.value = conv_txt.value = err_txt.value = ""
            page.update()

        def calculate(e):
            err_txt.value = ""
            if not f_cust.value: err_txt.value = "⚠ Selecciona un cliente."; page.update(); return
            if not f_veh.value:  err_txt.value = "⚠ Selecciona un vehículo."; page.update(); return
            start = (f_start.value or "").strip()
            end   = (f_end.value   or "").strip()
            if not start or not _valid_date(start):
                err_txt.value = "⚠ Fecha inicio inválida. Formato: YYYY-MM-DD"; page.update(); return
            if not end or not _valid_date(end):
                err_txt.value = "⚠ Fecha fin inválida. Formato: YYYY-MM-DD"; page.update(); return

            vid     = int(f_veh.value)
            vehicle = vehicle_map.get(str(vid))
            ok, days, total, msg = calculate_rental_cost(vid, start, end)

            if not ok:
                cost_txt.value = f"⚠ {msg}"; total_txt.value = ""
                cost_ok["value"] = False
                confirm_btn.disabled = True; confirm_btn.bgcolor = HEADER_BG; confirm_btn.color = TEXT_MUTED
            else:
                cost_txt.value  = f"{days} día(s)  ×  ${vehicle['rate_per_day']:.2f}/día"
                total_txt.value = f"Total a cobrar:  ${total:.2f}"
                cost_ok["value"] = True; cost_ok["rate"] = vehicle["rate_per_day"]
                confirm_btn.disabled = False; confirm_btn.bgcolor = SUCCESS; confirm_btn.color = TEXT_LIGHT
                from database.db import get_connection
                conn = get_connection()
                row = conn.execute("""
                    SELECT id FROM reservations WHERE vehicle_id=? AND status='pending'
                    AND NOT (end_date < ? OR start_date > ?) LIMIT 1
                """, (vid, start, end)).fetchone()
                conn.close()
                conv_txt.value = f"⚡ Reserva #{row['id']} se convertirá automáticamente." if row else ""
            page.update()

        def confirm_rental(e):
            if not cost_ok["value"]: return
            err_txt.value = ""
            vid = int(f_veh.value); cid = int(f_cust.value)
            start = f_start.value.strip(); end = f_end.value.strip()
            ok, msg, _ = start_rental(cid, vid, start, end, cost_ok["rate"])
            if ok:
                if close_fn["fn"]: close_fn["fn"]()
                snack(page, msg); load()
            else:
                err_txt.value = f"⚠ {msg}"; page.update()

        confirm_btn.on_click = confirm_rental

        content = ft.Column([
            # Reservation loader box
            ft.Container(
                content=ft.Column([
                    ft.Text("📋 Cargar desde Reserva Pendiente (opcional)",
                            size=12, weight="bold", color=PURPLE),
                    ft.Row([f_res,
                            ft.ElevatedButton("✕ Limpiar", on_click=clear_res,
                                              bgcolor=HEADER_BG, color=TEXT_MUTED)],
                           spacing=8),
                ], spacing=8, tight=True),
                bgcolor="#231a33", border_radius=8, padding=12,
                border=ft.border.all(1, PURPLE),
            ),
            ft.Divider(height=1, color=BORDER_COL),
            ft.Text("📝 Datos de la Renta", size=12, weight="bold", color=TEXT_DARK),
            f_cust, f_veh,
            ft.Row([f_start, f_end], spacing=12),
            ft.Divider(height=1, color=BORDER_COL),
            ft.Container(
                content=ft.Column([
                    ft.Text("💰 Costo", size=12, weight="bold", color=TEXT_DARK),
                    cost_txt, total_txt, conv_txt,
                ], spacing=4, tight=True),
                bgcolor=PANEL_BLUE, border_radius=8, padding=10,
                border=ft.border.all(1, PRIMARY),
            ),
            err_txt,
        ], spacing=10, tight=True, scroll=ft.ScrollMode.AUTO)

        actions = [
            ft.ElevatedButton("🧮 Calcular Costo", on_click=calculate, bgcolor=WARNING, color=TEXT_LIGHT),
            confirm_btn,
            ft.ElevatedButton("Cancelar",
                              on_click=lambda e: close_fn["fn"]() if close_fn["fn"] else None,
                              bgcolor=HEADER_BG, color=TEXT_MUTED),
        ]
        close_fn["fn"] = show_modal(page, "🔑 Nueva Renta", content, actions, width=580, height=480)

    def complete(e):
        if not selected["data"]: snack(page, "Selecciona una renta primero.", error=True); return
        r = selected["data"]
        if r["rental_status"] == "completed":
            snack(page, "Esta renta ya está completada.", error=True); return

        close_fn = {"fn": None}
        def do_complete(ev):
            ok, msg = complete_rental(r["id"])
            if close_fn["fn"]: close_fn["fn"]()
            snack(page, msg, error=not ok)
            if ok: selected["data"] = None; load()

        content = ft.Text(
            f"¿Marcar como completada la renta #{r['id']} de {r['customer_name']}?",
            color=TEXT_GREY, size=14,
        )
        actions = [
            ft.ElevatedButton("✅ Completar", on_click=do_complete, bgcolor=SUCCESS, color=TEXT_LIGHT),
            ft.ElevatedButton("Cancelar",
                              on_click=lambda e: close_fn["fn"]() if close_fn["fn"] else None,
                              bgcolor=HEADER_BG, color=TEXT_MUTED),
        ]
        close_fn["fn"] = show_modal(page, "✅ Confirmar Completar Renta", content, actions, width=400)

    load()

    return ft.Container(
        content=ft.Column([
            ft.Row([section_title("🔑 Rentas")]),
            ft.Divider(height=1, color=BORDER_COL),
            ft.Row([filter_dd, primary_btn("Filtrar", load)], spacing=8),
            ft.Row([primary_btn("➕ Nueva Renta",     open_form, SUCCESS),
                    primary_btn("✅ Completar Renta", complete,  PRIMARY)], spacing=8),
            tbl_header(COLS, WIDTHS),
            ft.Container(
                content=table_body, expand=True, bgcolor=CARD_BG,
                border=ft.border.all(1, BORDER_COL),
                border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
            ),
        ], spacing=12, expand=True),
        bgcolor=BG, padding=24, expand=True,
    )
