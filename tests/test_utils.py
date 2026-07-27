from datetime import date
from decimal import Decimal

import pytest

from bank_receipt_extractor.utils import (
    detect_file_type,
    format_error,
    parse_brazilian_date,
    parse_brazilian_decimal,
)


class TestParseBrazilianDecimal:
    def test_thousands_with_cents(self):
        assert parse_brazilian_decimal("1.234,56") == Decimal("1234.56")

    def test_with_r_symbol(self):
        assert parse_brazilian_decimal("R$ 1.234,56") == Decimal("1234.56")

    def test_clean_without_symbol(self):
        assert parse_brazilian_decimal("R$ 1.000,00") == Decimal("1000.00")

    def test_no_cents(self):
        assert parse_brazilian_decimal("R$ 1.000") == Decimal(1000)

    def test_small_value(self):
        assert parse_brazilian_decimal("0,50") == Decimal("0.50")

    def test_integer_without_separator(self):
        assert parse_brazilian_decimal("1500") == Decimal(1500)

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError, match="Invalid Brazilian decimal"):
            parse_brazilian_decimal("abc")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_brazilian_decimal("")

    def test_trailing_spaces(self):
        assert parse_brazilian_decimal("  R$ 99,90  ") == Decimal("99.90")


class TestParseBrazilianDate:
    def test_dd_mm_yyyy(self):
        assert parse_brazilian_date("15/03/2024") == date(2024, 3, 15)

    def test_iso_format(self):
        assert parse_brazilian_date("2024-03-15") == date(2024, 3, 15)

    def test_dd_mm_yy(self):
        assert parse_brazilian_date("15/03/24") == date(2024, 3, 15)

    def test_first_day_of_year(self):
        assert parse_brazilian_date("01/01/2025") == date(2025, 1, 1)

    def test_last_day_of_year(self):
        assert parse_brazilian_date("31/12/2024") == date(2024, 12, 31)

    def test_invalid_day_raises(self):
        with pytest.raises(ValueError):
            parse_brazilian_date("32/01/2024")

    def test_invalid_month_raises(self):
        with pytest.raises(ValueError):
            parse_brazilian_date("01/13/2024")

    def test_garbage_string_raises(self):
        with pytest.raises(ValueError, match="Unrecognized date format"):
            parse_brazilian_date("not-a-date")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_brazilian_date("")

    def test_whitespace_around(self):
        assert parse_brazilian_date("  20/07/2024  ") == date(2024, 7, 20)


class TestDetectFileType:
    def test_pdf(self):
        assert detect_file_type("comprovante.pdf") == "pdf"

    def test_pdf_case_insensitive(self):
        assert detect_file_type("file.PDF") == "pdf"

    def test_jpg(self):
        assert detect_file_type("foto.jpg") == "image"

    def test_jpeg(self):
        assert detect_file_type("foto.jpeg") == "image"

    def test_png(self):
        assert detect_file_type("foto.png") == "image"

    def test_unknown_txt(self):
        assert detect_file_type("arquivo.txt") == "unknown"

    def test_unknown_no_extension(self):
        assert detect_file_type("README") == "unknown"

    def test_jfif(self):
        assert detect_file_type("image.jfif") == "image"


class TestFormatError:
    def test_format_error_message(self):
        assert format_error("Algo deu errado") == {"erro": "Algo deu errado"}

    def test_format_error_empty(self):
        assert format_error("") == {"erro": ""}
