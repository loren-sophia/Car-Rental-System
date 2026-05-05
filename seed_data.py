"""
Run this script once to populate the database with sample data for demonstration.
Usage: python seed_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import initialize_db
from database.vehicle_queries import add_vehicle
from database.customer_queries import add_customer
from database.rental_queries import add_reservation, start_rental

initialize_db()

# Vehicles
vehicles = [
    ("Toyota",    "Camry",      2022, "Sedan",       55.00),
    ("Honda",     "CR-V",       2023, "SUV",         70.00),
    ("Ford",      "F-150",      2021, "Pickup",      85.00),
    ("Chevrolet", "Suburban",   2022, "Van",         95.00),
    ("BMW",       "3 Series",   2023, "Sedan",      110.00),
    ("Jeep",      "Wrangler",   2021, "SUV",         80.00),
    ("Mercedes",  "Sprinter",   2022, "Van",        120.00),
    ("Mazda",     "MX-5 Miata", 2023, "Convertible", 90.00),
    ("Honda",     "Civic",      2022, "Hatchback",   50.00),
    ("Toyota",    "Tacoma",     2021, "Pickup",      75.00),
]
for brand, model, year, vtype, rate in vehicles:
    ok, msg = add_vehicle(brand, model, year, vtype, rate)
    print(f"Vehicle: {msg}")

# Customers
customers = [
    ("Juan Pérez",      "809-555-0101", "juan@email.com",   "DR-001234"),
    ("María García",    "809-555-0202", "maria@email.com",  "DR-002345"),
    ("Carlos López",    "809-555-0303", "carlos@email.com", "DR-003456"),
    ("Ana Martínez",    "809-555-0404", "ana@email.com",    "DR-004567"),
    ("Pedro Rodríguez", "809-555-0505", "",                 "DR-005678"),
]
for name, phone, email, lic in customers:
    ok, msg = add_customer(name, phone, email, lic)
    print(f"Customer: {msg}")

# A reservation
ok, msg = add_reservation(1, 2, "2026-05-10", "2026-05-15")
print(f"Reservation: {msg}")

# A completed rental
ok, msg = start_rental(2, 3, "2026-04-01", "2026-04-05", 85.00)
print(f"Rental: {msg}")

print("\n✅ Sample data loaded successfully!")
