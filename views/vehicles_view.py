import flet as ft
from database.vehicle_queries import (
    get_all_vehicles, add_vehicle, update_vehicle, delete_vehicle
)
from utils.theme import (
    BG, PRIMARY, SUCCESS, WARNING, DANGER,
    CARD_BG, CARD_SEL, HEADER_BG, BORDER_COL,
    TEXT_DARK, TEXT_LIGHT, TEXT_GREY, TEXT_MUTED,
    VEHICLE_TYPES, VEHICLE_STATUSES,
    section_title, primary_btn, danger_btn, mk_field, mk_dropdown,
    status_chip, tbl_header, snack
)
from utils.modal import show_modal

COLS   = ["ID", "Marca", "Modelo", "Año",  "Tipo",  "Tarifa/Día", "Estado"]
WIDTHS = [45,   120,     120,      60,     110,     100,           110]


def vehicles_view(page: ft.Page) -> ft.Container:
    selected      = {"data": None}
    filter_brand  = mk_field("Marca", width=150)
    filter_type   = mk_dropdown("Tipo",
                                [ft.dropdown.Option("Todos")] + [ft.dropdown.Option(t) for t in VEHICLE_TYPES],
                                "Todos", width=130)
    filter_status = mk_dropdown("Estado",
                                [ft.dropdown.Option("Todos")] + [ft.dropdown.Option(s) for s in VEHICLE_STATUSES],
                                "Todos", width=140)
    table_body = ft.Column(spacing=1, scroll=ft.ScrollMode.AUTO, expand=True)

    def make_row(v):
        is_sel = selected["data"] and selected["data"]["id"] == v["id"]
        def on_click(e): selected["data"] = v; load()
        return ft.Container(
            content=ft.Row([
                ft.Text(str(v["id"]),                width=WIDTHS[0], size=12, color=TEXT_GREY),
                ft.Text(v["brand"],                  width=WIDTHS[1], size=12, color=TEXT_DARK),
                ft.Text(v["model"],                  width=WIDTHS[2], size=12, color=TEXT_DARK),
                ft.Text(str(v["year"]),              width=WIDTHS[3], size=12, color=TEXT_GREY),
                ft.Text(v["vehicle_type"],           width=WIDTHS[4], size=12, color=TEXT_GREY),
                ft.Text(f"${v['rate_per_day']:.2f}", width=WIDTHS[5], size=12, color=SUCCESS, weight="bold"),
                status_chip(v["status"], width=WIDTHS[6]),
            ]),
            bgcolor=CARD_SEL if is_sel else CARD_BG,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_click=on_click, ink=True,
            border=ft.border.all(1, PRIMARY if is_sel else BORDER_COL),
        )

    def load(e=None):
        filters = {}
        if filter_brand.value and filter_brand.value.strip():
            filters["brand"] = filter_brand.value.strip()
        if filter_type.value and filter_type.value != "Todos":
            filters["vehicle_type"] = filter_type.value
        if filter_status.value and filter_status.value != "Todos":
            filters["status"] = filter_status.value
        table_body.controls = [make_row(v) for v in get_all_vehicles(filters or None)]
        page.update()

    def clear_filters(e):
        filter_brand.value = ""; filter_type.value = "Todos"; filter_status.value = "Todos"
        selected["data"] = None; load()

    def open_form(vehicle=None):
        ie = vehicle is not None
        f_brand  = mk_field("Marca *",           vehicle["brand"]              if ie else "", width=210)
        f_model  = mk_field("Modelo *",          vehicle["model"]              if ie else "", width=210)
        f_year   = mk_field("Año *",             str(vehicle["year"])          if ie else "", ft.KeyboardType.NUMBER, width=140)
        f_rate   = mk_field("Tarifa/Día ($) *",  str(vehicle["rate_per_day"]) if ie else "", ft.KeyboardType.NUMBER, width=140)
        f_type   = mk_dropdown("Tipo *",
                               [ft.dropdown.Option(t) for t in VEHICLE_TYPES],
                               vehicle["vehicle_type"] if ie else VEHICLE_TYPES[0], width=210)
        f_status = mk_dropdown("Estado *",
                               [ft.dropdown.Option(s) for s in VEHICLE_STATUSES],
                               vehicle["status"] if ie else "available", width=210)
        err = ft.Text("", color=DANGER, size=13)
        close_fn = {"fn": None}

        def save(e):
            brand = (f_brand.value or "").strip()
            model = (f_model.value or "").strip()
            if not brand:
                err.value = "⚠ La Marca es obligatoria."; page.update(); return
            if not model:
                err.value = "⚠ El Modelo es obligatorio."; page.update(); return
            try:
                year = int(f_year.value or "")
                if not (1900 <= year <= 2030): raise ValueError
            except (ValueError, TypeError):
                err.value = "⚠ Año inválido (ej: 2022)."; page.update(); return
            try:
                rate = float(f_rate.value or "")
                if rate <= 0: raise ValueError
            except (ValueError, TypeError):
                err.value = "⚠ Tarifa debe ser un número mayor a 0."; page.update(); return

            if ie:
                ok, msg = update_vehicle(vehicle["id"], brand, model, year, f_type.value, rate, f_status.value)
            else:
                ok, msg = add_vehicle(brand, model, year, f_type.value, rate, f_status.value)

            if ok:
                if close_fn["fn"]: close_fn["fn"]()
                snack(page, msg); selected["data"] = None; load()
            else:
                err.value = f"⚠ {msg}"; page.update()

        content = ft.Column([
            ft.Row([f_brand, f_model], spacing=12),
            ft.Row([f_year,  f_rate],  spacing=12),
            ft.Row([f_type,  f_status], spacing=12),
            err,
        ], spacing=14, tight=True)

        actions = [
            ft.ElevatedButton("💾 Guardar", on_click=save, bgcolor=SUCCESS, color=TEXT_LIGHT),
            ft.ElevatedButton("Cancelar",
                              on_click=lambda e: close_fn["fn"]() if close_fn["fn"] else None,
                              bgcolor=HEADER_BG, color=TEXT_MUTED),
        ]
        close_fn["fn"] = show_modal(page, "✏️ Editar Vehículo" if ie else "➕ Nuevo Vehículo",
                                    content, actions, width=500)

    def confirm_delete(vehicle):
        close_fn = {"fn": None}
        def do_delete(e):
            ok, msg = delete_vehicle(vehicle["id"])
            if close_fn["fn"]: close_fn["fn"]()
            snack(page, msg, error=not ok)
            if ok: selected["data"] = None; load()

        content = ft.Text(
            f"¿Eliminar {vehicle['brand']} {vehicle['model']} ({vehicle['year']})?\nEsta acción no se puede deshacer.",
            color=TEXT_GREY, size=14,
        )
        actions = [
            ft.ElevatedButton("🗑 Eliminar", on_click=do_delete, bgcolor=DANGER, color=TEXT_LIGHT),
            ft.ElevatedButton("Cancelar",
                              on_click=lambda e: close_fn["fn"]() if close_fn["fn"] else None,
                              bgcolor=HEADER_BG, color=TEXT_MUTED),
        ]
        close_fn["fn"] = show_modal(page, "⚠️ Confirmar Eliminación", content, actions, width=380)

    def edit(e):
        if not selected["data"]: snack(page, "Selecciona un vehículo primero.", error=True); return
        open_form(selected["data"])

    def delete(e):
        if not selected["data"]: snack(page, "Selecciona un vehículo primero.", error=True); return
        confirm_delete(selected["data"])

    load()

    return ft.Container(
        content=ft.Column([
            ft.Row([section_title("🚙 Vehículos")]),
            ft.Divider(height=1, color=BORDER_COL),
            ft.Row([filter_brand, filter_type, filter_status,
                    primary_btn("🔍 Buscar", load),
                    ft.ElevatedButton("Limpiar", on_click=clear_filters,
                                      bgcolor=HEADER_BG, color=TEXT_MUTED)],
                   spacing=8, wrap=True),
            ft.Row([primary_btn("➕ Agregar", lambda e: open_form(), SUCCESS),
                    primary_btn("✏️ Editar",  edit, WARNING),
                    danger_btn("🗑 Eliminar",  delete)], spacing=8),
            tbl_header(COLS, WIDTHS),
            ft.Container(
                content=table_body, expand=True, bgcolor=CARD_BG,
                border=ft.border.all(1, BORDER_COL),
                border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
            ),
        ], spacing=12, expand=True),
        bgcolor=BG, padding=24, expand=True,
    )
