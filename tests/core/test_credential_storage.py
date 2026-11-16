"""Unit, adversarial, and native OS integration tests for credential storage and migration."""

import base64
import concurrent.futures
import json
import logging
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from keyring.backend import KeyringBackend
from pydantic import SecretStr

from agentbreaker.cli.storage import StorageManager
from agentbreaker.core.credentials import (
    CredentialMigrator,
    POSIXCredentialStore,
    SecureStorageUnavailableError,
    WindowsDPAPICredentialStore,
    get_credential_store,
)
from agentbreaker.schemas.target import TargetConfig

# ===========================================================================
# 1. Windows Native DPAPI Integration Tests (Executed on Windows Hosts / CI)
# ===========================================================================


@pytest.mark.integration
@pytest.mark.windows
@pytest.mark.credential_storage
def test_windows_dpapi_store_lifecycle_on_windows(tmp_path: Path) -> None:
    """Verify Windows DPAPI store on Windows: protect, unprotect, restart, delete."""
    if os.name != "nt":
        pytest.skip("Windows DPAPI live test only executes on Windows hosts.")

    store = WindowsDPAPICredentialStore(tmp_path)
    key = "target/dpapi-openai"
    secret = "sk-dpapi-live-secret-test-998877"

    # Store
    ref = store.store_secret(key, secret)
    assert ref.startswith("vault://dpapi/")
    assert store.secret_exists(ref)

    # Retrieve
    retrieved = store.retrieve_secret(ref)
    assert retrieved == secret

    # Direct inspect ciphertext file on disk to guarantee it is NOT plaintext
    clean_name = store._clean_key(key)
    vault_file = store.storage_dir / f"{clean_name}.vault"
    assert vault_file.is_file()
    raw_disk_content = vault_file.read_text(encoding="utf-8")
    assert secret not in raw_disk_content

    # Simulate application restart with new store instance
    restarted_store = WindowsDPAPICredentialStore(tmp_path)
    assert restarted_store.retrieve_secret(ref) == secret

    # Delete
    assert restarted_store.delete_secret(ref) is True
    assert not restarted_store.secret_exists(ref)
    assert restarted_store.retrieve_secret(ref) is None


@pytest.mark.integration
@pytest.mark.windows
@pytest.mark.credential_storage
def test_windows_dpapi_invalid_ciphertext_and_missing(tmp_path: Path) -> None:
    """Verify DPAPI store returns None on corrupted or missing vault files."""
    if os.name != "nt":
        pytest.skip("Windows DPAPI live test only executes on Windows hosts.")

    store = WindowsDPAPICredentialStore(tmp_path)

    # Missing ref
    assert store.retrieve_secret("vault://dpapi/non_existent_key") is None
    assert store.delete_secret("vault://dpapi/non_existent_key") is False
    assert not store.secret_exists("vault://dpapi/non_existent_key")

    # Corrupted ciphertext
    corrupt_file = store.storage_dir / "corrupted_target.vault"
    corrupt_file.write_text("bm90LWV2ZW4tdmFsaWQtZHBhcGk=", encoding="utf-8")
    assert store.retrieve_secret("vault://dpapi/corrupted_target") is None


@pytest.mark.integration
@pytest.mark.windows
@pytest.mark.credential_storage
def test_windows_dpapi_binary_envelope_and_zero_plaintext(tmp_path: Path) -> None:
    """Verify DPAPI produces valid CryptProtectData binary envelope with zero plaintext."""
    if os.name != "nt":
        pytest.skip("Windows DPAPI live test only executes on Windows hosts.")

    store = WindowsDPAPICredentialStore(tmp_path)
    secret = "super_sensitive_api_token_value_xyz999"
    ref = store.store_secret("target/envelope_test", secret)
    assert ref.startswith("vault://dpapi/")

    clean_name = store._clean_key("target/envelope_test")
    vault_file = store.storage_dir / f"{clean_name}.vault"
    raw_text = vault_file.read_text(encoding="utf-8")

    # Plaintext must never appear in raw or decoded bytes
    assert secret not in raw_text
    decoded = base64.b64decode(raw_text)
    assert secret.encode("utf-8") not in decoded

    # Windows DPAPI structures start with DWORD dwVersion = 1 (\x01\x00\x00\x00)
    assert decoded[:4] == b"\x01\x00\x00\x00"
    assert len(decoded) > len(secret)


@pytest.mark.integration
@pytest.mark.windows
@pytest.mark.credential_storage
def test_windows_dpapi_unique_ciphertexts_per_secret(tmp_path: Path) -> None:
    """Verify distinct secrets produce distinct encrypted ciphertext outputs."""
    if os.name != "nt":
        pytest.skip("Windows DPAPI live test only executes on Windows hosts.")

    store = WindowsDPAPICredentialStore(tmp_path)
    ref_a = store.store_secret("target/sec_a", "secret_value_alpha")
    ref_b = store.store_secret("target/sec_b", "secret_value_beta")

    vault_a = store.storage_dir / f"{store._clean_key('target/sec_a')}.vault"
    vault_b = store.storage_dir / f"{store._clean_key('target/sec_b')}.vault"

    assert vault_a.read_text() != vault_b.read_text()
    assert store.retrieve_secret(ref_a) == "secret_value_alpha"
    assert store.retrieve_secret(ref_b) == "secret_value_beta"


# ===========================================================================
# 2. Linux Native Secret Service Integration Tests (Executed on Linux Hosts / CI)
# ===========================================================================


@pytest.mark.integration
@pytest.mark.linux
@pytest.mark.credential_storage
def test_linux_secret_service_store_lifecycle_live(tmp_path: Path) -> None:
    """Verify actual Linux Secret Service integration under an active D-Bus session."""
    if os.name == "nt":
        pytest.skip("Linux Secret Service integration test only executes on Linux.")

    import keyring

    backend = keyring.get_keyring()
    backend_cls = backend.__class__.__name__
    if "fail" in backend_cls.lower() or getattr(backend, "priority", 0) <= 0:
        pytest.skip(
            f"Active Secret Service provider unavailable (detected '{backend_cls}'). "
            "Run under dbus-run-session with an unlocked keyring to execute this test."
        )

    try:
        import secretstorage

        bus = secretstorage.dbus_init()
        collection = secretstorage.get_default_collection(bus)
        if collection.is_locked():
            pytest.skip(
                "Default Secret Service collection is locked. "
                "Run within an unlocked session (e.g. CI dbus-run-session with unlocked keyring) "
                "to execute live tests."
            )
    except Exception as exc:
        pytest.skip(f"Secret Service D-Bus connection unavailable: {exc}")

    store = POSIXCredentialStore(tmp_path)
    key = "target/live-linux-target"
    secret = "tgt_sec_linux_live_ci_validation_key_!@#"

    # Store
    ref = store.store_secret(key, secret)
    assert ref.startswith("vault://keyring/")
    assert store.secret_exists(ref) is True

    # Retrieve & Exact value equality
    retrieved = store.retrieve_secret(ref)
    assert retrieved == secret

    # Restart simulation (fresh store instance)
    restarted_store = POSIXCredentialStore(tmp_path)
    assert restarted_store.retrieve_secret(ref) == secret

    # Delete
    del_ok = restarted_store.delete_secret(ref)
    assert del_ok is True
    assert restarted_store.secret_exists(ref) is False
    assert restarted_store.retrieve_secret(ref) is None


@pytest.mark.integration
@pytest.mark.linux
@pytest.mark.credential_storage
def test_linux_secret_service_unavailable_fails_closed(tmp_path: Path) -> None:
    """Verify that when Secret Service is unavailable, POSIX store strictly fails closed."""
    from keyring.backends import fail

    fail_backend = fail.Keyring()

    # Instantiating store with fail backend MUST fail closed immediately
    with pytest.raises(SecureStorageUnavailableError) as exc_info:
        POSIXCredentialStore(tmp_path, keyring_backend=fail_backend)

    err_msg = str(exc_info.value)
    assert "No secure OS credential service available" in err_msg
    assert "Plaintext credential storage is strictly prohibited" in err_msg

    # Verify ZERO vault files or plaintext were written to disk
    cred_dir = tmp_path / ".credentials"
    if cred_dir.exists():
        vault_files = list(cred_dir.glob("*.vault"))
        assert len(vault_files) == 0, (
            f"Security violation: Fallback files created on disk: {vault_files}"
        )


# ===========================================================================
# 3. Deterministic Unit Tests (Mocked OS Keyring / Independent of Daemons)
# ===========================================================================


class MockKeyringBackend(KeyringBackend):
    """Mock OS Keyring backend simulating Linux SecretService or macOS Keychain."""

    priority = 5

    def __init__(self, name: str = "MockSecretService", priority: int = 5):
        self.__class__.__name__ = name
        self.priority = priority
        self.passwords: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.passwords[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        if (service, username) not in self.passwords:
            raise RuntimeError("Password not found")
        del self.passwords[(service, username)]


@pytest.mark.unit
@pytest.mark.credential_storage
def test_factory_selection_platform_appropriate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify get_credential_store selects Windows DPAPI on Windows and POSIX on Linux."""
    # Test Windows selection
    monkeypatch.setattr(os, "name", "nt")
    win_store = get_credential_store(tmp_path)
    assert isinstance(win_store, WindowsDPAPICredentialStore)

    # Test POSIX selection with mock backend
    mock_backend = MockKeyringBackend()
    import keyring

    monkeypatch.setattr(keyring, "get_keyring", lambda: mock_backend)
    monkeypatch.setattr(os, "name", "posix")
    posix_store = get_credential_store(tmp_path)
    assert isinstance(posix_store, POSIXCredentialStore)


@pytest.mark.unit
@pytest.mark.credential_storage
def test_keyring_store_linux_secret_service_mocked(tmp_path: Path) -> None:
    """Verify Linux Secret Service integration through mock OS keyring backend."""
    mock_backend = MockKeyringBackend(name="SecretServiceKeyring", priority=5)
    store = POSIXCredentialStore(tmp_path, keyring_backend=mock_backend)

    key = "target/linux-ollama"
    secret = "sk-linux-secret-service-token-112233"

    ref = store.store_secret(key, secret)
    assert ref.startswith("vault://keyring/")
    assert store.secret_exists(ref)

    assert store.retrieve_secret(ref) == secret
    assert store.delete_secret(ref) is True
    assert not store.secret_exists(ref)


@pytest.mark.unit
@pytest.mark.credential_storage
def test_keyring_store_macos_keychain_mocked(tmp_path: Path) -> None:
    """Verify macOS Keychain integration through mock OS keyring backend."""
    mock_backend = MockKeyringBackend(name="Keyring", priority=5)
    store = POSIXCredentialStore(tmp_path, keyring_backend=mock_backend)

    key = "target/macos-anthropic"
    secret = "sk-macos-keychain-token-445566"

    ref = store.store_secret(key, secret)
    assert ref.startswith("vault://keyring/")
    assert store.secret_exists(ref)

    assert store.retrieve_secret(ref) == secret
    assert store.delete_secret(ref) is True
    assert not store.secret_exists(ref)


@pytest.mark.unit
@pytest.mark.credential_storage
def test_keyring_missing_backend_fails_closed(tmp_path: Path) -> None:
    """Verify that POSIX store strictly fails closed if no secure backend is available."""
    fail_backend = MockKeyringBackend(name="fail.Keyring", priority=0)
    with pytest.raises(SecureStorageUnavailableError) as exc_info:
        POSIXCredentialStore(tmp_path, keyring_backend=fail_backend)._verify_backend()
    assert "No secure OS credential service available" in str(exc_info.value)
    assert "Plaintext credential storage is strictly prohibited" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.credential_storage
def test_keyring_locked_and_permission_failures_handled(tmp_path: Path) -> None:
    """Verify that locked keyrings or permission failures fail closed safely."""
    mock_backend = MagicMock()
    mock_backend.priority = 5
    mock_backend.__class__.__name__ = "SecretServiceKeyring"
    mock_backend.set_password.side_effect = PermissionError("User cancelled authentication prompt")

    store = POSIXCredentialStore(tmp_path, keyring_backend=mock_backend)
    with pytest.raises(SecureStorageUnavailableError) as exc_info:
        store.store_secret("target/locked", "some_secret")
    assert "Failed to securely store secret in OS keyring" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.credential_storage
def test_legacy_posix_scheme_backward_compatibility(tmp_path: Path) -> None:
    """Verify reading and deleting legacy vault://posix/ files during migration."""
    mock_backend = MockKeyringBackend()
    store = POSIXCredentialStore(tmp_path, keyring_backend=mock_backend)

    # Manually create legacy vault file on disk
    legacy_secret = "legacy-xor-machine-secret-999"
    clean_name = "target_legacy-target"
    legacy_file = store.storage_dir / f"{clean_name}.vault"
    key = store._derive_legacy_machine_key()
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(legacy_secret.encode("utf-8")))

    legacy_file.write_text(base64.b64encode(encrypted).decode("ascii"), encoding="utf-8")

    legacy_ref = f"vault://posix/{clean_name}"
    assert store.secret_exists(legacy_ref)
    assert store.retrieve_secret(legacy_ref) == legacy_secret

    assert store.delete_secret(legacy_ref) is True
    assert not store.secret_exists(legacy_ref)


@pytest.mark.unit
@pytest.mark.credential_storage
def test_credential_migrator_safely_migrates_legacy_json(tmp_path: Path) -> None:
    """Verify that legacy target JSON with plaintext api_key is migrated to vault."""
    mock_backend = MockKeyringBackend()
    store = (
        WindowsDPAPICredentialStore(tmp_path)
        if os.name == "nt"
        else POSIXCredentialStore(tmp_path, keyring_backend=mock_backend)
    )
    targets_dir = tmp_path / "targets"
    targets_dir.mkdir(parents=True)

    legacy_key = "sk-legacy-plaintext-key-0001"
    target_id = "legacy-target-1"
    json_path = targets_dir / f"{target_id}.json"

    # Write legacy target with raw api_key
    legacy_data: dict[str, Any] = {
        "_target_id": target_id,
        "endpoint_url": "http://127.0.0.1:11434/api/generate",
        "target_type": "ollama",
        "model_name": "llama3",
        "api_key": legacy_key,
        "timeout_seconds": 30.0,
        "max_concurrency": 5,
        "max_retries": 2,
    }
    json_path.write_text(json.dumps(legacy_data, indent=2))

    # Run migrator
    migrator = CredentialMigrator(targets_dir, store)
    report = migrator.migrate_all()

    assert report["scanned"] == 1
    assert report["migrated"] == 1
    assert report["failed"] == 0

    # Verify JSON on disk no longer contains plaintext api_key
    updated_disk_data = json.loads(json_path.read_text())
    assert "api_key" not in updated_disk_data
    assert "credential_ref" in updated_disk_data
    assert legacy_key not in json_path.read_text()

    # Verify secret is retrievable via credential_ref
    ref = updated_disk_data["credential_ref"]
    assert store.retrieve_secret(ref) == legacy_key

    # Idempotency check: running migrator again skips
    report2 = migrator.migrate_all()
    assert report2["scanned"] == 1
    assert report2["migrated"] == 0
    assert report2["skipped"] == 1


@pytest.mark.unit
@pytest.mark.credential_storage
def test_credential_migrator_interruption_and_retry(tmp_path: Path) -> None:
    """Verify migrator handles interrupted / corrupted files safely and allows retry."""
    mock_backend = MockKeyringBackend()
    store = (
        WindowsDPAPICredentialStore(tmp_path)
        if os.name == "nt"
        else POSIXCredentialStore(tmp_path, keyring_backend=mock_backend)
    )
    targets_dir = tmp_path / "targets"
    targets_dir.mkdir(parents=True)

    # Create an invalid non-JSON target file
    corrupt_path = targets_dir / "corrupt-target.json"
    corrupt_path.write_text("NOT_VALID_JSON{", encoding="utf-8")

    migrator = CredentialMigrator(targets_dir, store)
    report = migrator.migrate_all()
    assert report["scanned"] == 1
    assert report["migrated"] == 0
    assert report["skipped"] == 1  # Corrupt json handled safely without crash

    # Fix file and retry
    valid_data = {
        "_target_id": "corrupt-target",
        "endpoint_url": "http://127.0.0.1:11434/v1",
        "target_type": "ollama",
        "model_name": "llama3",
        "api_key": "sk-retry-migrated-secret-key",
    }
    corrupt_path.write_text(json.dumps(valid_data))
    report_retry = migrator.migrate_all()
    assert report_retry["scanned"] == 1
    assert report_retry["migrated"] == 1


@pytest.mark.unit
@pytest.mark.credential_storage
def test_credential_migrator_zero_secret_logging(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify that migration errors and telemetry NEVER disclose secret values in logs."""
    failing_store = MagicMock()
    failing_store.migrate_secret.side_effect = RuntimeError("Storage engine full")

    targets_dir = tmp_path / "targets"
    targets_dir.mkdir(parents=True)

    super_secret_value = "SECRET_VALUE_THAT_MUST_NEVER_APPEAR_IN_LOGS_9999"
    target_data = {
        "_target_id": "test-logger-target",
        "endpoint_url": "http://127.0.0.1:11434/v1",
        "target_type": "ollama",
        "model_name": "llama3",
        "api_key": super_secret_value,
    }
    (targets_dir / "test-logger.json").write_text(json.dumps(target_data))

    migrator = CredentialMigrator(targets_dir, failing_store)
    with caplog.at_level(logging.DEBUG):
        report = migrator.migrate_all()

    assert report["failed"] == 1
    assert super_secret_value not in caplog.text
    for err in report["errors"]:
        assert super_secret_value not in err


@pytest.mark.unit
@pytest.mark.credential_storage
def test_concurrent_credential_store_and_retrieve(tmp_path: Path) -> None:
    """Verify thread-safe concurrent storage operations."""
    store = get_credential_store(tmp_path)

    def worker(idx: int) -> bool:
        key = f"target/concurrent-{idx}"
        secret = f"secret-token-worker-{idx}"
        ref = store.store_secret(key, secret)
        retrieved = store.retrieve_secret(ref)
        return retrieved == secret

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, i) for i in range(16)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(results)
    assert len(results) == 16


@pytest.mark.unit
@pytest.mark.credential_storage
def test_storage_manager_save_and_get_target_zero_plaintext_on_disk(tmp_path: Path) -> None:
    """Verify StorageManager saves target without plaintext api_key and re-hydrates SecretStr."""
    storage_mgr = StorageManager(base_dir=tmp_path)
    target_id = "secure-target-alpha"
    test_key = "sk-vault-secret-token-xyz987"

    cfg = TargetConfig(
        endpoint_url="http://127.0.0.1:11434/api/generate",
        target_type="ollama",
        model_name="llama3",
        api_key=SecretStr(test_key),
    )

    storage_mgr.save_target(target_id, cfg)

    # 1. Inspect file on disk
    target_file = storage_mgr.targets_dir / f"{target_id}.json"
    assert target_file.is_file()
    disk_text = target_file.read_text(encoding="utf-8")
    assert test_key not in disk_text
    disk_json = json.loads(disk_text)
    assert "api_key" not in disk_json
    assert "credential_ref" in disk_json

    # 2. Retrieve via StorageManager (should re-hydrate SecretStr)
    loaded = storage_mgr.get_target(target_id)
    assert loaded is not None
    assert loaded.api_key is not None
    assert loaded.api_key.get_secret_value() == test_key

    # 3. Delete target
    assert storage_mgr.delete_target(target_id) is True
    assert not target_file.is_file()


@pytest.mark.unit
@pytest.mark.credential_storage
def test_storage_manager_credential_update_and_delete_lifecycle(tmp_path: Path) -> None:
    """Verify target credential update and deletion removes vault entry."""
    storage_mgr = StorageManager(base_dir=tmp_path)
    target_id = "lifecycle-target"
    secret_v1 = "initial_secret_token_111"
    secret_v2 = "updated_secret_token_222"

    # 1. Create target with secret_v1
    cfg_v1 = TargetConfig(
        endpoint_url="http://127.0.0.1:11434/v1",
        model_name="llama3",
        api_key=SecretStr(secret_v1),
    )
    storage_mgr.save_target(target_id, cfg_v1)

    t1 = storage_mgr.get_target(target_id)
    assert t1 is not None and t1.api_key is not None
    assert t1.api_key.get_secret_value() == secret_v1

    # 2. Update target with secret_v2
    cfg_v2 = TargetConfig(
        endpoint_url="http://127.0.0.1:11434/v1",
        model_name="llama3",
        api_key=SecretStr(secret_v2),
    )
    storage_mgr.save_target(target_id, cfg_v2)

    t2 = storage_mgr.get_target(target_id)
    assert t2 is not None and t2.api_key is not None
    assert t2.api_key.get_secret_value() == secret_v2

    # 3. Delete target
    assert storage_mgr.delete_target(target_id) is True
    assert storage_mgr.get_target(target_id) is None
    # Subsequent target retrieval returns None safely without raising
    assert storage_mgr.get_target(target_id) is None
