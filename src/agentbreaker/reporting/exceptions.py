"""Domain-specific exceptions for AgentBreaker reporting and analytics subsystem."""


class ReportingError(Exception):
    """Base exception for all reporting and analytics operations."""


class ReportNotFoundError(ReportingError):
    """Raised when a requested report ID or source assessment results cannot be found."""


class ReportGenerationError(ReportingError):
    """Raised when compilation or formatting of a report fails."""


class IncompatibleAssessmentError(ReportingError):
    """Raised when attempting an invalid comparison across incompatible assessments."""


class RedactionError(ReportingError):
    """Raised when sensitive data redaction encounters an unexpected failure."""


class InvalidReportPathError(ReportingError):
    """Raised when an output report path attempts directory traversal or escapes approved bounds."""
