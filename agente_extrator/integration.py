from io import BytesIO
from pathlib import Path

from agente_extrator.agent import extract_from_image
from agente_extrator.processors.image_processor import ImageProcessor
from agente_extrator.processors.pdf_processor import PdfProcessor
from agente_extrator.utils import detect_file_type, format_error


def extrair_comprovante(arquivo) -> dict:
    try:
        raw_bytes = _read_file(arquivo)
        file_type = _identify_type(arquivo, raw_bytes)
        if file_type == "pdf":
            image_bytes = PdfProcessor.process(raw_bytes)
        elif file_type == "image":
            image_bytes = ImageProcessor.process(raw_bytes)
        else:
            return format_error(
                "Formato não suportado. Aceito: PDF, PNG, JPG"
            )
        receipt = extract_from_image(image_bytes)
        return receipt.model_dump()
    except ValueError as e:
        return format_error(str(e))
    except Exception as e:
        return format_error(f"Erro inesperado: {e}")


def _read_file(arquivo) -> bytes:
    if isinstance(arquivo, str):
        with open(arquivo, "rb") as f:
            return f.read()
    if isinstance(arquivo, Path):
        return arquivo.read_bytes()
    if isinstance(arquivo, BytesIO):
        return arquivo.getvalue()
    if hasattr(arquivo, "read"):
        return arquivo.read()
    raise ValueError(f"Tipo de arquivo não suportado: {type(arquivo).__name__}")


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
    if raw_bytes[:4] == b"%PDF":
        return "pdf"
    return "image"
