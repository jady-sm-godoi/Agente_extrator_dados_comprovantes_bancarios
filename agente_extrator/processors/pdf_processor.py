from io import BytesIO

from pdf2image import convert_from_bytes

from agente_extrator.processors.image_processor import ImageProcessor


class PdfProcessor:
    DPI = 300
    MAX_PAGES = 3

    @staticmethod
    def process(pdf_bytes: bytes) -> bytes:
        try:
            images = convert_from_bytes(
                pdf_bytes,
                dpi=PdfProcessor.DPI,
                first_page=1,
                last_page=PdfProcessor.MAX_PAGES,
            )
        except Exception as e:
            raise ValueError(
                f"Não foi possível processar o PDF. "
                f"Verifique se o arquivo é válido e não está protegido por senha. "
                f"Erro: {e}"
            )
        if not images:
            raise ValueError("PDF não contém páginas.")
        first_page = images[0]
        img_bytes = BytesIO()
        first_page.save(img_bytes, format="JPEG", quality=ImageProcessor.JPEG_QUALITY)
        return ImageProcessor.process(img_bytes.getvalue())
