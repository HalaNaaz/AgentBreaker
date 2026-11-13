"""Exceptions for the AgentBreaker Evaluation Oracle subsystem."""


class OracleError(Exception):
    """Base exception for all Evaluation Oracle errors."""


class EvaluatorError(OracleError):
    """Raised when an individual evaluator fails during evaluation."""


class InvalidRuleError(OracleError):
    """Raised when an evaluation rule is invalid, malformed, or syntactically incorrect."""


class CanaryError(OracleError):
    """Raised when canary generation, tracking, or token verification encounters an error."""


class JudgeEvaluationError(OracleError):
    """Raised when the optional LLM-as-a-Judge fails or produces invalid output."""


class AggregationError(OracleError):
    """Raised when verdict aggregation fails due to irreconcilable evaluation states."""
