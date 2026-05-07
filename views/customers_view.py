import flet as ft
import re
from database.customer_queries import (
    get_all_customers, add_customer, update_customer, delete_customer
)
from utils.theme import (
    BG, PRIMARY, SUCCESS, WARNING, DANGER,
    CARD_BG, CARD_SEL, HEADER_BG, BORDER_COL,
    TEXT_DARK, TEXT_LIGHT, TEXT_GREY, TEXT_MUTED,
    section_title, primary_btn, danger_btn, mk_field,
    tbl_header, snack
)
from utils.modal import show_modal

COLS   = ["ID", "Nombre",   "Teléfono",  "Email",   "Licencia"]
WIDTHS = [45,   180,         130,          200,        150]


def customers_view(page: ft.Page) -> ft.Container:
    selected   = {"data": None}
    search_fld = mk_field("Buscar por nombre, teléfono, email o licencia...", width=420)
    table_body = ft.Column(spacing=1, scroll=ft.ScrollMode.AUTO, expand=True)

    def make_row(c):
        is_sel = selected["data"] and selected["data"]["id"] == c["id"]
        def on_click(e): selected["data"] = c; load()
        return ft.Container(
            content=ft.Row([
                ft.Text(str(c["id"]),        width=WIDTHS[0], size=12, color=TEXT_GREY),
                ft.Text(c["full_name"],      width=WIDTHS[1], size=12, color=TEXT_DARK, weight="bold"),
                ft.Text(c["phone"],          width=WIDTHS[2], size=12, color=TEXT_GREY),
                ft.Text(c["email"] or "—",   width=WIDTHS[3], size=12, color=TEXT_MUTED),
                ft.Text(c["license_number"], width=WIDTHS[4], size=12, color=TEXT_GREY),
            ]),
            bgcolor=CARD_SEL if is_sel else CARD_BG,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_click=on_click, ink=True,
            border=ft.border.all(1, PRIMARY if is_sel else BORDER_COL),
        )

    def load(e=None):
        s = search_fld.value.strip() if search_fld.value else None
        table_body.controls = [make_row(c) for c in get_all_customers(s or None)]
        page.update()

    def clear_search(e):
        search_fld.value = ""; selected["data"] = None; load()

    def open_form(customer=None):
        ie = customer is not None
        f_name  = mk_field("Nombre completo *", customer["full_name"]      if ie else "", width=400)
        f_phone = mk_field("Teléfono *",        customer["phone"]          if ie else "", width=190)
        f_email = mk_field("Email (opcional)",  customer["email"] or ""    if ie else "", width=250)
        f_lic   = mk_field("No. Licencia *",    customer["license_number"] if ie else "", width=190)
        err     = ft.Text("", color=DANGER, size=13)

        close_fn = {"fn": None}

        def save(e):
            name  = (f_name.value  or "").strip()
            phone = (f_phone.value or "").strip()
            email = (f_email.value or "").strip()
            lic   = (f_lic.value   or "").strip()

            if not name:
                err.value = "⚠ El nombre completo es obligatorio."; page.update(); return
            if not phone:
                err.value = "⚠ El teléfono es obligatorio."; page.update(); return
            if not lic:
                err.value = "⚠ El número de licencia es obligatorio."; page.update(); return
            if email and not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email):
                err.value = "⚠ El email no tiene formato válido."; page.update(); return

            if ie:
                ok, msg = update_customer(customer["id"], name, phone, email, lic)
            else:
                ok, msg = add_customer(name, phone, email, lic)

            if ok:
                if close_fn["fn"]: close_fn["fn"]()
                snack(page, msg)
                selected["data"] = None
                load()
            else:
                err.value = f"⚠ {msg}"; page.update()

        content = ft.Column([
            f_name,
            ft.Row([f_phone, f_email], spacing=12),
            f_lic,
            err,
        ], spacing=14, tight=True)

        actions = [
            ft.ElevatedButton("💾 Guardar", on_click=save, bgcolor=SUCCESS, color=TEXT_LIGHT),
            ft.ElevatedButton("Cancelar",
                              on_click=lambda e: close_fn["fn"]() if close_fn["fn"] else None,
                              bgcolor=HEADER_BG, color=TEXT_MUTED),
        ]

        title = "✏️ Editar Cliente" if ie else "➕ Nuevo Cliente"
        close_fn["fn"] = show_modal(page, title, content, actions, width=480)

    def confirm_delete(customer):
        close_fn = {"fn": None}

        def do_delete(e):
            ok, msg = delete_customer(customer["id"])
            if close_fn["fn"]: close_fn["fn"]()
            snack(page, msg, error=not ok)
            if ok: selected["data"] = None; load()

        content = ft.Text(
            f"¿Estás seguro de eliminar a {customer['full_name']}?\nEsta acción no se puede deshacer.",
            color=TEXT_GREY, size=14,
        )
        actions = [
            ft.ElevatedButton("🗑 Eliminar", on_click=do_delete, bgcolor=DANGER, color=TEXT_LIGHT),
            ft.ElevatedButton("Cancelar",
                              on_click=lambda e: close_fn["fn"]() if close_fn["fn"] else None,
                              bgcolor=HEADER_BG, color=TEXT_MUTED),
        ]
        close_fn["fn"] = show_modal(page, "⚠️ Confirmar Eliminación", content, actions, width=400)

    def edit(e):
        if not selected["data"]:
            snack(page, "Selecciona un cliente de la tabla primero.", error=True); return
        open_form(selected["data"])

    def delete(e):
        if not selected["data"]:
            snack(page, "Selecciona un cliente de la tabla primero.", error=True); return
        confirm_delete(selected["data"])

    load()

    return ft.Container(
        content=ft.Column([
            ft.Row([section_title("👥 Clientes")]),
            ft.Divider(height=1, color=BORDER_COL),
            ft.Row([search_fld,
                    primary_btn("🔍 Buscar", load),
                    ft.ElevatedButton("Limpiar", on_click=clear_search,
                                      bgcolor=HEADER_BG, color=TEXT_MUTED)],
                   spacing=8),
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
