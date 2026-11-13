"""Comprehensive test suite for AgentBreaker Phase 6 CLI application."""

import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentbreaker import __version__
from agentbreaker.cli.main import app
from agentbreaker.schemas.target import TargetResponse

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate CLI storage to a temporary directory for every test."""
    monkeypatch.setenv("AGENTBREAKER_HOME", str(tmp_path))
    monkeypatch.setenv("COLUMNS", "200")
    return tmp_path


# ---------------------------------------------------------------------------
# 1. Root & Diagnostic Commands
# ---------------------------------------------------------------------------


def test_cli_version_flag() -> None:
    """Verify --version flag outputs version and framework title."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "AgentBreaker" in result.stdout
    assert __version__ in result.stdout


def test_cli_version_command() -> None:
    """Verify 'version' command executes cleanly."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "AgentBreaker" in result.stdout
    assert __version__ in result.stdout


def test_cli_help() -> None:
    """Verify --help displays available command groups."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "target" in result.stdout
    assert "payloads" in result.stdout
    assert "mutations" in result.stdout
    assert "assessment" in result.stdout
    assert "findings" in result.stdout
    assert "results" in result.stdout
    assert "config" in result.stdout


def test_cli_info() -> None:
    """Verify 'info' command displays platform diagnostics, storage paths, and providers."""
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Framework Version:" in result.stdout
    assert "Supported Target Providers" in result.stdout
    assert "Attack Categories" in result.stdout
    assert "Active Mutation Strategies" in result.stdout


# ---------------------------------------------------------------------------
# 2. Config Commands
# ---------------------------------------------------------------------------


def test_cli_config_show(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify config show masks API keys."""
    monkeypatch.setenv("AGENTBREAKER_API_KEY", "super-secret-production-key-12345")
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "super-secret-production-key-12345" not in result.stdout
    assert "sup...345" in result.stdout


def test_cli_config_validate() -> None:
    """Verify config validate checks environment parameters."""
    result = runner.invoke(app, ["config", "validate"])
    assert result.exit_code == 0
    assert "Platform configuration is valid" in result.stdout


def test_cli_config_path() -> None:
    """Verify config path outputs active storage and configuration paths."""
    result = runner.invoke(app, ["config", "path"])
    assert result.exit_code == 0
    assert "Storage Root:" in result.stdout
    assert "Targets Directory:" in result.stdout


# ---------------------------------------------------------------------------
# 3. Target Commands
# ---------------------------------------------------------------------------


def test_cli_target_lifecycle() -> None:
    """Verify full target management lifecycle: add, list, show, validate, remove."""
    # 1. Add valid target
    add_res = runner.invoke(
        app,
        [
            "target",
            "add",
            "--id",
            "test-llm",
            "--provider",
            "openai_compatible",
            "--url",
            "http://127.0.0.1:8000/v1/chat/completions",
            "--model",
            "gpt-4o-mini",
            "--api-key",
            "sk-secret-token-abcdef",
        ],
    )
    assert add_res.exit_code == 0
    assert "Target 'test-llm' successfully saved" in add_res.stdout

    # 2. List targets
    list_res = runner.invoke(app, ["target", "list"])
    assert list_res.exit_code == 0
    assert "test-llm" in list_res.stdout
    assert "gpt-4o-mini" in list_res.stdout

    # 3. Show target (verify secret is masked)
    show_res = runner.invoke(app, ["target", "show", "test-llm"])
    assert show_res.exit_code == 0
    assert "test-llm" in show_res.stdout
    assert "sk-secret-token-abcdef" not in show_res.stdout
    assert "sk-...def" in show_res.stdout

    # 4. Validate target
    val_res = runner.invoke(app, ["target", "validate", "test-llm"])
    assert val_res.exit_code == 0
    assert "is valid and adheres to security constraints" in val_res.stdout

    # 5. Remove target with confirmation
    rem_res = runner.invoke(app, ["target", "remove", "test-llm", "--confirm"])
    assert rem_res.exit_code == 0
    assert "Target 'test-llm' removed" in rem_res.stdout

    # Verify target is gone
    list_after = runner.invoke(app, ["target", "list"])
    assert "test-llm" not in list_after.stdout


def test_cli_target_test_mocked() -> None:
    """Verify 'target test' executes connector probe safely."""
    # Add target first
    runner.invoke(
        app,
        [
            "target",
            "add",
            "--id",
            "mock-target",
            "--provider",
            "ollama",
            "--url",
            "http://127.0.0.1:11434/api/generate",
            "--model",
            "llama3",
        ],
    )

    mock_conn = MagicMock()
    mock_conn.send_prompt = AsyncMock(
        return_value=TargetResponse(
            raw_content="pong",
            latency_ms=12.4,
            status_code=200,
        )
    )
    mock_conn.aclose = AsyncMock()

    with patch("agentbreaker.cli.commands.target.get_connector", return_value=mock_conn):
        res = runner.invoke(app, ["target", "test", "mock-target"])
        assert res.exit_code == 0
        assert "Successfully connected!" in res.stdout


def test_cli_target_errors() -> None:
    """Verify target error handling for non-existent and cancelled removals."""
    # Show non-existent
    res_not_found = runner.invoke(app, ["target", "show", "missing-id"])
    assert res_not_found.exit_code != 0
    assert "Target 'missing-id' not found" in res_not_found.output

    # Remove without confirm and declining
    runner.invoke(
        app,
        [
            "target",
            "add",
            "--id",
            "t1",
            "--provider",
            "ollama",
            "--url",
            "http://127.0.0.1:11434",
            "--model",
            "llama3",
        ],
    )
    res_declined = runner.invoke(app, ["target", "remove", "t1"], input="n\n")
    assert "Removal aborted" in res_declined.stdout


# ---------------------------------------------------------------------------
# 4. Payload Commands
# ---------------------------------------------------------------------------


def test_cli_payloads_list_and_filters() -> None:
    """Verify payload listing and filtering by category and severity."""
    # Full list
    res_all = runner.invoke(app, ["payloads", "list"])
    assert res_all.exit_code == 0
    assert "JB-001" in res_all.stdout
    assert "direct_jailbreak" in res_all.stdout

    # Filtered by category
    res_cat = runner.invoke(app, ["payloads", "list", "--category", "direct_jailbreak"])
    assert res_cat.exit_code == 0
    assert "JB-001" in res_cat.stdout
    assert "EXT-001" not in res_cat.stdout

    # Filtered by severity
    res_sev = runner.invoke(app, ["payloads", "list", "--severity", "CRITICAL"])
    assert res_sev.exit_code == 0
    assert "CRITICAL" in res_sev.stdout


def test_cli_payloads_show() -> None:
    """Verify 'payloads show' displays detailed payload metadata and content."""
    res = runner.invoke(app, ["payloads", "show", "JB-001"])
    assert res.exit_code == 0
    assert "JB-001" in res.stdout
    assert "Adversarial Hypothetical Scenario Jailbreak" in res.stdout
    assert "Payload Template:" in res.stdout


def test_cli_payloads_categories() -> None:
    """Verify 'payloads categories' displays summary statistics."""
    res = runner.invoke(app, ["payloads", "categories"])
    assert res.exit_code == 0
    assert "direct_jailbreak" in res.stdout
    assert "system_extraction" in res.stdout
    assert "indirect_injection" in res.stdout
    assert "tool_hijacking" in res.stdout


def test_cli_payloads_validate() -> None:
    """Verify 'payloads validate' confirms bundled vectors meet schema."""
    res = runner.invoke(app, ["payloads", "validate"])
    assert res.exit_code == 0
    assert "All" in res.stdout
    assert "validated successfully" in res.stdout


# ---------------------------------------------------------------------------
# 5. Mutation Commands
# ---------------------------------------------------------------------------


def test_cli_mutations_list_and_strategies() -> None:
    """Verify mutations list and strategies commands."""
    res_list = runner.invoke(app, ["mutations", "list"])
    assert res_list.exit_code == 0
    assert "rot13" in res_list.stdout
    assert "base64" in res_list.stdout

    res_strat = runner.invoke(app, ["mutations", "strategies"])
    assert res_strat.exit_code == 0
    assert "leetspeak" in res_strat.stdout
    assert "markdown_obfuscation" in res_strat.stdout


def test_cli_mutations_preview() -> None:
    """Verify mutation preview displays transformed content and preserves parent traceability."""
    res = runner.invoke(
        app,
        ["mutations", "preview", "JB-001", "--strategy", "rot13", "--seed", "42"],
    )
    assert res.exit_code == 0
    assert "Adversarial Mutation Preview" in res.stdout
    assert "Original Baseline Prompt Template" in res.stdout
    assert "RESEARCH DATA ONLY" in res.stdout


# ---------------------------------------------------------------------------
# 6. Assessment, Findings & Results Commands
# ---------------------------------------------------------------------------


def test_cli_assessment_lifecycle_and_run() -> None:
    """Verify creating, listing, running, and exporting an assessment."""
    # 1. Setup target
    runner.invoke(
        app,
        [
            "target",
            "add",
            "--id",
            "eval-target",
            "--provider",
            "openai_compatible",
            "--url",
            "http://127.0.0.1:8000/v1/chat/completions",
            "--model",
            "mock-llm",
        ],
    )

    # 2. Create assessment restricted to JB-001
    create_res = runner.invoke(
        app,
        [
            "assessment",
            "create",
            "--name",
            "Jailbreak Defense Audit",
            "--target",
            "eval-target",
            "--payload",
            "JB-001",
        ],
    )
    assert create_res.exit_code == 0
    assert "created successfully for target" in create_res.stdout
    # Extract assessment ID (format: ASM-XXXXXXXX)
    match = re.search(r"Assessment '(ASM-[0-9A-F]+)'", create_res.stdout)
    assert match is not None
    asm_id = match.group(1)

    # 3. List assessments
    list_res = runner.invoke(app, ["assessment", "list"])
    assert list_res.exit_code == 0
    assert asm_id in list_res.stdout

    # 4. Show assessment
    show_res = runner.invoke(app, ["assessment", "show", asm_id])
    assert show_res.exit_code == 0
    assert asm_id in show_res.stdout
    assert "eval-target" in show_res.stdout

    # 5. Run assessment with mocked connector returning refusal (DEFENDED verdict)
    mock_connector = MagicMock()
    mock_connector.initialize = AsyncMock()
    mock_connector.aclose = AsyncMock()
    mock_connector.send_prompt = AsyncMock(
        return_value=TargetResponse(
            raw_content="I cannot fulfill this request as it is against my safety guidelines.",
            latency_ms=35.0,
            status_code=200,
        )
    )

    with patch("agentbreaker.cli.orchestration.get_connector", return_value=mock_connector):
        run_res = runner.invoke(app, ["assessment", "run", asm_id])
        assert run_res.exit_code == 0
        assert "execution completed successfully" in run_res.stdout
        assert "Evaluation Outcome Summary" in run_res.stdout

    # 6. Results list and show
    res_list = runner.invoke(app, ["results", "list"])
    assert res_list.exit_code == 0
    assert asm_id in res_list.stdout

    res_show = runner.invoke(app, ["results", "show", asm_id])
    assert res_show.exit_code == 0
    assert asm_id in res_show.stdout

    # 7. Findings list and filter
    f_list = runner.invoke(app, ["findings", "list", "--assessment", asm_id])
    assert f_list.exit_code == 0
    assert "JB-001" in f_list.stdout

    f_filter = runner.invoke(app, ["findings", "filter", "--verdict", "DEFENDED"])
    assert f_filter.exit_code == 0
    assert "JB-001" in f_filter.stdout

    finding_id = f"{asm_id}_JB-001"
    f_show = runner.invoke(app, ["findings", "show", finding_id])
    assert f_show.exit_code == 0
    assert finding_id in f_show.stdout

    # 8. Results export (JSON & Markdown)
    json_export_path = Path("test_export.json")
    try:
        exp_json = runner.invoke(
            app,
            [
                "results",
                "export",
                asm_id,
                "--format",
                "json",
                "--output",
                str(json_export_path),
                "--overwrite",
            ],
        )
        assert exp_json.exit_code == 0
        assert json_export_path.exists()
        assert asm_id in json_export_path.read_text(encoding="utf-8")
    finally:
        if json_export_path.exists():
            json_export_path.unlink()

    md_export_path = Path("test_export.md")
    try:
        exp_md = runner.invoke(
            app,
            [
                "results",
                "export",
                asm_id,
                "--format",
                "markdown",
                "--output",
                str(md_export_path),
                "--overwrite",
            ],
        )
        assert exp_md.exit_code == 0
        assert md_export_path.exists()
        assert "# AgentBreaker Security Assessment Audit Report:" in md_export_path.read_text(
            encoding="utf-8"
        )
    finally:
        if md_export_path.exists():
            md_export_path.unlink()


def test_cli_assessment_cancel() -> None:
    """Verify assessment cancellation command."""
    runner.invoke(
        app,
        [
            "target",
            "add",
            "--id",
            "cancel-target",
            "--provider",
            "ollama",
            "--url",
            "http://127.0.0.1:11434",
            "--model",
            "m",
        ],
    )
    create_res = runner.invoke(
        app,
        [
            "assessment",
            "create",
            "--name",
            "Cancel Audit",
            "--target",
            "cancel-target",
        ],
    )
    match = re.search(r"Assessment '(ASM-[0-9A-F]+)'", create_res.stdout)
    assert match is not None
    asm_id = match.group(1)

    cancel_res = runner.invoke(app, ["assessment", "cancel", asm_id])
    assert cancel_res.exit_code == 0
    assert "marked as CANCELLED" in cancel_res.stdout
