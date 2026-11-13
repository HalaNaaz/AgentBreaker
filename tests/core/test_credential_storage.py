"""Unit and security tests for OS-backed credential storage and legacy migration."""

import json
import os
from pathlib import Path

from pydantic import SecretStr

from agentbreaker.cli.storage import StorageManager
from agentbreaker.core.credentials import (
    CredentialMigrator,
    POSIXCredentialStore,
    WindowsDPAPICredentialStore,
    get_credential_store,
)
from agentbreaker.schemas.target import TargetConfig


def test_posix_credential_store_lifecycle(tmp_path: Path) -> None:
    """Verify store, retrieve, delete, and exists in POSIXCredentialStore."""
    store = POSIXCredentialStore(tmp_path)
    key = "target/mock-ollama"
    secret = "sk-posix-test-token-12345"

    # Store
    ref = store.store_secret(key, secret)
    assert ref.startswith("vault://posix/")
    assert store.secret_exists(ref)

    # Retrieve
    retrieved = store.retrieve_secret(ref)
    assert retrieved == secret

    # Delete
    deleted = store.delete_secret(ref)
    assert deleted is True
    assert not store.secret_exists(ref)
    assert store.retrieve_secret(ref) is None


def test_windows_dpapi_store_lifecycle_on_windows(tmp_path: Path) -> None:
    """Verify Windows DPAPI store on Windows or when crypt32 is available."""
    if os.name != "nt":
        return

    store = WindowsDPAPICredentialStore(tmp_path)
    key = "target/dpapi-openai"
    secret = "sk-dpapi-secret-key-998877"

    ref = store.store_secret(key, secret)
    assert ref.startswith("vault://dpapi/")
    assert store.secret_exists(ref)

    retrieved = store.retrieve_secret(ref)
    assert retrieved == secret

    # Direct inspect ciphertext file on disk to guarantee it is NOT plaintext
    clean_name = store._clean_key(key)
    vault_file = store.storage_dir / f"{clean_name}.vault"
    assert vault_file.is_file()
    raw_disk_content = vault_file.read_text()
    assert secret not in raw_disk_content

    # Delete
    assert store.delete_secret(ref) is True
    assert not store.secret_exists(ref)


def test_credential_migrator_safely_migrates_legacy_json(tmp_path: Path) -> None:
    """Verify that legacy target JSON with plaintext api_key is migrated to vault."""
    store = get_credential_store(tmp_path)
    targets_dir = tmp_path / "targets"
    targets_dir.mkdir(parents=True)

    legacy_key = "sk-legacy-plaintext-key-0001"
    target_id = "legacy-target-1"
    json_path = targets_dir / f"{target_id}.json"

    # Write legacy target with raw api_key
    legacy_data = {
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
