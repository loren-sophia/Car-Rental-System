# 🚗 Car Rental Management System

A GUI desktop application for managing vehicle rentals, built with **Python 3**, **Tkinter**, and **SQLite**.

---

## 📁 Project Structure

```
car_rental/
├── main.py                        # Entry point
├── seed_data.py                   # Sample data loader
├── database/
│   ├── db.py                      # Connection, schema, VIEWs
│   ├── vehicle_queries.py
│   ├── customer_queries.py
│   ├── rental_queries.py          # Reservations + Rentals + conflict check
│   └── report_queries.py
├── views/
│   ├── dashboard_view.py
│   ├── vehicles_view.py
│   ├── customers_view.py
│   ├── reservations_view.py
│   ├── rentals_view.py
│   └── reports_view.py
└── utils/
    └── validators.py
```

---

## ▶️ How to Run

### Requirements
- Python 3.8+
- No external packages needed (Tkinter and SQLite are included with Python)

### Steps

```bash
# 1. Navigate to the project folder
cd Car-Rental-System-main

# 2. (Optional) Load sample data
python seed_data.py

# 3. Launch the application
python main.py
```

---

## ✅ Features

| Feature | Details |
|---|---|
| Dashboard | Summary cards: vehicles, rentals, reservations, revenue |
| Vehicles | Add, edit, delete, search by brand/type/status |
| Customers | Add, edit, delete, search by name/phone/email/license |
| Reservations | Create, cancel, filter by status. Conflict detection built in. |
| Rentals | Start rental with cost preview, complete rental, CASE-based late detection |
| Reports | Fleet status, revenue by month, top customers |

---

## 🗄️ SQL Features Used

- `CREATE TABLE` with constraints (`NOT NULL`, `CHECK`, `UNIQUE`, `REFERENCES`)
- `CREATE VIEW` — `available_vehicles` and `rental_summary`
- `CASE` expression — classifies rentals as active, late, or completed
- `SELECT`, `INSERT`, `UPDATE`, `DELETE`
- `JOIN` across customers, vehicles, reservations, rentals
- `GROUP BY` with `COUNT` and `SUM` for reports
- Conflict detection with date overlap query

---

## 🔒 Business Logic

- A vehicle cannot be double-booked for overlapping dates
- Vehicle status updates automatically on reservation/rental/completion
- Total rental cost is calculated from rate × days
- Late rentals are detected via CASE in the `rental_summary` VIEW

---
