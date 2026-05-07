from database.db import get_connection


def get_all_customers(search=None):
    conn = get_connection()
    q = "SELECT * FROM customers WHERE 1=1"
    p = []
    if search:
        q += " AND (full_name LIKE ? OR phone LIKE ? OR email LIKE ? OR license_number LIKE ?)"
        s = f"%{search}%"; p.extend([s, s, s, s])
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_customer_by_id(cid):
    conn = get_connection()
    r = conn.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()
    conn.close()
    return dict(r) if r else None


def add_customer(full_name, phone, email, license_number):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO customers (full_name,phone,email,license_number) VALUES(?,?,?,?)",
            (full_name, phone, email, license_number))
        conn.commit()
        return True, "Cliente agregado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_customer(cid, full_name, phone, email, license_number):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE customers SET full_name=?,phone=?,email=?,license_number=? WHERE id=?",
            (full_name, phone, email, license_number, cid))
        conn.commit()
        return True, "Cliente actualizado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def delete_customer(cid):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM customers WHERE id=?", (cid,))
        conn.commit()
        return True, "Cliente eliminado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
