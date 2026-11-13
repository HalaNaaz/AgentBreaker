"""Migration engine for safely migrating legacy plaintext credentials to OS storage."""

import json
import logging
import os
from pathlib import Path
from typing import Any

from agentbreaker.core.credentials.base import BaseCredentialStore

logger = logging.getLogger(__name__)


class CredentialMigrator:
    """Detects and safely migrates legacy plaintext credentials in target configurations.

    Adheres to strict security invariants:
    - Zero secret disclosure in logs or exceptions.
    - Retrieval verification prior to removing plaintext from disk.
    - Atomic file replacement with restricted file permissions.
    - Complete idempotency (targets already possessing credential_ref are untouched).
    """

    def __init__(self, targets_dir: Path, credential_store: BaseCredentialStore) -> None:
        self.targets_dir = targets_dir
        self.credential_store = credential_store

    def migrate_all(self) -> dict[str, Any]:
        """Scan all target files and migrate legacy credentials.

        Returns:
            dict containing migration telemetry (scanned, migrated, skipped, failed).
        """
        report: dict[str, Any] = {
            "scanned": 0,
            "migrated": 0,
            "skipped": 0,
            "failed": 0,
            "migrated_targets": [],
            "errors": [],
        }

        if not self.targets_dir.is_dir():
            return report

        for path in sorted(self.targets_dir.glob("*.json")):
            report["scanned"] += 1
            target_id = path.stem
            try:
                migrated = self.migrate_target_file(path, target_id)
                if migrated:
                    report["migrated"] += 1
                    report["migrated_targets"].append(target_id)
                else:
                    report["skipped"] += 1
            except Exception as exc:
                report["failed"] += 1
                logger.error("Failed to migrate credential for target: %s", target_id)
                report["errors"].append(f"Target '{target_id}': {exc!s}")

        return report

    def migrate_target_file(self, file_path: Path, target_id: str) -> bool:
        """Migrate a single target configuration file if legacy api_key is present."""
        if not file_path.is_file():
            return False

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return False

        legacy_key = data.get("api_key")
        # Check if already migrated or no key present
        if not legacy_key or not isinstance(legacy_key, str) or not legacy_key.strip():
            return False

        # If already has a valid credential_ref, clean up the redundant api_key
        existing_ref = data.get("credential_ref")
        if existing_ref and self.credential_store.secret_exists(existing_ref):
            del data["api_key"]
            self._atomic_save(file_path, data)
            return True

        # Store into OS-backed vault and verify
        credential_ref = self.credential_store.migrate_secret(
            f"target/{target_id}", legacy_key.strip()
        )

        # Replace plaintext with reference
        del data["api_key"]
        data["credential_ref"] = credential_ref

        # Atomically write to disk
        self._atomic_save(file_path, data)
        return True

    def _atomic_save(self, file_path: Path, data: dict[str, Any]) -> None:
        """Atomically persist updated configuration data with restricted permissions."""
        tmp_path = file_path.with_suffix(".tmp_mig")
        try:
            content = json.dumps(data, indent=2)
            tmp_path.write_text(content, encoding="utf-8")
            if hasattr(os, "chmod"):
                try:
                    os.chmod(tmp_path, 0o600)
                except OSError:
                    pass
            os.replace(tmp_path, file_path)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
