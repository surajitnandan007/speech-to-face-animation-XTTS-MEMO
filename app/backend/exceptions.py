class ConfigurationError(RuntimeError):
    """Raised when the local pipeline configuration is invalid."""


class GenerationError(RuntimeError):
    """Raised when XTTS or MEMO generation fails."""

    def __init__(self, message: str, *, logs: str = "") -> None:
        super().__init__(message)
        self.logs = logs

