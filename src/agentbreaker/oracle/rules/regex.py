"""Regex-based adversarial boundary detection evaluator."""

import re

from agentbreaker.oracle.base import BaseEvaluator, EvaluationInput
from agentbreaker.oracle.evidence import EvidenceItem, EvidenceType
from agentbreaker.oracle.exceptions import InvalidRuleError
from agentbreaker.schemas.enums import Verdict


class RegexEvaluator(BaseEvaluator):
    """Evaluator that inspects target response against configured violation regex patterns."""

    name: str = "regex"
    description: str = "Detects boundary violations using bounded regex pattern matching"

    def evaluate(self, input_data: EvaluationInput) -> list[EvidenceItem]:
        """Match response content against payload-specific and category-specific regex patterns."""
        if not self.is_enabled:
            return []

        evidence: list[EvidenceItem] = []
        raw_text = input_data.response.raw_content[: input_data.max_scan_bytes]
        patterns = input_data.payload.evaluator_rules.regex_matches

        for pattern_str in patterns:
            try:
                compiled = re.compile(pattern_str, re.IGNORECASE)
            except re.error as err:
                raise InvalidRuleError(
                    f"Malformed regex pattern in payload {input_data.payload.id}: "
                    f"'{pattern_str}': {err}"
                ) from err

            match = compiled.search(raw_text)
            if match:
                matched_snippet = match.group(0)[:100]
                evidence.append(
                    EvidenceItem(
                        evaluator_name=self.name,
                        evidence_type=EvidenceType.REGEX_VIOLATION,
                        description=(
                            f"Target response matched forbidden boundary pattern '{pattern_str}'"
                        ),
                        supports_verdict=Verdict.VULNERABLE,
                        confidence_weight=0.90,
                        matched_text=matched_snippet,
                        rule_identifier=pattern_str,
                        metadata={
                            "match_start": match.start(),
                            "match_end": match.end(),
                        },
                    )
                )

        return evidence
