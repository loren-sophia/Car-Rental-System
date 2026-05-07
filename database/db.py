import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "car_rental.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL CHECK(year >= 1900),
            vehicle_type TEXT NOT NULL CHECK(vehicle_type IN
                ('Sedan','SUV','Pickup','Van','Convertible','Hatchback')),
            rate_per_day REAL NOT NULL CHECK(rate_per_day > 0),
            status TEXT NOT NULL DEFAULT 'available'
                CHECK(status IN ('available','reserved','rented','maintenance'))
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            license_number TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            vehicle_id  INTEGER NOT NULL REFERENCES vehicles(id),
            start_date  TEXT NOT NULL,
            end_date    TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending','completed','cancelled','converted'))
        );

        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id    INTEGER NOT NULL REFERENCES customers(id),
            vehicle_id     INTEGER NOT NULL REFERENCES vehicles(id),
            start_date     TEXT NOT NULL,
            end_date       TEXT NOT NULL,
            total_cost     REAL,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active','completed','late')),
            reservation_id INTEGER REFERENCES reservations(id)
        );

        CREATE TABLE IF NOT EXISTS maintenance (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id       INTEGER NOT NULL REFERENCES vehicles(id),
            description      TEXT NOT NULL,
            maintenance_date TEXT NOT NULL
        );

        CREATE VIEW IF NOT EXISTS available_vehicles AS
            SELECT id, brand, model, year, vehicle_type, rate_per_day
            FROM vehicles WHERE status = 'available';

        CREATE VIEW IF NOT EXISTS rental_summary AS
            SELECT
                r.id,
                c.full_name AS customer_name,
                v.brand || ' ' || v.model AS vehicle,
                r.start_date, r.end_date, r.total_cost,
                r.reservation_id,
                CASE
                    WHEN r.status = 'active' AND date(r.end_date) < date('now') THEN 'late'
                    WHEN r.status = 'active'    THEN 'active'
                    WHEN r.status = 'completed' THEN 'completed'
                    ELSE r.status
                END AS rental_status
            FROM rentals r
            JOIN customers c ON r.customer_id = c.id
            JOIN vehicles  v ON r.vehicle_id  = v.id;
    """)
    conn.commit()
    # Migration for existing DBs
    try:
        conn.execute("ALTER TABLE rentals ADD COLUMN reservation_id INTEGER REFERENCES reservations(id)")
        conn.commit()
    except Exception:
        pass
    conn.close()
