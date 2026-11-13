"""AgentBreaker OS-backed secure credential storage and migration package."""

from agentbreaker.core.credentials.base import BaseCredentialStore
from agentbreaker.core.credentials.factory import get_credential_store
from agentbreaker.core.credentials.migrator import CredentialMigrator
from agentbreaker.core.credentials.posix import POSIXCredentialStore
from agentbreaker.core.credentials.windows import WindowsDPAPICredentialStore

__all__ = [
    "BaseCredentialStore",
    "CredentialMigrator",
    "POSIXCredentialStore",
    "WindowsDPAPICredentialStore",
    "get_credential_store",
]
