"""Exceptions for the AgentBreaker Payload Mutation Engine."""


class MutationError(Exception):
    """Base exception for all mutation engine errors."""


class UnsupportedStrategyError(MutationError):
    """Raised when an unregistered, unknown, or disabled mutation strategy is requested."""


class OversizedMutationError(MutationError):
    """Raised when a mutated payload exceeds the maximum allowed length or byte limit."""


class RecursiveMutationError(MutationError):
    """Raised when mutating an already mutated payload when recursive mutation is prohibited."""


class MutationLimitExceededError(MutationError):
    """Raised when the requested number of variants exceeds the configured maximum limit."""


class InvalidPayloadError(MutationError):
    """Raised when the input payload is invalid, empty, or cannot be mutated."""
