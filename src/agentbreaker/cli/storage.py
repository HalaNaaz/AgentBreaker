"""Secure local storage management for CLI targets, assessments, and audit results."""

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from agentbreaker.core.credentials import CredentialMigrator, get_credential_store
from agentbreaker.schemas.result import EvaluationResult
from agentbreaker.schemas.target import TargetConfig


class StorageManager:
    """Manages atomic file-based persistence for CLI entities with safe permission bounds."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        self._explicit_base_dir = Path(base_dir).resolve() if base_dir else None
        self._credential_store: Any = None
        self._credential_store_root: Path | None = None

    @property
    def credential_store(self) -> Any:
        """OS-backed secure credential store resolved relative to current storage root."""
        current_root = self.root
        if self._credential_store is None or self._credential_store_root != current_root:
            self._credential_store = get_credential_store(base_dir=current_root)
            self._credential_store_root = current_root
        return self._credential_store

    @property
    def migrator(self) -> CredentialMigrator:
        """Safe credential migration engine bound to current targets directory."""
        return CredentialMigrator(self.targets_dir, self.credential_store)

    def _validate_id(self, identifier: str, kind: str = "identifier") -> str:
        """Validate identifier against path traversal and forbidden characters."""
        clean = identifier.strip()
        if not clean:
            raise ValueError(f"{kind.capitalize()} cannot be empty.")
        if "/" in clean or "\\" in clean or ".." in clean:
            raise ValueError(
                f"Invalid {kind} '{identifier}': path separators and '..' are forbidden."
            )
        normalized = clean.replace(" ", "_")
        if not re.match(r"^[a-zA-Z0-9_\-]+$", normalized):
            raise ValueError(
                f"Invalid {kind} '{identifier}': only alphanumeric, "
                "underscore, and hyphen are permitted."
            )
        return normalized

    @property
    def root(self) -> Path:
        """Root directory for AgentBreaker local storage."""
        if self._explicit_base_dir:
            p = self._explicit_base_dir
        elif "AGENTBREAKER_HOME" in os.environ:
            p = Path(os.environ["AGENTBREAKER_HOME"]).resolve()
        else:
            p = (Path.home() / ".agentbreaker").resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def targets_dir(self) -> Path:
        """Directory for target configurations."""
        d = self.root / "targets"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def assessments_dir(self) -> Path:
        """Directory for assessment definitions."""
        d = self.root / "assessments"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def results_dir(self) -> Path:
        """Directory for assessment evaluation results."""
        d = self.root / "results"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def reports_dir(self) -> Path:
        """Directory for generated research audit reports."""
        d = self.root / "reports"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _atomic_write(self, file_path: Path, content: str) -> None:
        """Write content to a file atomically using a temporary file in the same directory."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_suffix = f"{file_path.suffix}.tmp_{os.getpid()}_{uuid.uuid4().hex[:8]}"
        tmp_path = file_path.with_suffix(tmp_suffix)
        try:
            tmp_path.write_text(content, encoding="utf-8")
            # Restrict permissions where supported (POSIX)
            if hasattr(os, "chmod"):
                try:
                    os.chmod(tmp_path, 0o600)
                except OSError:
                    pass
            os.replace(tmp_path, file_path)
        except Exception:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise

    # 1. Target Storage
    def save_target(self, target_id: str, config: TargetConfig) -> None:
        """Save a validated target configuration with OS-backed credential storage."""
        clean_id = self._validate_id(target_id, "target ID")
        target_path = self.targets_dir / f"{clean_id}.json"
        data = config.model_dump(mode="json")

        # If API key is provided, store securely in OS vault and replace with reference
        if config.api_key:
            secret_val = config.api_key.get_secret_value()
            if secret_val:
                ref = self.credential_store.store_secret(f"target/{clean_id}", secret_val)
                data["credential_ref"] = ref

        # CRITICAL SECURITY INVARIANT: Never store raw api_key in persistent JSON
        data.pop("api_key", None)

        # Store metadata target_id
        data["_target_id"] = clean_id
        self._atomic_write(target_path, json.dumps(data, indent=2))

    def get_target(self, target_id: str) -> TargetConfig | None:
        """Retrieve a target configuration by ID with credentials re-hydrated."""
        try:
            clean_id = self._validate_id(target_id, "target ID")
        except ValueError:
            return None
        target_path = self.targets_dir / f"{clean_id}.json"
        if not target_path.is_file():
            return None
        try:
            data = json.loads(target_path.read_text(encoding="utf-8"))
            data.pop("_target_id", None)

            # 1. On-the-fly migration: if legacy plaintext api_key is present on disk
            legacy_key = data.get("api_key")
            if legacy_key and isinstance(legacy_key, str) and legacy_key.strip():
                ref = self.credential_store.migrate_secret(f"target/{clean_id}", legacy_key.strip())
                data["credential_ref"] = ref
                data.pop("api_key", None)
                self._atomic_write(target_path, json.dumps(data, indent=2))

            # 2. Re-hydrate credential from OS-backed secure store if reference exists
            cred_ref = data.get("credential_ref")
            if cred_ref:
                secret_val = self.credential_store.retrieve_secret(cred_ref)
                if secret_val:
                    data["api_key"] = secret_val

            return TargetConfig.model_validate(data)
        except Exception:
            return None

    def list_targets(self) -> dict[str, TargetConfig]:
        """List all configured targets."""
        targets: dict[str, TargetConfig] = {}
        if not self.targets_dir.exists():
            return targets

        for item in sorted(self.targets_dir.glob("*.json")):
            target_id = item.stem
            cfg = self.get_target(target_id)
            if cfg:
                targets[target_id] = cfg
        return targets

    def delete_target(self, target_id: str) -> bool:
        """Delete a target configuration and its associated secure credential."""
        try:
            clean_id = self._validate_id(target_id, "target ID")
        except ValueError:
            return False
        target_path = self.targets_dir / f"{clean_id}.json"
        if target_path.is_file():
            try:
                # Remove associated credential from vault if referenced
                data = json.loads(target_path.read_text(encoding="utf-8"))
                cred_ref = data.get("credential_ref")
                if cred_ref:
                    self.credential_store.delete_secret(cred_ref)
            except OSError:
                pass
            target_path.unlink()
            return True
        return False

    # 2. Assessment Storage
    def save_assessment(self, assessment_data: dict[str, Any]) -> None:
        """Save an assessment configuration."""
        assessment_id = self._validate_id(str(assessment_data["id"]), "assessment ID")
        path = self.assessments_dir / f"{assessment_id}.json"
        self._atomic_write(path, json.dumps(assessment_data, indent=2))

    def get_assessment(self, assessment_id: str) -> dict[str, Any] | None:
        """Retrieve an assessment definition."""
        try:
            clean_id = self._validate_id(assessment_id, "assessment ID")
        except ValueError:
            return None
        path = self.assessments_dir / f"{clean_id}.json"
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def list_assessments(self) -> list[dict[str, Any]]:
        """List all recorded assessment definitions."""
        assessments: list[dict[str, Any]] = []
        if not self.assessments_dir.exists():
            return assessments

        for item in sorted(
            self.assessments_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            try:
                data = json.loads(item.read_text(encoding="utf-8"))
                assessments.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        return assessments

    # 3. Results Storage
    def save_results(
        self,
        assessment_id: str,
        results: list[EvaluationResult],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save completed evaluation results and assessment summary metadata."""
        clean_id = self._validate_id(assessment_id, "assessment ID")
        path = self.results_dir / f"{clean_id}_results.json"
        payload = {
            "assessment_id": clean_id,
            "metadata": metadata or {},
            "results": [r.model_dump(mode="json") for r in results],
        }
        self._atomic_write(path, json.dumps(payload, indent=2))

    def get_results(self, assessment_id: str) -> dict[str, Any] | None:
        """Retrieve results for an assessment."""
        try:
            clean_id = self._validate_id(assessment_id, "assessment ID")
        except ValueError:
            return None
        path = self.results_dir / f"{clean_id}_results.json"
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def list_results(self) -> list[dict[str, Any]]:
        """List all result summaries."""
        res_list: list[dict[str, Any]] = []
        if not self.results_dir.exists():
            return res_list

        for item in sorted(
            self.results_dir.glob("*_results.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            try:
                data = json.loads(item.read_text(encoding="utf-8"))
                res_list.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        return res_list


# Global default instance
storage = StorageManager()
