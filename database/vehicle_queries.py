from database.db import get_connection


def get_all_vehicles(filters=None):
    conn = get_connection()
    q = "SELECT * FROM vehicles WHERE 1=1"
    p = []
    if filters:
        if filters.get("brand"):
            q += " AND brand LIKE ?"; p.append(f"%{filters['brand']}%")
        if filters.get("vehicle_type"):
            q += " AND vehicle_type = ?"; p.append(filters["vehicle_type"])
        if filters.get("status"):
            q += " AND status = ?"; p.append(filters["status"])
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_vehicle_by_id(vid):
    conn = get_connection()
    r = conn.execute("SELECT * FROM vehicles WHERE id=?", (vid,)).fetchone()
    conn.close()
    return dict(r) if r else None


def add_vehicle(brand, model, year, vehicle_type, rate_per_day, status="available"):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO vehicles (brand,model,year,vehicle_type,rate_per_day,status) VALUES(?,?,?,?,?,?)",
            (brand, model, year, vehicle_type, rate_per_day, status))
        conn.commit()
        return True, "Vehículo agregado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_vehicle(vid, brand, model, year, vehicle_type, rate_per_day, status):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE vehicles SET brand=?,model=?,year=?,vehicle_type=?,rate_per_day=?,status=? WHERE id=?",
            (brand, model, year, vehicle_type, rate_per_day, status, vid))
        conn.commit()
        return True, "Vehículo actualizado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def delete_vehicle(vid):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM vehicles WHERE id=?", (vid,))
        conn.commit()
        return True, "Vehículo eliminado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_available_vehicles():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM available_vehicles").fetchall()
    conn.close()
    return [dict(r) for r in rows]
