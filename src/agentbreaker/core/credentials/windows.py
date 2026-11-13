"""Windows Data Protection API (DPAPI) backed secure credential store."""

import base64
import ctypes
import os
from ctypes import wintypes
from pathlib import Path

from agentbreaker.core.credentials.base import BaseCredentialStore


class DATA_BLOB(ctypes.Structure):  # noqa: N801
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


CRYPTPROTECT_UI_FORBIDDEN = 0x01
AGENTBREAKER_ENTROPY = b"AgentBreaker_AshlynxCyber_CredentialVault_v1"


class WindowsDPAPICredentialStore(BaseCredentialStore):
    """Secure credential store leveraging Windows DPAPI (CryptProtectData).

    Keys are encrypted using the current user's DPAPI logon credentials and
    hardware TPM/LSA state, ensuring ciphertext cannot be read by another user
    or without physical logon credentials.
    """

    SCHEME_PREFIX = "vault://dpapi/"

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir / ".credentials"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(os, "chmod"):
            try:
                os.chmod(self.storage_dir, 0o700)
            except OSError:
                pass

    def _clean_key(self, key: str) -> str:
        """Sanitize key identifier into a safe filename."""
        clean = key.replace("/", "_").replace("\\", "_")
        return "".join(c for c in clean if c.isalnum() or c in ("-", "_", "."))

    def _dpapi_protect(self, plaintext: bytes) -> bytes:
        """Encrypt bytes using CryptProtectData."""
        data_in = DATA_BLOB(
            len(plaintext),
            ctypes.cast(ctypes.create_string_buffer(plaintext), ctypes.POINTER(ctypes.c_char)),
        )
        ent_in = DATA_BLOB(
            len(AGENTBREAKER_ENTROPY),
            ctypes.cast(
                ctypes.create_string_buffer(AGENTBREAKER_ENTROPY),
                ctypes.POINTER(ctypes.c_char),
            ),
        )
        data_out = DATA_BLOB()

        res = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(data_in),
            "AgentBreaker Target Credential",
            ctypes.byref(ent_in),
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(data_out),
        )
        if not res:
            err = ctypes.GetLastError()
            raise OSError(f"CryptProtectData failed with system error code {err}")

        try:
            return ctypes.string_at(data_out.pbData, data_out.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(data_out.pbData)

    def _dpapi_unprotect(self, ciphertext: bytes) -> bytes:
        """Decrypt bytes using CryptUnprotectData."""
        data_in = DATA_BLOB(
            len(ciphertext),
            ctypes.cast(ctypes.create_string_buffer(ciphertext), ctypes.POINTER(ctypes.c_char)),
        )
        ent_in = DATA_BLOB(
            len(AGENTBREAKER_ENTROPY),
            ctypes.cast(
                ctypes.create_string_buffer(AGENTBREAKER_ENTROPY),
                ctypes.POINTER(ctypes.c_char),
            ),
        )
        data_out = DATA_BLOB()

        res = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(data_in),
            None,
            ctypes.byref(ent_in),
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(data_out),
        )
        if not res:
            err = ctypes.GetLastError()
            raise OSError(f"CryptUnprotectData failed with system error code {err}")

        try:
            return ctypes.string_at(data_out.pbData, data_out.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(data_out.pbData)

    def store_secret(self, key: str, secret: str) -> str:
        """Encrypt and persist secret with DPAPI."""
        clean_name = self._clean_key(key)
        target_file = self.storage_dir / f"{clean_name}.vault"
        encrypted_bytes = self._dpapi_protect(secret.encode("utf-8"))
        encoded = base64.b64encode(encrypted_bytes).decode("ascii")

        # Atomic write
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
        """Retrieve and decrypt secret using DPAPI."""
        if not credential_ref.startswith(self.SCHEME_PREFIX):
            return None
        clean_name = credential_ref[len(self.SCHEME_PREFIX) :]
        target_file = self.storage_dir / f"{clean_name}.vault"
        if not target_file.is_file():
            return None

        try:
            encoded = target_file.read_text(encoding="utf-8").strip()
            encrypted_bytes = base64.b64decode(encoded)
            decrypted_bytes = self._dpapi_unprotect(encrypted_bytes)
            return decrypted_bytes.decode("utf-8")
        except Exception:
            return None

    def delete_secret(self, credential_ref: str) -> bool:
        """Remove credential vault file."""
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
        """Check if credential vault file exists."""
        if not credential_ref.startswith(self.SCHEME_PREFIX):
            return False
        clean_name = credential_ref[len(self.SCHEME_PREFIX) :]
        return (self.storage_dir / f"{clean_name}.vault").is_file()
