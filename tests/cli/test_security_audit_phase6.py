"""Independent security and integration audit verification tests for Phase 6 CLI."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentbreaker.cli.main import app
from agentbreaker.cli.orchestration import AssessmentOrchestrator
from agentbreaker.cli.storage import StorageManager
from agentbreaker.schemas.enums import TargetType, Verdict
from agentbreaker.schemas.target import TargetConfig, TargetResponse

runner = CliRunner()


@pytest.fixture
def clean_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> StorageManager:
    """Isolate CLI storage environment."""
    monkeypatch.setenv("AGENTBREAKER_HOME", str(tmp_path))
    monkeypatch.setenv("COLUMNS", "200")
    return StorageManager(tmp_path)


# ===========================================================================
# 1. Path Traversal & Storage Boundary Protection
# ===========================================================================


def test_audit_path_traversal_rejection(clean_storage: StorageManager) -> None:
    """Verify that path traversal sequences in target and assessment IDs are rejected."""
    cfg = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        target_type=TargetType.OPENAI_COMPATIBLE,
        model_name="mock-model",
    )

    # Malicious target identifiers
    traversal_ids = ["../traversal", "../../evil", "evil/path", "evil\\path", "...", ""]
    for bad_id in traversal_ids:
        with pytest.raises(ValueError, match="(forbidden|cannot be empty|only alphanumeric)"):
            clean_storage.save_target(bad_id, cfg)

        # get_target returns None safely
        assert clean_storage.get_target(bad_id) is None
        # delete_target returns False safely
        assert clean_storage.delete_target(bad_id) is False

    # Verify no file escaped outside targets_dir
    escaped = clean_storage.root / "traversal.json"
    assert not escaped.exists()


def test_audit_assessment_path_traversal(clean_storage: StorageManager) -> None:
    """Verify that assessment storage rejects path traversal sequences."""
    bad_assessment = {"id": "../evil_asm", "name": "bad"}
    with pytest.raises(ValueError, match="path separators and '..' are forbidden"):
        clean_storage.save_assessment(bad_assessment)

    assert clean_storage.get_assessment("../evil_asm") is None
    assert clean_storage.get_results("../evil_asm") is None


# ===========================================================================
# 2. Secret Redaction & Safe API Key Injection
# ===========================================================================


def test_audit_api_key_env_support(
    clean_storage: StorageManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that API keys can be passed via environment variables to avoid history exposure."""
    secret_key = "sk-live-super-secret-key-9999"
    monkeypatch.setenv("MY_TARGET_API_KEY", secret_key)

    res = runner.invoke(
        app,
        [
            "target",
            "add",
            "--id",
            "secure-target",
            "--provider",
            "openai_compatible",
            "--url",
            "http://127.0.0.1:8000/v1",
            "--model",
            "gpt-4o",
            "--api-key-env",
            "MY_TARGET_API_KEY",
        ],
    )
    assert res.exit_code == 0
    assert "successfully saved" in res.stdout

    # Verify key is loaded into stored configuration
    stored = clean_storage.get_target("secure-target")
    assert stored is not None
    assert stored.api_key is not None
    assert stored.api_key.get_secret_value() == secret_key

    # Verify target show NEVER outputs the full key
    show_res = runner.invoke(app, ["target", "show", "secure-target"])
    assert show_res.exit_code == 0
    assert secret_key not in show_res.stdout
    assert "sk-...999" in show_res.stdout


def test_audit_secret_never_exposed_in_exports(
    clean_storage: StorageManager, tmp_path: Path
) -> None:
    """Verify that evaluation results exports do not contain API keys."""
    # Setup target with secret key
    secret_key = "sk-secret-confidential-0000"
    cfg = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        target_type=TargetType.OPENAI_COMPATIBLE,
        model_name="mock-model",
        api_key=secret_key,
    )
    clean_storage.save_target("exp-target", cfg)

    # Save mock results
    from agentbreaker.schemas.enums import AttackCategory, Severity
    from agentbreaker.schemas.result import EvaluationResult

    mock_result = EvaluationResult(
        payload_id="JB-001",
        category=AttackCategory.DIRECT_JAILBREAK,
        severity=Severity.HIGH,
        verdict=Verdict.DEFENDED,
        confidence=0.95,
        cvss_score=7.5,
    )
    clean_storage.save_results(
        "ASM-EXPAUDIT",
        [mock_result],
        metadata={"target_id": "exp-target", "completed_at": "2026-11-10T00:00:00Z"},
    )

    # Export to JSON
    json_path = tmp_path / "audit_export.json"
    runner.invoke(
        app,
        ["results", "export", "ASM-EXPAUDIT", "-f", "json", "-o", str(json_path), "-y"],
    )
    assert json_path.exists()
    content = json_path.read_text(encoding="utf-8")
    assert secret_key not in content

    # Export to Markdown
    md_path = tmp_path / "audit_export.md"
    runner.invoke(
        app,
        ["results", "export", "ASM-EXPAUDIT", "-f", "markdown", "-o", str(md_path), "-y"],
    )
    assert md_path.exists()
    md_content = md_path.read_text(encoding="utf-8")
    assert secret_key not in md_content


# ===========================================================================
# 3. Target Authorization & Boundary Verification
# ===========================================================================


def test_audit_unapproved_target_rejection(clean_storage: StorageManager) -> None:
    """Verify that an assessment configured for an missing target fails immediately."""
    orchestrator = AssessmentOrchestrator()
    bad_config = {
        "id": "ASM-UNAPPROVED",
        "target_id": "non_existent_target",
    }
    with pytest.raises(ValueError, match="is not configured in local storage"):
        asyncio.run(orchestrator.execute_assessment(bad_config))


def test_audit_target_cloud_metadata_rejection() -> None:
    """Verify that target URLs pointing to metadata IP are rejected by schema."""
    with pytest.raises(Exception, match="restricted"):
        TargetConfig(
            endpoint_url="http://169.254.169.254/latest/meta-data/",
            target_type=TargetType.CUSTOM_HTTP,
            model_name="metadata-probe",
        )


# ===========================================================================
# 4. Mutation Opt-In & Lineage Preservation
# ===========================================================================


def test_audit_mutation_opt_in_strictly_enforced(clean_storage: StorageManager) -> None:
    """Verify that mutation variants are NEVER dispatched unless enable_mutation=True."""
    # Setup target
    cfg = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        target_type=TargetType.OPENAI_COMPATIBLE,
        model_name="mock-model",
    )
    clean_storage.save_target("mut-target", cfg)

    # Mock connector
    mock_conn = MagicMock()
    mock_conn.initialize = AsyncMock()
    mock_conn.aclose = AsyncMock()
    mock_conn.send_prompt = AsyncMock(
        return_value=TargetResponse(raw_content="I refuse.", status_code=200)
    )

    with patch("agentbreaker.cli.orchestration.get_connector", return_value=mock_conn):
        orchestrator = AssessmentOrchestrator()
        # Assessment with mutation disabled (default)
        asm_cfg_no_mut = {
            "id": "ASM-NOMUT",
            "target_id": "mut-target",
            "selected_payloads": ["JB-001"],
            "enable_mutation": False,
        }
        results, summary = asyncio.run(orchestrator.execute_assessment(asm_cfg_no_mut))
        assert summary["total_payloads"] == 1
        assert len(results) == 1
        assert results[0].parent_id is None  # Baseline payload, no parent

        # Assessment with mutation explicitly enabled
        asm_cfg_mut = {
            "id": "ASM-WITHMUT",
            "target_id": "mut-target",
            "selected_payloads": ["JB-001"],
            "enable_mutation": True,
            "mutation_strategies": ["rot13"],
            "max_variants_per_payload": 1,
        }
        results_mut, summary_mut = asyncio.run(orchestrator.execute_assessment(asm_cfg_mut))
        assert summary_mut["total_payloads"] == 2  # 1 baseline + 1 variant
        assert len(results_mut) == 2
        # Verify lineage: variant has parent_id == 'JB-001'
        variant_res = next(r for r in results_mut if r.parent_id is not None)
        assert variant_res.parent_id == "JB-001"


# ===========================================================================
# 5. Inert Tool Call Safety
# ===========================================================================


def test_audit_model_generated_tool_calls_remain_inert(clean_storage: StorageManager) -> None:
    """Verify that model-generated tool calls are strictly static data and never executed."""
    cfg = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        target_type=TargetType.OPENAI_COMPATIBLE,
        model_name="mock-model",
    )
    clean_storage.save_target("tool-target", cfg)

    # Model attempts malicious tool invocation
    malicious_tool_call = {
        "id": "call_123",
        "type": "function",
        "function": {
            "name": "run_shell",
            "arguments": '{"command": "rm -rf /"}',
        },
    }

    mock_conn = MagicMock()
    mock_conn.initialize = AsyncMock()
    mock_conn.aclose = AsyncMock()
    mock_conn.send_prompt = AsyncMock(
        return_value=TargetResponse(
            raw_content="Executing system command...",
            status_code=200,
            tool_calls=[malicious_tool_call],
        )
    )

    with patch("agentbreaker.cli.orchestration.get_connector", return_value=mock_conn):
        orchestrator = AssessmentOrchestrator()
        asm_cfg = {
            "id": "ASM-TOOLTEST",
            "target_id": "tool-target",
            "selected_payloads": ["TOOL-001"],
            "enable_mutation": False,
        }
        results, summary = asyncio.run(orchestrator.execute_assessment(asm_cfg))
        assert len(results) == 1
        res = results[0]
        # Oracle detects forbidden tool call and flags it as VULNERABLE
        assert res.verdict == Verdict.VULNERABLE


# ===========================================================================
# 6. Malformed Storage Recovery & Resilience
# ===========================================================================


def test_audit_malformed_storage_files_fail_safely(clean_storage: StorageManager) -> None:
    """Verify that corrupt or non-JSON files in storage directories are handled safely."""
    # Write garbage to targets dir
    corrupt_target_file = clean_storage.targets_dir / "corrupted.json"
    corrupt_target_file.write_text("{broken json syntax...!", encoding="utf-8")

    # get_target returns None without crashing
    assert clean_storage.get_target("corrupted") is None

    # list_targets ignores corrupt target
    targets = clean_storage.list_targets()
    assert "corrupted" not in targets

    # Write garbage to assessments dir
    corrupt_asm_file = clean_storage.assessments_dir / "corrupted.json"
    corrupt_asm_file.write_text("NOT_JSON", encoding="utf-8")
    assert clean_storage.get_assessment("corrupted") is None
    assert len(clean_storage.list_assessments()) == 0


# ===========================================================================
# 7. Atomic Writes & Concurrency
# ===========================================================================


def test_audit_concurrent_atomic_writes(clean_storage: StorageManager) -> None:
    """Verify that concurrent writes to storage do not corrupt JSON files."""
    cfg = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        target_type=TargetType.OPENAI_COMPATIBLE,
        model_name="mock-model",
    )

    def _worker(thread_idx: int) -> None:
        target_id = f"concurrent_target_{thread_idx}"
        clean_storage.save_target(target_id, cfg)
        retrieved = clean_storage.get_target(target_id)
        assert retrieved is not None
        assert retrieved.model_name == "mock-model"

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_worker, i) for i in range(16)]
        for f in futures:
            f.result()

    targets = clean_storage.list_targets()
    assert len(targets) == 16


# ===========================================================================
# 8. Partial Results Survivability & Cancellation
# ===========================================================================


def test_audit_partial_results_on_error(clean_storage: StorageManager) -> None:
    """Verify that target HTTP 500 errors produce INCONCLUSIVE records and do not crash suite."""
    cfg = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        target_type=TargetType.OPENAI_COMPATIBLE,
        model_name="mock-model",
    )
    clean_storage.save_target("error-target", cfg)

    # Connector returns error response
    mock_conn = MagicMock()
    mock_conn.initialize = AsyncMock()
    mock_conn.aclose = AsyncMock()
    mock_conn.send_prompt = AsyncMock(
        return_value=TargetResponse(
            raw_content="",
            status_code=500,
            is_error=True,
            error_message="Internal Server Error: model failed to generate",
        )
    )

    with patch("agentbreaker.cli.orchestration.get_connector", return_value=mock_conn):
        orchestrator = AssessmentOrchestrator()
        asm_cfg = {
            "id": "ASM-ERRORSUITE",
            "target_id": "error-target",
            "selected_payloads": ["JB-001"],
            "enable_mutation": False,
        }
        results, summary = asyncio.run(orchestrator.execute_assessment(asm_cfg))
        assert len(results) == 1
        assert results[0].verdict == Verdict.INCONCLUSIVE
        assert summary["inconclusive_count"] == 1
        assert summary["status"] == "COMPLETED"


def test_audit_cancellation_closes_connector(clean_storage: StorageManager) -> None:
    """Verify that canceling an assessment closes connector and cleans up resources."""
    orchestrator = AssessmentOrchestrator()
    mock_runner = MagicMock()
    orchestrator.runner = mock_runner
    orchestrator.cancel()
    mock_runner.cancel.assert_called_once()
