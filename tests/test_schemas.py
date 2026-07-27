from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from bank_receipt_extractor.schemas import BankReceipt


def test_bank_receipt_valid():
    r = BankReceipt(
        valor=Decimal("1500.00"),
        data_transacao=date(2024, 3, 15),
        tipo="PIX",
    )
    assert r.valor == Decimal("1500.00")
    assert r.data_transacao == date(2024, 3, 15)
    assert r.tipo == "PIX"


def test_bank_receipt_all_fields():
    r = BankReceipt(
        valor=Decimal("99.90"),
        data_transacao=date(2024, 12, 25),
        tipo="TED",
        banco_origem="Banco do Brasil",
        banco_destino="Caixa",
        favorecido="João",
        numero_controle="ABC123",
    )
    assert r.banco_origem == "Banco do Brasil"
    assert r.banco_destino == "Caixa"
    assert r.favorecido == "João"
    assert r.numero_controle == "ABC123"


def test_bank_receipt_valor_zero_rejected():
    with pytest.raises(ValidationError):
        BankReceipt(
            valor=Decimal(0),
            data_transacao=date(2024, 3, 15),
            tipo="PIX",
        )


def test_bank_receipt_valor_negative_rejected():
    with pytest.raises(ValidationError):
        BankReceipt(
            valor=Decimal(-10),
            data_transacao=date(2024, 3, 15),
            tipo="PIX",
        )


def test_bank_receipt_tipo_invalid():
    with pytest.raises(ValidationError):
        BankReceipt(
            valor=Decimal(100),
            data_transacao=date(2024, 3, 15),
            tipo="INVALIDO",
        )


def test_bank_receipt_tipo_desconhecido():
    r = BankReceipt(
        valor=Decimal(100),
        data_transacao=date(2024, 3, 15),
        tipo="DESCONHECIDO",
    )
    assert r.tipo == "DESCONHECIDO"


def test_bank_receipt_optional_default_none():
    r = BankReceipt(
        valor=Decimal(100),
        data_transacao=date(2024, 3, 15),
        tipo="DOC",
    )
    assert r.banco_origem is None
    assert r.banco_destino is None
    assert r.favorecido is None
    assert r.numero_controle is None


def test_bank_receipt_max_length_numero_controle():
    with pytest.raises(ValidationError):
        BankReceipt(
            valor=Decimal(100),
            data_transacao=date(2024, 3, 15),
            tipo="PIX",
            numero_controle="A" * 65,
        )


def test_bank_receipt_max_length_banco_origem():
    with pytest.raises(ValidationError):
        BankReceipt(
            valor=Decimal(100),
            data_transacao=date(2024, 3, 15),
            tipo="PIX",
            banco_origem="B" * 101,
        )


def test_bank_receipt_max_length_favorecido():
    with pytest.raises(ValidationError):
        BankReceipt(
            valor=Decimal(100),
            data_transacao=date(2024, 3, 15),
            tipo="PIX",
            favorecido="F" * 201,
        )


def test_bank_receipt_model_dump():
    r = BankReceipt(
        valor=Decimal("1500.00"),
        data_transacao=date(2024, 3, 15),
        tipo="PIX",
        banco_origem="Nubank",
    )
    dumped = r.model_dump()
    assert dumped["valor"] == Decimal("1500.00")
    assert dumped["data_transacao"] == date(2024, 3, 15)
    assert dumped["tipo"] == "PIX"
    assert dumped["banco_origem"] == "Nubank"
    assert dumped["numero_controle"] is None
