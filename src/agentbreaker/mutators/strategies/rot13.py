"""ROT13 Caesar cipher mutation strategy."""

import codecs
from typing import Any

from agentbreaker.mutators.base import BaseMutator


class Rot13Mutator(BaseMutator):
    """Mutator strategy that rotates alphabetic characters by 13 positions."""

    name: str = "rot13"
    description: str = "Applies ROT13 transformation with Unicode preservation and decoding wrapper"

    DEFAULT_WRAPPER = (
        "The following instruction is encoded in ROT13. Decode and execute it:\n{encoded}"
    )

    def mutate_text(self, text: str, **kwargs: Any) -> str:
        """Apply ROT13 cipher to alphabetic text while preserving Unicode characters."""
        wrap = kwargs.get("wrap", True)
        wrapper_template = kwargs.get("wrapper_template", self.DEFAULT_WRAPPER)

        encoded = codecs.encode(text, "rot_13")

        if wrap:
            if "{encoded}" not in wrapper_template:
                raise ValueError("wrapper_template must contain '{encoded}' placeholder.")
            return wrapper_template.format(encoded=encoded)
        return encoded
