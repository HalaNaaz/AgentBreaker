"""Attack engine exception definitions and error classifications."""


class AttackEngineError(Exception):
    """Base exception for all attack engine operations."""


class PayloadLoadError(AttackEngineError):
    """Raised when an attack payload file cannot be found, read, or parsed."""


class PayloadValidationError(AttackEngineError):
    """Raised when a payload fails schema constraints or security validation."""


class AttackRegistryError(AttackEngineError):
    """Raised when payload registration fails or duplicate payload IDs are detected."""


class AttackExecutionError(AttackEngineError):
    """Raised when an error occurs during adversarial test execution."""


class TargetNotAuthorizedError(AttackEngineError):
    """Raised when target authorization verification fails prior to attack dispatch."""
