from database.db import get_connection


def get_all_customers(search=None):
    conn = get_connection()
    query = "SELECT * FROM customers WHERE 1=1"
    params = []
    if search:
        query += " AND (full_name LIKE ? OR phone LIKE ? OR email LIKE ? OR license_number LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_customer_by_id(customer_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_customer(full_name, phone, email, license_number):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO customers (full_name, phone, email, license_number) VALUES (?,?,?,?)",
            (full_name, phone, email, license_number)
        )
        conn.commit()
        return True, "Customer added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_customer(customer_id, full_name, phone, email, license_number):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE customers SET full_name=?, phone=?, email=?, license_number=? WHERE id=?",
            (full_name, phone, email, license_number, customer_id)
        )
        conn.commit()
        return True, "Customer updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def delete_customer(customer_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
        return True, "Customer deleted."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
