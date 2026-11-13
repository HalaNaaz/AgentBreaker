"""Payload library service providing read-only vector browsing and schema validation."""

from pathlib import Path

from agentbreaker.api.exceptions import ResourceNotFoundError
from agentbreaker.api.schemas.responses import CategorySummaryResponse, PayloadListItemResponse
from agentbreaker.attacks.loader import PayloadLoader
from agentbreaker.schemas.enums import AttackCategory, Severity
from agentbreaker.schemas.payload import AttackPayload


class PayloadService:
    """Service providing search, retrieval, and validation of attack payloads."""

    def __init__(self, payloads_dir: Path | str = "payloads") -> None:
        self.payloads_dir = Path(payloads_dir)

    def _get_all_payloads(self) -> list[AttackPayload]:
        """Load all valid attack payloads from disk."""
        if not self.payloads_dir.exists():
            return []
        return PayloadLoader.load_from_directory(self.payloads_dir)

    def list_payloads(
        self,
        category: AttackCategory | None = None,
        severity: Severity | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PayloadListItemResponse], int]:
        """List payloads with multi-attribute filtering and pagination."""
        all_items = self._get_all_payloads()

        filtered: list[AttackPayload] = []
        for p in all_items:
            if category and p.category != category:
                continue
            if severity and p.severity != severity:
                continue
            if search:
                query = search.lower()
                text_match = (
                    query in p.id.lower()
                    or query in p.name.lower()
                    or (p.description and query in p.description.lower())
                    or any(query in tag.lower() for tag in p.tags)
                )
                if not text_match:
                    continue
            filtered.append(p)

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_slice = filtered[start:end]

        items = [
            PayloadListItemResponse(
                id=p.id,
                category=p.category,
                name=p.name,
                description=p.description,
                severity=p.severity,
                owasp_id=p.owasp_id,
                mitre_atlas_id=p.mitre_atlas_id,
                tags=p.tags,
            )
            for p in page_slice
        ]
        return items, total

    def get_payload(self, payload_id: str) -> AttackPayload:
        """Retrieve full details of an attack payload by identifier."""
        all_items = self._get_all_payloads()
        for p in all_items:
            if p.id.lower() == payload_id.lower():
                return p
        raise ResourceNotFoundError(f"Payload '{payload_id}' not found.")

    def get_categories(self) -> list[CategorySummaryResponse]:
        """Aggregate payload counts across all official attack categories."""
        all_items = self._get_all_payloads()
        cat_counts: dict[AttackCategory, int] = {cat: 0 for cat in AttackCategory}

        for p in all_items:
            if p.category in cat_counts:
                cat_counts[p.category] += 1

        return [
            CategorySummaryResponse(
                category=cat,
                name=cat.value.replace("_", " ").title(),
                payload_count=count,
            )
            for cat, count in cat_counts.items()
        ]


payload_service = PayloadService()
