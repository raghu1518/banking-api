from datetime import date
from secrets import randbelow


def generate_account_number() -> str:
    return f"{randbelow(10**12):012d}"


def generate_card_number() -> str:
    prefix = "521234"
    suffix = f"{randbelow(10**9):09d}"
    return f"{prefix}{suffix}"


def generate_transaction_reference() -> str:
    return f"TXN{randbelow(10**12):012d}"


def generate_otp() -> str:
    return f"{randbelow(10**6):06d}"


def calculate_maturity_date(start: date, term_months: int) -> date:
    year = start.year + ((start.month - 1 + term_months) // 12)
    month = ((start.month - 1 + term_months) % 12) + 1
    day = min(start.day, 28)
    return date(year, month, day)
