from database.db import get_connection
from datetime import datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_vehicle_conflict(vehicle_id, start_date, end_date, exclude_id=None, table="reservations"):
    """
    Returns True if the vehicle has an overlapping booking in the given table.
    Overlap formula: NOT (end_date < start OR start_date > end)
    """
    conn = get_connection()
    query = f"""
        SELECT COUNT(*) FROM {table}
        WHERE vehicle_id = ?
          AND status NOT IN ('cancelled', 'completed', 'converted')
          AND NOT (end_date < ? OR start_date > ?)
    """
    params = [vehicle_id, start_date, end_date]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)
    count = conn.execute(query, params).fetchone()[0]
    conn.close()
    return count > 0


def _calc_days(start_date: str, end_date: str) -> int:
    return (datetime.strptime(end_date, "%Y-%m-%d") -
            datetime.strptime(start_date, "%Y-%m-%d")).days


# ── RESERVATIONS ──────────────────────────────────────────────────────────────

def get_all_reservations(filters=None):
    conn = get_connection()
    query = """
        SELECT res.id,
               c.full_name   AS customer_name,
               v.brand || ' ' || v.model AS vehicle,
               res.start_date, res.end_date, res.status,
               res.customer_id, res.vehicle_id
        FROM reservations res
        JOIN customers c ON res.customer_id = c.id
        JOIN vehicles  v ON res.vehicle_id  = v.id
        WHERE 1=1
    """
    params = []
    if filters:
        if filters.get("status"):
            query += " AND res.status = ?"
            params.append(filters["status"])
        if filters.get("customer_id"):
            query += " AND res.customer_id = ?"
            params.append(filters["customer_id"])
    query += " ORDER BY res.start_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_reservation(customer_id, vehicle_id, start_date, end_date):
    if check_vehicle_conflict(vehicle_id, start_date, end_date):
        return False, "El vehiculo ya tiene una reserva activa en esas fechas."
    if check_vehicle_conflict(vehicle_id, start_date, end_date, table="rentals"):
        return False, "El vehiculo ya esta rentado en esas fechas."
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO reservations (customer_id, vehicle_id, start_date, end_date, status) "
            "VALUES (?,?,?,?,'pending')",
            (customer_id, vehicle_id, start_date, end_date)
        )
        conn.execute("UPDATE vehicles SET status='reserved' WHERE id=?", (vehicle_id,))
        conn.commit()
        return True, "Reserva creada exitosamente."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def cancel_reservation(reservation_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT vehicle_id FROM reservations WHERE id=?", (reservation_id,)
        ).fetchone()
        if not row:
            return False, "Reserva no encontrada."
        vehicle_id = row["vehicle_id"]
        conn.execute("UPDATE reservations SET status='cancelled' WHERE id=?", (reservation_id,))
        other = conn.execute(
            "SELECT COUNT(*) FROM reservations "
            "WHERE vehicle_id=? AND status='pending' AND id!=?",
            (vehicle_id, reservation_id)
        ).fetchone()[0]
        if other == 0:
            conn.execute("UPDATE vehicles SET status='available' WHERE id=?", (vehicle_id,))
        conn.commit()
        return True, "Reserva cancelada."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ── RENTALS ───────────────────────────────────────────────────────────────────

def get_all_rentals(filters=None):
    conn = get_connection()
    query = "SELECT * FROM rental_summary WHERE 1=1"
    params = []
    if filters and filters.get("status"):
        query += " AND rental_status = ?"
        params.append(filters["status"])
    query += " ORDER BY start_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def calculate_rental_cost(vehicle_id, start_date, end_date):
    """
    Pure cost calculation - does NOT write to DB.
    Returns (ok, days, total_cost, message)
    """
    days = _calc_days(start_date, end_date)
    if days <= 0:
        return False, 0, 0.0, "La fecha de fin debe ser posterior a la de inicio."
    conn = get_connection()
    row = conn.execute("SELECT rate_per_day FROM vehicles WHERE id=?", (vehicle_id,)).fetchone()
    conn.close()
    if not row:
        return False, 0, 0.0, "Vehiculo no encontrado."
    total = days * row["rate_per_day"]
    return True, days, total, f"{days} dia(s) x ${row['rate_per_day']:.2f}/dia = ${total:.2f}"


def start_rental(customer_id, vehicle_id, start_date, end_date, rate_per_day):
    """
    Creates a rental. Auto-converts any overlapping pending reservation
    for the same vehicle, marking it as 'converted'.
    Returns (ok, message, converted_reservation_id | None)
    """
    if check_vehicle_conflict(vehicle_id, start_date, end_date, table="rentals"):
        return False, "El vehiculo ya tiene una renta activa en esas fechas.", None

    days = _calc_days(start_date, end_date)
    if days <= 0:
        return False, "La fecha de fin debe ser posterior a la de inicio.", None

    total_cost = days * rate_per_day
    converted_res_id = None

    conn = get_connection()
    try:
        # Auto-detect and convert overlapping reservation
        existing_res = conn.execute("""
            SELECT * FROM reservations
            WHERE vehicle_id = ?
              AND status = 'pending'
              AND NOT (end_date < ? OR start_date > ?)
            ORDER BY start_date ASC
            LIMIT 1
        """, (vehicle_id, start_date, end_date)).fetchone()

        if existing_res:
            converted_res_id = existing_res["id"]
            conn.execute(
                "UPDATE reservations SET status='converted' WHERE id=?",
                (converted_res_id,)
            )

        conn.execute(
            "INSERT INTO rentals "
            "(customer_id, vehicle_id, start_date, end_date, total_cost, status, reservation_id) "
            "VALUES (?,?,?,?,?,'active',?)",
            (customer_id, vehicle_id, start_date, end_date, total_cost, converted_res_id)
        )
        conn.execute("UPDATE vehicles SET status='rented' WHERE id=?", (vehicle_id,))
        conn.commit()

        msg = f"Renta iniciada. Costo total: ${total_cost:.2f}"
        if converted_res_id:
            msg += f"\nReserva #{converted_res_id} convertida automaticamente."
        return True, msg, converted_res_id

    except Exception as e:
        return False, str(e), None
    finally:
        conn.close()


def complete_rental(rental_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT vehicle_id FROM rentals WHERE id=?", (rental_id,)).fetchone()
        if not row:
            return False, "Renta no encontrada."
        vehicle_id = row["vehicle_id"]
        conn.execute("UPDATE rentals SET status='completed' WHERE id=?", (rental_id,))
        next_res = conn.execute(
            "SELECT COUNT(*) FROM reservations WHERE vehicle_id=? AND status='pending'",
            (vehicle_id,)
        ).fetchone()[0]
        new_status = "reserved" if next_res > 0 else "available"
        conn.execute("UPDATE vehicles SET status=? WHERE id=?", (new_status, vehicle_id))
        conn.commit()
        return True, "Renta completada. Vehiculo disponible."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
