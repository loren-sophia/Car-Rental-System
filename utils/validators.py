import re
from datetime import datetime


def validate_not_empty(*fields):
    for name, value in fields:
        if not value or not str(value).strip():
            return False, f"'{name}' is required."
    return True, ""


def validate_year(year_str):
    try:
        y = int(year_str)
        if y < 1900 or y > datetime.now().year + 1:
            return False, "Invalid year."
        return True, y
    except ValueError:
        return False, "Year must be a number."


def validate_rate(rate_str):
    try:
        r = float(rate_str)
        if r <= 0:
            return False, "Rate must be greater than 0."
        return True, r
    except ValueError:
        return False, "Rate must be a number."


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True, date_str
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format."


def validate_date_range(start_str, end_str):
    ok1, s = validate_date(start_str)
    if not ok1:
        return False, "Start date: " + s
    ok2, e = validate_date(end_str)
    if not ok2:
        return False, "End date: " + e
    if datetime.strptime(end_str, "%Y-%m-%d") <= datetime.strptime(start_str, "%Y-%m-%d"):
        return False, "End date must be after start date."
    return True, ""


def validate_email(email):
    if not email:
        return True, ""  # optional
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    if not re.match(pattern, email):
        return False, "Invalid email format."
    return True, ""


def today_str():
    return datetime.now().strftime("%Y-%m-%d")
