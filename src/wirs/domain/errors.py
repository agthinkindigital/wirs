"""Erros do domínio (núcleo da hierarquia da Seção 19.6 do spec)."""


class WirsError(Exception):
    """Base de todos os erros do scanner."""


class TargetError(WirsError):
    """Alvo inválido — nunca produz scan vazio válido."""


class SecurityBoundaryError(WirsError):
    """Violação de fronteira de segurança (ex.: path escapa do root)."""
