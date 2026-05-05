from database.db import get_connection


def get_dashboard_stats():
    conn = get_connection()
    stats = {}
    stats["total_vehicles"] = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    stats["available_vehicles"] = conn.execute("SELECT COUNT(*) FROM vehicles WHERE status='available'").fetchone()[0]
    stats["rented_vehicles"] = conn.execute("SELECT COUNT(*) FROM vehicles WHERE status='rented'").fetchone()[0]
    stats["reserved_vehicles"] = conn.execute("SELECT COUNT(*) FROM vehicles WHERE status='reserved'").fetchone()[0]
    stats["maintenance_vehicles"] = conn.execute("SELECT COUNT(*) FROM vehicles WHERE status='maintenance'").fetchone()[0]
    stats["total_customers"] = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    stats["active_rentals"] = conn.execute("SELECT COUNT(*) FROM rentals WHERE status='active'").fetchone()[0]
    stats["pending_reservations"] = conn.execute("SELECT COUNT(*) FROM reservations WHERE status='pending'").fetchone()[0]
    stats["total_revenue"] = conn.execute("SELECT COALESCE(SUM(total_cost),0) FROM rentals WHERE status='completed'").fetchone()[0]
    conn.close()
    return stats


def get_vehicles_by_status():
    conn = get_connection()
    rows = conn.execute(
        "SELECT status, COUNT(*) as count FROM vehicles GROUP BY status"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_rentals_by_month():
    conn = get_connection()
    rows = conn.execute("""
        SELECT strftime('%Y-%m', start_date) AS month,
               COUNT(*) AS total_rentals,
               COALESCE(SUM(total_cost), 0) AS revenue
        FROM rentals
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_top_customers():
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.full_name, COUNT(r.id) AS total_rentals,
               COALESCE(SUM(r.total_cost), 0) AS total_spent
        FROM customers c
        LEFT JOIN rentals r ON c.id = r.customer_id
        GROUP BY c.id
        ORDER BY total_rentals DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
