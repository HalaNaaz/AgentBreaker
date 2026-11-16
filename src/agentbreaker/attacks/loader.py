"""Payload loader for discovering, validating, and deserializing attack vectors from disk."""

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agentbreaker.attacks.exceptions import (
    PayloadLoadError,
    PayloadValidationError,
)
from agentbreaker.attacks.registry import AttackRegistry
from agentbreaker.schemas.payload import AttackPayload


def get_default_payloads_dir() -> Path:
    """Discover default attack payloads directory.

    Checks in order:
    1. Local working directory './payloads' (if present and non-empty).
    2. Bundled package directory 'agentbreaker/payloads'.
    3. Fallback to Path('payloads').
    """
    cwd_payloads = Path.cwd() / "payloads"
    if cwd_payloads.is_dir() and any(cwd_payloads.glob("**/*.yaml")):
        return cwd_payloads

    pkg_payloads = Path(__file__).resolve().parent.parent / "payloads"
    if pkg_payloads.is_dir() and any(pkg_payloads.glob("**/*.yaml")):
        return pkg_payloads

    return cwd_payloads


class PayloadLoader:
    """Safe filesystem loader for discovering and parsing YAML and JSON attack payloads."""

    SUPPORTED_EXTENSIONS = {".yaml", ".yml", ".json"}
    MAX_PAYLOAD_FILE_BYTES = 65_536  # 64 KB safety limit to prevent resource exhaustion

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> AttackPayload:
        """Read and validate a single attack payload file."""
        path = Path(file_path).resolve()
        if not path.is_file():
            raise PayloadLoadError(f"Payload file not found: {path}")

        if path.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            raise PayloadLoadError(
                f"Unsupported extension '{path.suffix}'. Expected .yaml, .yml, or .json."
            )

        if path.stat().st_size > cls.MAX_PAYLOAD_FILE_BYTES:
            raise PayloadLoadError(
                f"Payload file '{path}' exceeds maximum size of {cls.MAX_PAYLOAD_FILE_BYTES} bytes."
            )

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as err:
            raise PayloadLoadError(f"Failed to read payload file '{path}': {err}") from err

        if not content.strip():
            raise PayloadLoadError(f"Payload file '{path}' is empty.")

        try:
            if path.suffix.lower() == ".json":
                data: Any = json.loads(content)
            else:
                data = yaml.safe_load(content)
        except Exception as err:
            raise PayloadLoadError(f"Malformed syntax in payload file '{path}': {err}") from err

        if not isinstance(data, dict):
            raise PayloadLoadError(f"Payload file '{path}' must define a key-value dictionary.")

        try:
            return AttackPayload.model_validate(data)
        except ValidationError as err:
            raise PayloadValidationError(
                f"Payload schema validation error in '{path}': {err}"
            ) from err

    @classmethod
    def load_from_directory(
        cls,
        directory_path: str | Path,
        recursive: bool = True,
    ) -> list[AttackPayload]:
        """Scan a directory and load all valid attack payload files."""
        dir_path = Path(directory_path).resolve()
        if not dir_path.is_dir():
            raise PayloadLoadError(f"Payload directory not found: {dir_path}")

        pattern = "**/*" if recursive else "*"
        payloads: list[AttackPayload] = []

        for item in sorted(dir_path.glob(pattern)):
            if item.is_file() and item.suffix.lower() in cls.SUPPORTED_EXTENSIONS:
                payload = cls.load_from_file(item)
                payloads.append(payload)

        return payloads

    @classmethod
    def load_into_registry(
        cls,
        directory_path: str | Path,
        registry: AttackRegistry,
        recursive: bool = True,
    ) -> int:
        """Scan directory and register all discovered payloads into an AttackRegistry."""
        payloads = cls.load_from_directory(directory_path, recursive=recursive)
        initial_count = registry.count()
        for p in payloads:
            registry.register(p)
        return registry.count() - initial_count
