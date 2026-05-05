import tkinter as tk
from tkinter import ttk
import sys
import os

# Make sure imports resolve from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import initialize_db
from views.dashboard_view import DashboardView
from views.vehicles_view import VehiclesView
from views.customers_view import CustomersView
from views.reservations_view import ReservationsView
from views.rentals_view import RentalsView
from views.reports_view import ReportsView


class CarRentalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚗 Car Rental Management System")
        self.geometry("1100x680")
        self.minsize(900, 580)
        self.configure(bg="#1a1a2e")

        initialize_db()
        self._build_ui()

    def _build_ui(self):
        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = tk.Frame(self, bg="#1a1a2e", width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo area
        tk.Label(sidebar, text="🚗", font=("Helvetica", 32), bg="#1a1a2e",
                 fg="white").pack(pady=(24, 2))
        tk.Label(sidebar, text="Car Rental", font=("Helvetica", 13, "bold"),
                 bg="#1a1a2e", fg="white").pack()
        tk.Label(sidebar, text="Management System", font=("Helvetica", 9),
                 bg="#1a1a2e", fg="#aaaacc").pack(pady=(0, 20))

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=16, pady=4)

        # Nav buttons
        self.nav_buttons = {}
        nav_items = [
            ("Dashboard",     "🏠"),
            ("Vehicles",      "🚙"),
            ("Customers",     "👥"),
            ("Reservations",  "📅"),
            ("Rentals",       "🔑"),
            ("Reports",       "📊"),
        ]

        for name, icon in nav_items:
            btn = tk.Button(
                sidebar, text=f"  {icon}  {name}",
                font=("Helvetica", 11), anchor="w",
                bg="#1a1a2e", fg="#ccccee",
                activebackground="#16213e", activeforeground="white",
                relief="flat", bd=0, padx=14, pady=10,
                cursor="hand2",
                command=lambda n=name: self.show_view(n)
            )
            btn.pack(fill="x", pady=1)
            self.nav_buttons[name] = btn

        # ── Main content area ─────────────────────────────────────────────────
        self.content = tk.Frame(self, bg="#f0f2f5")
        self.content.pack(side="right", fill="both", expand=True)

        # Pre-load all views
        self.views = {
            "Dashboard":    DashboardView(self.content),
            "Vehicles":     VehiclesView(self.content),
            "Customers":    CustomersView(self.content),
            "Reservations": ReservationsView(self.content),
            "Rentals":      RentalsView(self.content),
            "Reports":      ReportsView(self.content),
        }

        for view in self.views.values():
            view.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_view("Dashboard")

    def show_view(self, name):
        # Highlight active nav button
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                btn.config(bg="#16213e", fg="white",
                           font=("Helvetica", 11, "bold"))
            else:
                btn.config(bg="#1a1a2e", fg="#ccccee",
                           font=("Helvetica", 11))

        # Raise the selected view
        self.views[name].lift()

        # Refresh on switch
        view = self.views[name]
        if hasattr(view, "refresh"):
            view.refresh()
        elif hasattr(view, "load_vehicles"):
            view.load_vehicles()
        elif hasattr(view, "load_customers"):
            view.load_customers()
        elif hasattr(view, "load_reservations"):
            view.load_reservations()
        elif hasattr(view, "load_rentals"):
            view.load_rentals()


if __name__ == "__main__":
    app = CarRentalApp()
    app.mainloop()
