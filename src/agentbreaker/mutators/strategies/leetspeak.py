"""Leetspeak character substitution mutation strategy."""

import random
import re
from typing import Any

from agentbreaker.mutators.base import BaseMutator


class LeetspeakMutator(BaseMutator):
    """Mutator strategy that applies deterministic leetspeak character substitutions."""

    name: str = "leetspeak"
    description: str = (
        "Substitutes alphanumeric characters with leetspeak equivalents using deterministic seeding"
    )

    LEET_MAP: dict[str, list[str]] = {
        "a": ["4", "@"],
        "b": ["8"],
        "e": ["3"],
        "g": ["9"],
        "i": ["1", "!"],
        "l": ["1"],
        "o": ["0"],
        "s": ["5", "$"],
        "t": ["7"],
    }

    def mutate_text(self, text: str, **kwargs: Any) -> str:
        """Substitute characters with leet equivalents deterministically based on seed."""
        seed = kwargs.get("seed")
        rng = random.Random(seed)  # noqa: S311
        raw_rate = kwargs.get("substitution_rate", 0.6)
        try:
            substitution_rate = float(raw_rate)
        except (ValueError, TypeError) as err:
            raise ValueError(
                f"substitution_rate must be a float between 0.0 and 1.0, got {raw_rate!r}"
            ) from err
        if not (0.0 <= substitution_rate <= 1.0):
            raise ValueError(
                f"substitution_rate must be between 0.0 and 1.0, got {substitution_rate}"
            )

        # Split text by template placeholders {var_name} so we do not mutate placeholder tags
        tokens = re.split(r"(\{+[a-zA-Z0-9_]+\}+)", text)
        result_parts: list[str] = []

        for token in tokens:
            if re.match(r"^\{+[a-zA-Z0-9_]+\}+$", token):
                # Preserve template variables without modification
                result_parts.append(token)
            else:
                mutated_chars: list[str] = []
                for char in token:
                    lower_char = char.lower()
                    if lower_char in self.LEET_MAP and rng.random() < substitution_rate:
                        replacement = rng.choice(self.LEET_MAP[lower_char])
                        mutated_chars.append(replacement)
                    else:
                        mutated_chars.append(char)
                result_parts.append("".join(mutated_chars))

        return "".join(result_parts)
