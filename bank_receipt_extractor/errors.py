import logging

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Erro base de extração, carregando o status HTTP e o motivo.

    A mensagem técnica da causa NUNCA deve ir para o cliente — vá para o log.
    """

    status_code: int = 500
    motivo: str = "unknown_error"
    mensagem: str = "Não foi possível processar o comprovante."

    def __init__(self, causa: str | None = None):
        self.causa = causa
        if causa:
            logger.warning("%s: %s", self.__class__.__name__, causa)
        super().__init__(self.mensagem)


class ProviderError(ExtractionError):
    """Todos os provedores de IA falharam."""
    status_code = 502
    motivo = "provider_error"
    mensagem = "Serviço de extração indisponível. Tente novamente."


class UnsupportedFormatError(ExtractionError):
    """O arquivo não é PDF, PNG ou JPG."""
    status_code = 415
    motivo = "unsupported_format"
    mensagem = "Formato não suportado. Aceito: PDF, PNG, JPG."


class FileTooLargeError(ExtractionError):
    """O arquivo excede o limite de tamanho."""
    status_code = 413
    motivo = "file_too_large"
    mensagem = "Arquivo excede o limite de 50MB."


class InvalidFileError(ExtractionError):
    """O arquivo é corrompido ou ilegível."""
    status_code = 400
    motivo = "invalid_file"
    mensagem = "Não foi possível ler o arquivo."


class ParseError(ExtractionError):
    """O modelo retornou um JSON que não valida no schema."""
    status_code = 422
    motivo = "parse_error"
    mensagem = "Não foi possível extrair os dados do comprovante."


def format_error(exc: ExtractionError) -> dict:
    """Monta o dict de erro neutro e seguro para o cliente.

    Loga a causa técnica no servidor; o cliente recebe apenas a mensagem neutra,
    o status HTTP e o motivo classificatório. Nada de chaves, request_id
    ou detalhes internos do provedor.
    """
    if exc.causa:
        logger.error("Causa técnica (não exposta ao cliente): %s", exc.causa)
    return {
        "erro": exc.mensagem,
        "status": exc.status_code,
        "motivo": exc.motivo,
    }


def erro_para_status(resultado: dict) -> int:
    """Retorna o status HTTP de um dict de erro (padrão: 500)."""
    return resultado.get("status", 500)