"""
DatePicker widget for Tkinter — zero external dependencies.
Compatible with Python 3.8+ including 3.14.

Usage:
    picker = DatePickerButton(parent, initial_date="2026-05-10")
    picker.pack()
    date_str = picker.get()          # "YYYY-MM-DD"
    picker.set("2026-06-01")         # programmatic set
    picker.on_change = my_callback   # called whenever date changes
"""

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import date, timedelta


# ── Palette ───────────────────────────────────────────────────────────────────
C_BG        = "#ffffff"
C_HEADER    = "#1a1a2e"
C_HEADER_FG = "#ffffff"
C_TODAY     = "#4a90d9"
C_SEL       = "#27ae60"
C_SEL_FG    = "#ffffff"
C_WEEKEND   = "#e74c3c"
C_HOVER     = "#eaf4ff"
C_BTN_FG    = "#1a1a2e"
C_DISABLED  = "#cccccc"
C_BORDER    = "#dddddd"


class DatePickerPopup(tk.Toplevel):
    """
    Floating calendar popup.  Calls on_select(date_obj) when a day is chosen.
    """
    def __init__(self, parent, initial: date, on_select, min_date=None, max_date=None):
        super().__init__(parent)
        self.overrideredirect(True)          # borderless window
        self.resizable(False, False)
        self.configure(bg=C_BORDER)
        self.on_select  = on_select
        self.min_date   = min_date
        self.max_date   = max_date
        self._current   = date(initial.year, initial.month, 1)
        self._selected  = initial
        self._day_btns  = {}

        self._build()
        self._render_days()
        self._position(parent)

        # Close on click outside
        self.bind("<FocusOut>", self._on_focus_out)
        self.focus_set()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        outer = tk.Frame(self, bg=C_BORDER, padx=1, pady=1)
        outer.pack()
        inner = tk.Frame(outer, bg=C_BG)
        inner.pack()

        # ── Header: prev  Month Year  next ────────────────────────────────────
        hdr = tk.Frame(inner, bg=C_HEADER, padx=6, pady=6)
        hdr.pack(fill="x")

        tk.Button(hdr, text="◀", bg=C_HEADER, fg=C_HEADER_FG,
                  relief="flat", bd=0, font=("Helvetica", 11, "bold"),
                  activebackground="#16213e", activeforeground="white",
                  cursor="hand2", command=self._prev_month).pack(side="left")

        self._month_label = tk.Label(hdr, text="", bg=C_HEADER, fg=C_HEADER_FG,
                                     font=("Helvetica", 11, "bold"), width=16)
        self._month_label.pack(side="left", expand=True)
        self._month_label.bind("<Button-1>", self._open_month_year_selector)

        tk.Button(hdr, text="▶", bg=C_HEADER, fg=C_HEADER_FG,
                  relief="flat", bd=0, font=("Helvetica", 11, "bold"),
                  activebackground="#16213e", activeforeground="white",
                  cursor="hand2", command=self._next_month).pack(side="right")

        # ── Day-of-week row ───────────────────────────────────────────────────
        dow_frame = tk.Frame(inner, bg=C_BG)
        dow_frame.pack(fill="x", padx=6, pady=(4, 0))
        for i, d in enumerate(["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]):
            color = C_WEEKEND if i >= 5 else "#555555"
            tk.Label(dow_frame, text=d, width=3, font=("Helvetica", 9, "bold"),
                     bg=C_BG, fg=color).grid(row=0, column=i, padx=1)

        # ── Day grid ──────────────────────────────────────────────────────────
        self._grid_frame = tk.Frame(inner, bg=C_BG)
        self._grid_frame.pack(padx=6, pady=4)

        # ── Footer: Today button ──────────────────────────────────────────────
        footer = tk.Frame(inner, bg=C_BG, pady=4)
        footer.pack(fill="x")
        tk.Button(footer, text="Hoy", font=("Helvetica", 9),
                  bg=C_TODAY, fg="white", relief="flat", padx=8,
                  cursor="hand2", command=self._go_today).pack()

    def _render_days(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()
        self._day_btns.clear()

        yr, mo = self._current.year, self._current.month
        self._month_label.config(
            text=f"{calendar.month_name[mo]} {yr}"
        )

        today = date.today()
        first_weekday, num_days = calendar.monthrange(yr, mo)
        # Monday=0 in calendar; we want Monday as first column
        col = first_weekday  # 0=Mon … 6=Sun
        row = 0

        for day in range(1, num_days + 1):
            d = date(yr, mo, day)
            is_today    = (d == today)
            is_selected = (d == self._selected)
            is_weekend  = (col >= 5)
            disabled    = False
            if self.min_date and d < self.min_date:
                disabled = True
            if self.max_date and d > self.max_date:
                disabled = True

            if is_selected:
                bg, fg = C_SEL, C_SEL_FG
            elif is_today:
                bg, fg = C_TODAY, "white"
            elif disabled:
                bg, fg = C_BG, C_DISABLED
            elif is_weekend:
                bg, fg = C_BG, C_WEEKEND
            else:
                bg, fg = C_BG, C_BTN_FG

            btn = tk.Button(
                self._grid_frame, text=str(day),
                width=3, font=("Helvetica", 9),
                bg=bg, fg=fg, relief="flat", bd=0,
                activebackground=C_HOVER,
                cursor="hand2" if not disabled else "arrow",
                state="normal" if not disabled else "disabled",
                command=(lambda _d=d: self._select(_d)) if not disabled else None
            )
            btn.grid(row=row, column=col, padx=1, pady=1)
            self._day_btns[day] = btn

            col += 1
            if col > 6:
                col = 0
                row += 1

    # ── Navigation ────────────────────────────────────────────────────────────

    def _prev_month(self):
        yr, mo = self._current.year, self._current.month
        mo -= 1
        if mo < 1:
            mo, yr = 12, yr - 1
        self._current = date(yr, mo, 1)
        self._render_days()

    def _next_month(self):
        yr, mo = self._current.year, self._current.month
        mo += 1
        if mo > 12:
            mo, yr = 1, yr + 1
        self._current = date(yr, mo, 1)
        self._render_days()

    def _go_today(self):
        t = date.today()
        self._current  = date(t.year, t.month, 1)
        self._selected = t
        self._render_days()
        self._select(t)

    def _open_month_year_selector(self, event=None):
        MonthYearSelector(self, self._current, self._on_month_year_chosen)

    def _on_month_year_chosen(self, yr, mo):
        self._current = date(yr, mo, 1)
        self._render_days()

    def _select(self, d: date):
        self._selected = d
        self._render_days()
        self.on_select(d)
        self.destroy()

    # ── Positioning ───────────────────────────────────────────────────────────

    def _position(self, parent):
        self.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty() + parent.winfo_height() + 2
        sw = parent.winfo_screenwidth()
        pw = self.winfo_reqwidth()
        # Don't go off screen right
        x = min(px, sw - pw - 4)
        self.geometry(f"+{x}+{py}")

    def _on_focus_out(self, event):
        # Small delay so clicks inside popup register first
        self.after(150, self._check_focus)

    def _check_focus(self):
        try:
            if self.focus_get() is None:
                self.destroy()
        except Exception:
            self.destroy()


class MonthYearSelector(tk.Toplevel):
    """Quick month/year picker accessible from the calendar header."""

    def __init__(self, parent, current: date, callback):
        super().__init__(parent)
        self.title("Ir a…")
        self.resizable(False, False)
        self.configure(bg="#f0f2f5")
        self.callback = callback
        self.grab_set()

        MONTHS = [calendar.month_name[m] for m in range(1, 13)]
        years  = list(range(date.today().year - 5, date.today().year + 10))

        frame = tk.Frame(self, bg="#f0f2f5", padx=16, pady=12)
        frame.pack()

        tk.Label(frame, text="Mes:", bg="#f0f2f5").grid(row=0, column=0, sticky="w")
        self.month_cb = ttk.Combobox(frame, values=MONTHS, state="readonly", width=14)
        self.month_cb.set(MONTHS[current.month - 1])
        self.month_cb.grid(row=0, column=1, padx=6, pady=4)

        tk.Label(frame, text="Año:", bg="#f0f2f5").grid(row=1, column=0, sticky="w")
        self.year_cb = ttk.Combobox(frame, values=years, state="readonly", width=14)
        self.year_cb.set(current.year)
        self.year_cb.grid(row=1, column=1, padx=6, pady=4)

        tk.Button(frame, text="Ir", command=self._go,
                  bg="#4a90d9", fg="white", relief="flat",
                  padx=10, pady=4, cursor="hand2").grid(
            row=2, column=0, columnspan=2, pady=8)

    def _go(self):
        MONTHS = [calendar.month_name[m] for m in range(1, 13)]
        mo = MONTHS.index(self.month_cb.get()) + 1
        yr = int(self.year_cb.get())
        self.callback(yr, mo)
        self.destroy()


# ── Public widget ─────────────────────────────────────────────────────────────

class DatePickerButton(tk.Frame):
    """
    Drop-in replacement for tk.Entry when entering dates.

    Shows a button with the current date and opens a popup calendar.

    Parameters
    ----------
    parent      : tk parent widget
    initial_date: "YYYY-MM-DD" string (defaults to today)
    min_date    : "YYYY-MM-DD" minimum selectable date (optional)
    label_width : width of the date label inside the button
    on_change   : callable(date_str) — fired on every selection
    """

    def __init__(self, parent, initial_date: str = None,
                 min_date: str = None, label_width: int = 12,
                 on_change=None, **kwargs):
        super().__init__(parent, bg=parent.cget("bg"), **kwargs)

        self._min  = date.fromisoformat(min_date) if min_date else None
        self._date = date.fromisoformat(initial_date) if initial_date else date.today()
        self.on_change = on_change

        self._var = tk.StringVar(value=self._fmt())
        self._popup = None

        btn = tk.Button(
            self, textvariable=self._var,
            font=("Helvetica", 10), width=label_width,
            bg="white", fg="#1a1a2e",
            relief="solid", bd=1,
            activebackground=C_HOVER,
            cursor="hand2",
            command=self._open
        )
        btn.pack(side="left")

        cal_btn = tk.Button(
            self, text="📅",
            font=("Helvetica", 10),
            bg="white", fg="#4a90d9",
            relief="solid", bd=1,
            activebackground=C_HOVER,
            cursor="hand2",
            command=self._open
        )
        cal_btn.pack(side="left")

    def _fmt(self) -> str:
        return self._date.strftime("%d/%m/%Y")

    def _open(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            return
        self._popup = DatePickerPopup(
            self, self._date, self._on_select,
            min_date=self._min
        )

    def _on_select(self, d: date):
        self._date = d
        self._var.set(self._fmt())
        if self.on_change:
            self.on_change(self.get())

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self) -> str:
        """Returns selected date as 'YYYY-MM-DD'."""
        return self._date.strftime("%Y-%m-%d")

    def set(self, date_str: str):
        """Programmatically set the date ('YYYY-MM-DD')."""
        self._date = date.fromisoformat(date_str)
        self._var.set(self._fmt())

    def set_min_date(self, date_str: str):
        self._min = date.fromisoformat(date_str)
