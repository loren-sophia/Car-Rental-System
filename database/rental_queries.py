from database.db import get_connection
from datetime import datetime


def _calc_days(start: str, end: str) -> int:
    return (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days


def check_conflict(vehicle_id, start, end, table="reservations", exclude_id=None):
    conn = get_connection()
    q = f"""SELECT COUNT(*) FROM {table}
            WHERE vehicle_id=?
              AND status NOT IN ('cancelled','completed','converted')
              AND NOT (end_date < ? OR start_date > ?)"""
    p = [vehicle_id, start, end]
    if exclude_id:
        q += " AND id!=?"; p.append(exclude_id)
    n = conn.execute(q, p).fetchone()[0]
    conn.close()
    return n > 0


# ── RESERVATIONS ──────────────────────────────────────────────────────────────

def get_all_reservations(filters=None):
    conn = get_connection()
    q = """SELECT res.id, c.full_name AS customer_name,
                  v.brand||' '||v.model AS vehicle,
                  res.start_date, res.end_date, res.status,
                  res.customer_id, res.vehicle_id
           FROM reservations res
           JOIN customers c ON res.customer_id=c.id
           JOIN vehicles  v ON res.vehicle_id=v.id
           WHERE 1=1"""
    p = []
    if filters:
        if filters.get("status"):
            q += " AND res.status=?"; p.append(filters["status"])
    q += " ORDER BY res.start_date DESC"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_reservation(customer_id, vehicle_id, start, end):
    if check_conflict(vehicle_id, start, end):
        return False, "El vehículo ya tiene una reserva en esas fechas."
    if check_conflict(vehicle_id, start, end, table="rentals"):
        return False, "El vehículo ya está rentado en esas fechas."
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO reservations (customer_id,vehicle_id,start_date,end_date,status) VALUES(?,?,?,?,'pending')",
            (customer_id, vehicle_id, start, end))
        conn.execute("UPDATE vehicles SET status='reserved' WHERE id=?", (vehicle_id,))
        conn.commit()
        return True, "Reserva creada exitosamente."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def cancel_reservation(res_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT vehicle_id FROM reservations WHERE id=?", (res_id,)).fetchone()
        if not row: return False, "Reserva no encontrada."
        vid = row["vehicle_id"]
        conn.execute("UPDATE reservations SET status='cancelled' WHERE id=?", (res_id,))
        others = conn.execute(
            "SELECT COUNT(*) FROM reservations WHERE vehicle_id=? AND status='pending' AND id!=?",
            (vid, res_id)).fetchone()[0]
        if others == 0:
            conn.execute("UPDATE vehicles SET status='available' WHERE id=?", (vid,))
        conn.commit()
        return True, "Reserva cancelada."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ── RENTALS ───────────────────────────────────────────────────────────────────

def get_all_rentals(filters=None):
    conn = get_connection()
    q = "SELECT * FROM rental_summary WHERE 1=1"
    p = []
    if filters and filters.get("status"):
        q += " AND rental_status=?"; p.append(filters["status"])
    q += " ORDER BY start_date DESC"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def calculate_rental_cost(vehicle_id, start, end):
    days = _calc_days(start, end)
    if days <= 0:
        return False, 0, 0.0, "La fecha fin debe ser posterior al inicio."
    conn = get_connection()
    row = conn.execute("SELECT rate_per_day FROM vehicles WHERE id=?", (vehicle_id,)).fetchone()
    conn.close()
    if not row: return False, 0, 0.0, "Vehículo no encontrado."
    total = days * row["rate_per_day"]
    return True, days, total, f"{days} día(s) × ${row['rate_per_day']:.2f}/día = ${total:.2f}"


def start_rental(customer_id, vehicle_id, start, end, rate_per_day):
    if check_conflict(vehicle_id, start, end, table="rentals"):
        return False, "El vehículo ya tiene una renta activa en esas fechas.", None
    days = _calc_days(start, end)
    if days <= 0:
        return False, "La fecha fin debe ser posterior al inicio.", None
    total_cost = days * rate_per_day
    conn = get_connection()
    try:
        existing = conn.execute("""
            SELECT * FROM reservations
            WHERE vehicle_id=? AND status='pending'
              AND NOT (end_date < ? OR start_date > ?)
            ORDER BY start_date LIMIT 1""",
            (vehicle_id, start, end)).fetchone()
        converted_id = None
        if existing:
            converted_id = existing["id"]
            conn.execute("UPDATE reservations SET status='converted' WHERE id=?", (converted_id,))
        conn.execute(
            "INSERT INTO rentals (customer_id,vehicle_id,start_date,end_date,total_cost,status,reservation_id) "
            "VALUES(?,?,?,?,?,'active',?)",
            (customer_id, vehicle_id, start, end, total_cost, converted_id))
        conn.execute("UPDATE vehicles SET status='rented' WHERE id=?", (vehicle_id,))
        conn.commit()
        msg = f"Renta iniciada. Total: ${total_cost:.2f}"
        if converted_id:
            msg += f"\n✅ Reserva #{converted_id} convertida automáticamente."
        return True, msg, converted_id
    except Exception as e:
        return False, str(e), None
    finally:
        conn.close()


def complete_rental(rental_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT vehicle_id FROM rentals WHERE id=?", (rental_id,)).fetchone()
        if not row: return False, "Renta no encontrada."
        vid = row["vehicle_id"]
        conn.execute("UPDATE rentals SET status='completed' WHERE id=?", (rental_id,))
        conn.execute("""UPDATE reservations SET status='completed'
                        WHERE id=(SELECT reservation_id FROM rentals WHERE id=?)
                          AND status='converted'""", (rental_id,))
        next_res = conn.execute(
            "SELECT COUNT(*) FROM reservations WHERE vehicle_id=? AND status='pending'", (vid,)
        ).fetchone()[0]
        conn.execute("UPDATE vehicles SET status=? WHERE id=?",
                     ("reserved" if next_res > 0 else "available", vid))
        conn.commit()
        return True, "Renta completada. Vehículo disponible."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
