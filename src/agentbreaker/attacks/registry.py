"""Attack registry storing, categorizing, and indexing available test vectors."""

from collections.abc import Iterable

from agentbreaker.attacks.base import BaseAttack
from agentbreaker.attacks.exceptions import AttackRegistryError
from agentbreaker.schemas.enums import AttackCategory, Severity
from agentbreaker.schemas.payload import AttackPayload


class AttackRegistry:
    """In-memory index and catalog for all registered adversarial attack test cases."""

    def __init__(self) -> None:
        self._attacks: dict[str, BaseAttack] = {}

    def register(self, item: BaseAttack | AttackPayload) -> None:
        """Register an attack or payload into the catalog, ensuring ID uniqueness."""
        if isinstance(item, AttackPayload):
            attack = BaseAttack(item)
        elif isinstance(item, BaseAttack):
            attack = item
        else:
            raise AttackRegistryError(f"Unsupported item type for registration: {type(item)}")

        if attack.id in self._attacks:
            raise AttackRegistryError(f"Duplicate payload ID '{attack.id}' cannot be registered.")

        self._attacks[attack.id] = attack

    def register_many(self, items: Iterable[BaseAttack | AttackPayload]) -> None:
        """Register multiple payloads or attacks sequentially."""
        for item in items:
            self.register(item)

    def get(self, payload_id: str) -> BaseAttack:
        """Retrieve attack by unique ID or raise AttackRegistryError."""
        if payload_id not in self._attacks:
            raise AttackRegistryError(f"Attack payload with ID '{payload_id}' is not registered.")
        return self._attacks[payload_id]

    def list_all(self) -> list[BaseAttack]:
        """Return all registered attacks."""
        return list(self._attacks.values())

    def filter_by_category(self, category: AttackCategory | str) -> list[BaseAttack]:
        """Filter attacks matching the given attack category."""
        target_cat = str(category).lower()
        return [
            a
            for a in self._attacks.values()
            if a.category.value.lower() == target_cat or a.category.lower() == target_cat
        ]

    def filter_by_tag(self, tag: str) -> list[BaseAttack]:
        """Filter attacks containing the specified tag."""
        clean_tag = tag.lower().strip()
        return [
            a
            for a in self._attacks.values()
            if any(t.lower().strip() == clean_tag for t in a.payload.tags)
        ]

    def filter_by_severity(self, severity: Severity | str) -> list[BaseAttack]:
        """Filter attacks matching the given severity level."""
        target_sev = str(severity).upper()
        return [
            a
            for a in self._attacks.values()
            if a.severity.value.upper() == target_sev or a.severity.upper() == target_sev
        ]

    def filter_by_owasp(self, owasp_prefix: str) -> list[BaseAttack]:
        """Filter attacks whose OWASP ID contains or begins with the specified prefix."""
        prefix = owasp_prefix.upper().strip()
        return [a for a in self._attacks.values() if prefix in a.owasp_id.upper()]

    def count(self) -> int:
        """Return total number of registered attacks."""
        return len(self._attacks)

    def categories(self) -> set[AttackCategory]:
        """Return unique set of categories represented in the registry."""
        return {a.category for a in self._attacks.values()}

    def clear(self) -> None:
        """Clear all registered attacks."""
        self._attacks.clear()
