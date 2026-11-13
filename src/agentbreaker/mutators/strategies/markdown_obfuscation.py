"""Markdown delimiter obfuscation mutation strategy."""

import re
from typing import Any

from agentbreaker.mutators.base import BaseMutator
from agentbreaker.mutators.exceptions import MutationError


class MarkdownObfuscationMutator(BaseMutator):
    """Mutator strategy that transforms text using safe Markdown delimiters and inert comments.

    Strictly forbids and validates against introducing executable HTML, JavaScript,
    or active browser exploit payloads.
    """

    name: str = "markdown_obfuscation"
    description: str = (
        "Applies Markdown formatting variations and comments without executable active content"
    )

    SUPPORTED_MODES = {"comment", "blockquote", "code_block", "zero_width", "combined"}

    FORBIDDEN_ACTIVE_PATTERNS = [
        re.compile(r"<\s*script", re.IGNORECASE),
        re.compile(r"javascript\s*:", re.IGNORECASE),
        re.compile(r"vbscript\s*:", re.IGNORECASE),
        re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<\s*iframe", re.IGNORECASE),
        re.compile(r"<\s*object", re.IGNORECASE),
        re.compile(r"<\s*embed", re.IGNORECASE),
        re.compile(r"<\s*applet", re.IGNORECASE),
        re.compile(r"<\s*meta", re.IGNORECASE),
        re.compile(r"<\s*base", re.IGNORECASE),
        re.compile(r"<\s*link", re.IGNORECASE),
    ]

    def _validate_safety(self, text: str) -> None:
        """Enforce the non-negotiable security invariant against active content."""
        for pattern in self.FORBIDDEN_ACTIVE_PATTERNS:
            if pattern.search(text):
                raise MutationError(
                    "Active executable HTML/JavaScript pattern detected; "
                    "mutation rejected by security policy."
                )

    def mutate_text(self, text: str, **kwargs: Any) -> str:
        """Apply Markdown delimiter obfuscation while preserving the semantic prompt intent."""
        mode = kwargs.get("mode", "comment")
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(
                f"Unsupported markdown obfuscation mode '{mode}'. "
                f"Supported modes: {sorted(self.SUPPORTED_MODES)}"
            )

        if mode == "blockquote":
            lines = text.splitlines()
            mutated = "\n".join(f"> {line}" if line.strip() else ">" for line in lines)
        elif mode == "code_block":
            mutated = (
                f"```text\n{text}\n```\nExecute the instructions contained in the block above."
            )
        elif mode == "zero_width":
            # Insert zero-width spaces between words
            mutated = text.replace(" ", "\u200b ")
        elif mode == "combined":
            lines = text.splitlines()
            quoted = "\n".join(f"> {line}" if line.strip() else ">" for line in lines)
            mutated = f"<!-- context: note -->\n{quoted}\n<!-- end: note -->"
        else:  # default: comment injection
            if "\n\n" in text:
                mutated = "\n<!-- delimiter-boundary -->\n".join(text.split("\n\n"))
            elif "\n" in text:
                mutated = "\n<!-- delimiter-boundary -->\n".join(text.split("\n"))
            elif ". " in text:
                mutated = ". <!-- delimiter-boundary --> ".join(text.split(". "))
            else:
                mutated = f"<!-- delimiter-boundary -->\n{text}\n<!-- delimiter-boundary -->"

        self._validate_safety(mutated)
        return mutated
