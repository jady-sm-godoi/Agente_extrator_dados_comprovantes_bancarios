import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


def parse_brazilian_decimal(value: str) -> Decimal:
    cleaned = value.strip()
    cleaned = cleaned.replace("R$", "").replace("r$", "").strip()
    cleaned = cleaned.replace(".", "").replace(",", ".")
    cleaned = re.sub(r"[^\d.,-]", "", cleaned)
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"Invalid Brazilian decimal format: {value!r}")


def parse_brazilian_date(value: str) -> date:
    cleaned = value.strip()
    formats = [
        ("%d/%m/%Y", r"\d{2}/\d{2}/\d{4}"),
        ("%Y-%m-%d", r"\d{4}-\d{2}-\d{2}"),
        ("%d/%m/%y", r"\d{2}/\d{2}/\d{2}"),
    ]
    for fmt, pattern in formats:
        if re.fullmatch(pattern, cleaned):
            try:
                return datetime.strptime(cleaned, fmt).date()  # noqa: DTZ007
            except ValueError:
                raise ValueError(f"Invalid date: {value!r}")
    raise ValueError(f"Unrecognized date format: {value!r}")


def detect_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in {".png", ".jpg", ".jpeg", ".jfif"}:
        return "image"
    return "unknown"


def format_error(message: str) -> dict:
    return {"erro": message}
