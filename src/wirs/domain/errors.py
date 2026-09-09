"""Erros do domínio (núcleo da hierarquia da Seção 19.6 do spec)."""


class WirsError(Exception):
    """Base de todos os erros do scanner."""


class TargetError(WirsError):
    """Alvo inválido — nunca produz scan vazio válido."""


class SecurityBoundaryError(WirsError):
    """Violação de fronteira de segurança (ex.: path escapa do root)."""


class BudgetExceeded(WirsError):
    """Leitura além do budget: carrega os bytes já lidos para relato."""

    def __init__(self, message: str, bytes_read: int = 0) -> None:
        super().__init__(message)
        self.bytes_read = bytes_read


class ReadCancelled(WirsError):
    """Leitura interrompida por cancelamento cooperativo."""


class ProviderError(WirsError):
    """Falha de provider externo (vira Coverage, nunca aborta o scan)."""


class ProviderUnavailable(ProviderError):
    """Capability não disponível no ambiente."""


class ProviderTimeout(ProviderError):
    """Provider excedeu o timeout (processo encerrado)."""


class ProviderInvalidOutput(ProviderError):
    """Output do provider fora do contrato documentado."""


class ProviderExecutionError(ProviderError):
    """Provider falhou sem output aproveitável."""
