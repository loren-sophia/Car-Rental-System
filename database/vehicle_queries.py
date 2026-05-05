from database.db import get_connection


def get_all_vehicles(filters=None):
    conn = get_connection()
    query = "SELECT * FROM vehicles WHERE 1=1"
    params = []
    if filters:
        if filters.get("brand"):
            query += " AND brand LIKE ?"
            params.append(f"%{filters['brand']}%")
        if filters.get("vehicle_type"):
            query += " AND vehicle_type = ?"
            params.append(filters["vehicle_type"])
        if filters.get("status"):
            query += " AND status = ?"
            params.append(filters["status"])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_vehicle_by_id(vehicle_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_vehicle(brand, model, year, vehicle_type, rate_per_day, status="available"):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO vehicles (brand, model, year, vehicle_type, rate_per_day, status) VALUES (?,?,?,?,?,?)",
            (brand, model, year, vehicle_type, rate_per_day, status)
        )
        conn.commit()
        return True, "Vehicle added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_vehicle(vehicle_id, brand, model, year, vehicle_type, rate_per_day, status):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE vehicles SET brand=?, model=?, year=?, vehicle_type=?, rate_per_day=?, status=? WHERE id=?",
            (brand, model, year, vehicle_type, rate_per_day, status, vehicle_id)
        )
        conn.commit()
        return True, "Vehicle updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def delete_vehicle(vehicle_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
        conn.commit()
        return True, "Vehicle deleted."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_vehicle_status(vehicle_id, status):
    conn = get_connection()
    try:
        conn.execute("UPDATE vehicles SET status=? WHERE id=?", (status, vehicle_id))
        conn.commit()
        return True, "Status updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_available_vehicles():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM available_vehicles").fetchall()
    conn.close()
    return [dict(r) for r in rows]
