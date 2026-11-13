"""Factory for obtaining the platform-appropriate secure credential store."""

import os
from pathlib import Path

from agentbreaker.core.credentials.base import BaseCredentialStore
from agentbreaker.core.credentials.posix import POSIXCredentialStore
from agentbreaker.core.credentials.windows import WindowsDPAPICredentialStore


def get_credential_store(base_dir: Path | None = None) -> BaseCredentialStore:
    """Instantiate the secure credential store appropriate for the host OS.

    On Windows, uses Windows DPAPI (CryptProtectData).
    On POSIX (Linux/macOS), uses POSIXCredentialStore.
    """
    target_dir = base_dir or Path(".agentbreaker")
    if os.name == "nt":
        try:
            return WindowsDPAPICredentialStore(target_dir)
        except Exception:
            # Fallback to file-isolated store if DPAPI ctypes fails
            return POSIXCredentialStore(target_dir)
    return POSIXCredentialStore(target_dir)
