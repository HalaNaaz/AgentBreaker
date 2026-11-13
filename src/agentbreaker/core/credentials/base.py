"""Base credential store abstraction for secure target secret persistence."""

from abc import ABC, abstractmethod


class BaseCredentialStore(ABC):
    """Abstract interface for OS-backed secure credential storage."""

    @abstractmethod
    def store_secret(self, key: str, secret: str) -> str:
        """Securely store a secret and return a canonical credential reference string.

        Args:
            key: Logical identifier (e.g., 'target/target-123').
            secret: Plaintext credential to store.

        Returns:
            credential_ref string (e.g., 'vault://dpapi/target/target-123').
        """

    @abstractmethod
    def retrieve_secret(self, credential_ref: str) -> str | None:
        """Retrieve and decrypt a stored secret given its credential reference.

        Args:
            credential_ref: Reference string returned by store_secret.

        Returns:
            Plaintext secret string, or None if not found or corrupted.
        """

    @abstractmethod
    def delete_secret(self, credential_ref: str) -> bool:
        """Delete a stored secret from the secure credential store.

        Args:
            credential_ref: Reference string of the secret to remove.

        Returns:
            True if deleted, False if not found.
        """

    @abstractmethod
    def secret_exists(self, credential_ref: str) -> bool:
        """Check whether a secret exists for the given reference without reading it."""

    def migrate_secret(self, key: str, legacy_secret: str) -> str:
        """Migrate a legacy plaintext credential into secure storage.

        Verifies storage retrieval before confirming migration.

        Args:
            key: Logical identifier.
            legacy_secret: Plaintext secret to migrate.

        Returns:
            Verified credential_ref.
        """
        ref = self.store_secret(key, legacy_secret)
        retrieved = self.retrieve_secret(ref)
        if retrieved != legacy_secret:
            raise RuntimeError(
                f"Credential migration verification failed for key '{key}'. "
                "Retrieved secret does not match source."
            )
        return ref
