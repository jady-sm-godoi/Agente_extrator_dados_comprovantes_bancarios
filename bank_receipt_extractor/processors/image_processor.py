from io import BytesIO

from PIL import Image, ImageOps  # type: ignore[attr-defined]


class ImageProcessor:
    MAX_DIMENSION = 2048
    JPEG_QUALITY = 85

    @staticmethod
    def process(image_bytes: bytes) -> bytes:
        image: Image.Image = Image.open(BytesIO(image_bytes))
        transposed = ImageOps.exif_transpose(image)
        if transposed is not None:
            image = transposed
        if max(image.size) > ImageProcessor.MAX_DIMENSION:
            image.thumbnail(
                (ImageProcessor.MAX_DIMENSION, ImageProcessor.MAX_DIMENSION),
                Image.LANCZOS,  # type: ignore[attr-defined]
            )
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        output = BytesIO()
        image.save(output, format="JPEG", quality=ImageProcessor.JPEG_QUALITY)
        return output.getvalue()
