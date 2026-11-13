"""POSIX (Linux / macOS) secure credential store implementation."""

import base64
import hashlib
import os
from pathlib import Path

from agentbreaker.core.credentials.base import BaseCredentialStore


class POSIXCredentialStore(BaseCredentialStore):
    """Secure credential store for POSIX environments (macOS / Linux).

    Stores encrypted secrets in a dedicated directory restricted to 0o700/0o600
    user permissions, utilizing machine-id and user UID key derivation.
    """

    SCHEME_PREFIX = "vault://posix/"

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir / ".credentials"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(os, "chmod"):
            try:
                os.chmod(self.storage_dir, 0o700)
            except OSError:
                pass
        self._key = self._derive_machine_key()

    def _derive_machine_key(self) -> bytes:
        """Derive an isolated machine-local key using system identifiers."""
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

    def _clean_key(self, key: str) -> str:
        clean = key.replace("/", "_").replace("\\", "_")
        return "".join(c for c in clean if c.isalnum() or c in ("-", "_", "."))

    def _xor_cipher(self, data: bytes) -> bytes:
        """Symmetric transform using derived machine key stream."""
        key = self._key
        key_len = len(key)
        return bytes(b ^ key[i % key_len] for i, b in enumerate(data))

    def store_secret(self, key: str, secret: str) -> str:
        clean_name = self._clean_key(key)
        target_file = self.storage_dir / f"{clean_name}.vault"
        encrypted = self._xor_cipher(secret.encode("utf-8"))
        encoded = base64.b64encode(encrypted).decode("ascii")

        tmp_file = self.storage_dir / f"{clean_name}.tmp"
        tmp_file.write_text(encoded, encoding="utf-8")
        if hasattr(os, "chmod"):
            try:
                os.chmod(tmp_file, 0o600)
            except OSError:
                pass
        os.replace(tmp_file, target_file)
        return f"{self.SCHEME_PREFIX}{clean_name}"

    def retrieve_secret(self, credential_ref: str) -> str | None:
        if not credential_ref.startswith(self.SCHEME_PREFIX):
            return None
        clean_name = credential_ref[len(self.SCHEME_PREFIX) :]
        target_file = self.storage_dir / f"{clean_name}.vault"
        if not target_file.is_file():
            return None
        try:
            encoded = target_file.read_text(encoding="utf-8").strip()
            encrypted = base64.b64decode(encoded)
            decrypted = self._xor_cipher(encrypted)
            return decrypted.decode("utf-8")
        except Exception:
            return None

    def delete_secret(self, credential_ref: str) -> bool:
        if not credential_ref.startswith(self.SCHEME_PREFIX):
            return False
        clean_name = credential_ref[len(self.SCHEME_PREFIX) :]
        target_file = self.storage_dir / f"{clean_name}.vault"
        if target_file.is_file():
            try:
                target_file.unlink()
                return True
            except OSError:
                return False
        return False

    def secret_exists(self, credential_ref: str) -> bool:
        if not credential_ref.startswith(self.SCHEME_PREFIX):
            return False
        clean_name = credential_ref[len(self.SCHEME_PREFIX) :]
        return (self.storage_dir / f"{clean_name}.vault").is_file()
