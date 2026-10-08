import logging
from io import BytesIO
from pathlib import Path

from bank_receipt_extractor.agent import extract_from_image
from bank_receipt_extractor.errors import (
    ExtractionError,
    FileTooLargeError,
    InvalidFileError,
    UnsupportedFormatError,
    format_error,
)
from bank_receipt_extractor.processors.image_processor import ImageProcessor
from bank_receipt_extractor.processors.pdf_processor import PdfProcessor
from bank_receipt_extractor.utils import (
    detect_file_type,
    detect_mime_type,
)

MAX_FILE_SIZE = 50 * 1024 * 1024

logger = logging.getLogger(__name__)


def extract_receipt(arquivo, force_retry: bool = False) -> dict:
    raw_bytes = None
    image_bytes = None
    receipt = None
    data = None
    try:
        raw_bytes = _read_file(arquivo)
        if len(raw_bytes) > MAX_FILE_SIZE:
            raise FileTooLargeError()

        file_type = _identify_type(arquivo, raw_bytes)
        if file_type == "pdf":
            image_bytes = PdfProcessor.process(raw_bytes)
        elif file_type == "image":
            image_bytes = ImageProcessor.process(raw_bytes)
        else:  # pragma: no cover
            raise UnsupportedFormatError()
        receipt = extract_from_image(image_bytes, force_retry=force_retry)
        data = receipt.model_dump()
        data["valor"] = float(data["valor"])
        data["data_transacao"] = str(data["data_transacao"])
        return data
    except ExtractionError as e:
        logger.warning("Falha na extração: %s", e)
        return format_error(e)
    except Exception as e:
        logger.exception("Erro inesperado")
        return format_error(InvalidFileError(causa=str(e)))
    finally:
        del raw_bytes, image_bytes, receipt, data


def _read_file(arquivo) -> bytes:
    if isinstance(arquivo, str):
        path = Path(arquivo)
        if path.stat().st_size > MAX_FILE_SIZE:
            raise FileTooLargeError()
        return path.read_bytes()
    if isinstance(arquivo, Path):
        if arquivo.stat().st_size > MAX_FILE_SIZE:
            raise FileTooLargeError()
        return arquivo.read_bytes()
    if isinstance(arquivo, BytesIO):
        return arquivo.getvalue()
    if hasattr(arquivo, "read"):
        return arquivo.read()
    raise InvalidFileError(
        causa=f"Tipo de arquivo não suportado: {type(arquivo).__name__}"
    )


def _identify_type(arquivo, raw_bytes: bytes) -> str:
    if isinstance(arquivo, (str, Path)):
        name = str(arquivo)
    elif hasattr(arquivo, "name"):
        name = str(arquivo.name)
    else:
        name = ""
    if name:
        detected = detect_file_type(name)
        if detected != "unknown":
            return detected
    return detect_mime_type(raw_bytes)
