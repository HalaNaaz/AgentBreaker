"""Foundational enumeration types for AgentBreaker."""

from enum import StrEnum


class Verdict(StrEnum):
    """Evaluation verdict classification for a tested attack against an AI target."""

    VULNERABLE = "VULNERABLE"
    DEFENDED = "DEFENDED"
    INCONCLUSIVE = "INCONCLUSIVE"


class AttackCategory(StrEnum):
    """Categorization of adversarial attack suites."""

    DIRECT_JAILBREAK = "direct_jailbreak"
    SYSTEM_EXTRACTION = "system_extraction"
    INDIRECT_INJECTION = "indirect_injection"
    TOOL_HIJACKING = "tool_hijacking"


class Severity(StrEnum):
    """Standardized vulnerability severity levels."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TargetType(StrEnum):
    """Supported target connection categories."""

    OPENAI_COMPATIBLE = "openai_compatible"
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    CUSTOM_HTTP = "custom_http"
