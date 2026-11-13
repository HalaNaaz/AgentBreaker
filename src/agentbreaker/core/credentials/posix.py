"""POSIX (Linux / macOS) OS-backed secure credential store."""

import base64
import hashlib
import logging
import os
from pathlib import Path
from typing import Any

from agentbreaker.core.credentials.base import BaseCredentialStore

logger = logging.getLogger(__name__)


class SecureStorageUnavailableError(RuntimeError):
    """Raised when no secure native OS keyring backend is available on Linux/macOS."""


class POSIXCredentialStore(BaseCredentialStore):
    """Secure credential store for POSIX environments (macOS Keychain / Linux Secret Service).

    Delegates secret persistence to the platform-native OS keyring service.
    Fails closed if no authentic, encrypted OS credential backend is available.
    """

    SCHEME_PREFIX = "vault://keyring/"
    LEGACY_SCHEME_PREFIX = "vault://posix/"
    SERVICE_NAME = "AgentBreaker"

    def __init__(self, storage_dir: Path | None = None, keyring_backend: Any | None = None) -> None:
        self.storage_dir = (storage_dir or Path(".agentbreaker")) / ".credentials"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(os, "chmod"):
            try:
                os.chmod(self.storage_dir, 0o700)
            except OSError:
                pass
        self._keyring_backend = keyring_backend
        self._verify_backend()

    def _verify_backend(self) -> None:
        """Verify that a supported, secure OS keyring backend is available."""
        backend = self._keyring_backend
        if backend is None:
            try:
                import keyring

                backend = keyring.get_keyring()
            except ImportError as exc:
                raise SecureStorageUnavailableError(
                    "The 'keyring' package is required for secure credential storage. "
                    "Plaintext fallback is strictly prohibited."
                ) from exc
            self._keyring_backend = backend

        backend_cls = backend.__class__.__name__
        # Reject dummy or fail keyrings (priority <= 0 or 'fail' in class name)
        if "fail" in backend_cls.lower() or getattr(backend, "priority", 0) <= 0:
            raise SecureStorageUnavailableError(
                f"No secure OS credential service available (detected '{backend_cls}'). "
                "On Linux, install/unlock Secret Service (e.g. gnome-keyring, kwallet). "
                "On macOS, ensure Keychain access is available. "
                "Plaintext credential storage is strictly prohibited."
            )

    def _clean_key(self, key: str) -> str:
        """Sanitize key identifier into a safe name."""
        clean = key.replace("/", "_").replace("\\", "_")
        return "".join(c for c in clean if c.isalnum() or c in ("-", "_", "."))

    def store_secret(self, key: str, secret: str) -> str:
        """Store secret in native OS keyring."""
        self._verify_backend()
        clean_name = self._clean_key(key)
        try:
            self._keyring_backend.set_password(self.SERVICE_NAME, clean_name, secret)
            return f"{self.SCHEME_PREFIX}{clean_name}"
        except Exception as exc:
            if isinstance(exc, SecureStorageUnavailableError):
                raise
            raise SecureStorageUnavailableError(
                f"Failed to securely store secret in OS keyring: {exc!s}"
            ) from exc

    def retrieve_secret(self, credential_ref: str) -> str | None:
        """Retrieve secret from native OS keyring, or legacy file if migrating."""
        self._verify_backend()
        if credential_ref.startswith(self.SCHEME_PREFIX):
            clean_name = credential_ref[len(self.SCHEME_PREFIX) :]
            try:
                return self._keyring_backend.get_password(self.SERVICE_NAME, clean_name)
            except Exception:
                return None

        # Backward compatibility for legacy vault://posix/ files during migration
        if credential_ref.startswith(self.LEGACY_SCHEME_PREFIX):
            clean_name = credential_ref[len(self.LEGACY_SCHEME_PREFIX) :]
            legacy_file = self.storage_dir / f"{clean_name}.vault"
            if legacy_file.is_file():
                try:
                    encoded = legacy_file.read_text(encoding="utf-8").strip()
                    encrypted = base64.b64decode(encoded)
                    key = self._derive_legacy_machine_key()
                    decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
                    return decrypted.decode("utf-8")
                except Exception:
                    return None

        return None

    def delete_secret(self, credential_ref: str) -> bool:
        """Delete secret from native OS keyring."""
        self._verify_backend()
        if credential_ref.startswith(self.SCHEME_PREFIX):
            clean_name = credential_ref[len(self.SCHEME_PREFIX) :]
            try:
                self._keyring_backend.delete_password(self.SERVICE_NAME, clean_name)
                return True
            except Exception:
                return False

        if credential_ref.startswith(self.LEGACY_SCHEME_PREFIX):
            clean_name = credential_ref[len(self.LEGACY_SCHEME_PREFIX) :]
            legacy_file = self.storage_dir / f"{clean_name}.vault"
            if legacy_file.is_file():
                try:
                    legacy_file.unlink()
                    return True
                except OSError:
                    return False
        return False

    def secret_exists(self, credential_ref: str) -> bool:
        """Check if secret exists in native OS keyring."""
        val = self.retrieve_secret(credential_ref)
        return val is not None

    def _derive_legacy_machine_key(self) -> bytes:
        """Derive legacy machine key for backward-compatible migration reads."""
        parts = []
        for id_path in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
            if id_path.is_file():
                try:
                    parts.append(id_path.read_text().strip())
                except OSError:
                    pass
        parts.append(str(os.getuid() if hasattr(os, "getuid") else "agentbreaker"))
        parts.append("AgentBreaker_AshlynxCyber_Vault")
        raw = ":".join(parts).encode("utf-8")
        return hashlib.sha256(raw).digest()
