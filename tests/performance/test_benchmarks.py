"""Automated performance and resource benchmark tests validating PRD NFRs."""

import time
import tracemalloc
from pathlib import Path

import pytest

from agentbreaker.attacks.base import BaseAttack
from agentbreaker.attacks.loader import PayloadLoader
from agentbreaker.attacks.runner import AttackRunner
from agentbreaker.cli.storage import StorageManager
from agentbreaker.connectors.base import BaseConnector
from agentbreaker.oracle.engine import EvaluationEngine
from agentbreaker.reporting.generators.html_report import HtmlReportGenerator
from agentbreaker.reporting.generators.json_report import JsonReportGenerator
from agentbreaker.reporting.generators.markdown_report import MarkdownReportGenerator
from agentbreaker.reporting.service import ReportingService
from agentbreaker.schemas.enums import TargetType
from agentbreaker.schemas.target import TargetConfig, TargetResponse


class BenchmarkLocalConnector(BaseConnector):
    """High-throughput local test connector for performance benchmarks."""

    target_type = TargetType.CUSTOM_HTTP

    async def send_prompt(self, prompt: str, **kwargs) -> TargetResponse:
        return TargetResponse(
            raw_content="I cannot fulfill this request. Against safety guidelines.",
            status_code=200,
            latency_ms=1.0,
            tool_calls=[],
        )

    async def validate_connection(self) -> bool:
        return True

    async def health_check(self) -> bool:
        return True

    async def close(self) -> None:
        pass


@pytest.fixture
def bundled_payloads():
    payloads_dir = Path("payloads")
    return PayloadLoader.load_from_directory(payloads_dir, recursive=True)


@pytest.mark.asyncio
async def test_nfr_01_execution_duration_and_throughput(bundled_payloads):
    """Verify NFR-01 (25 payloads < 30s), PRD 17 (50 payloads < 60s), and Throughput >= 10 req/s."""
    config = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        model_name="benchmark-model",
        max_concurrency=10,
    )
    connector = BenchmarkLocalConnector(config)
    runner = AttackRunner(connector=connector, max_concurrency=10)
    engine = EvaluationEngine()
    payload_map = {p.id: p for p in bundled_payloads}

    # 1. Benchmark A: 25 payloads
    suite_25 = [BaseAttack(p) for p in bundled_payloads[:25]]
    start_25 = time.perf_counter()
    execs_25 = await runner.run_suite(suite_25)
    for item in execs_25:
        if item.response:
            await engine.evaluate_async(payload_map[item.payload_id], item.response)
    duration_25 = time.perf_counter() - start_25
    assert duration_25 < 30.0, f"25-payload execution took {duration_25:.2f}s, expected < 30s"

    # 2. Benchmark B: Full 50 payloads
    suite_50 = [BaseAttack(p) for p in bundled_payloads]
    start_50 = time.perf_counter()
    execs_50 = await runner.run_suite(suite_50)
    for item in execs_50:
        if item.response:
            await engine.evaluate_async(payload_map[item.payload_id], item.response)
    duration_50 = time.perf_counter() - start_50
    assert duration_50 < 60.0, f"50-payload execution took {duration_50:.2f}s, expected < 60s"

    # 3. Benchmark C: Throughput >= 10 req/s
    attacks_100 = [BaseAttack(bundled_payloads[i % len(bundled_payloads)]) for i in range(50)]
    start_tp = time.perf_counter()
    await runner.run_suite(attacks_100)
    duration_tp = time.perf_counter() - start_tp
    throughput = len(attacks_100) / duration_tp
    assert throughput >= 10.0, f"Throughput was {throughput:.2f} req/s, expected >= 10 req/s"


@pytest.mark.asyncio
async def test_nfr_06_memory_consumption(bundled_payloads):
    """Verify NFR-06: Evaluation engine memory consumption remains < 250 MB RAM."""
    tracemalloc.start()
    config = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        model_name="benchmark-model",
        max_concurrency=10,
    )
    connector = BenchmarkLocalConnector(config)
    runner = AttackRunner(connector=connector, max_concurrency=10)
    engine = EvaluationEngine()
    payload_map = {p.id: p for p in bundled_payloads}

    suite_50 = [BaseAttack(p) for p in bundled_payloads]
    execs_50 = await runner.run_suite(suite_50)
    for item in execs_50:
        if item.response:
            await engine.evaluate_async(payload_map[item.payload_id], item.response)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    assert peak_mb < 250.0, f"Evaluation memory peak {peak_mb:.2f} MB exceeded 250 MB threshold"


@pytest.mark.asyncio
async def test_report_generation_latency(tmp_path, bundled_payloads):
    """Verify report generation latency is < 2.0 seconds post-run across formats."""
    storage = StorageManager(base_dir=tmp_path / "reports")
    assessment_id = "BENCH-TEST-RPT"
    engine = EvaluationEngine()

    results_data = []
    for p in bundled_payloads:
        resp = TargetResponse(
            raw_content="I cannot fulfill this request.",
            status_code=200,
            latency_ms=10.0,
            tool_calls=[],
        )
        res = await engine.evaluate_async(p, resp)
        results_data.append(res)

    storage.save_results(
        assessment_id=assessment_id,
        results=results_data,
        metadata={
            "assessment_id": assessment_id,
            "target_id": "TGT-BENCH",
            "target_provider": "local",
            "target_model": "benchmark-model",
            "started_at": "2026-11-16T12:00:00Z",
            "completed_at": "2026-11-16T12:00:05Z",
            "duration_seconds": 5.0,
            "total_attacks": len(bundled_payloads),
            "total_mutations": 0,
        },
    )

    reporting = ReportingService(storage_manager=storage)
    report = reporting.build_report(assessment_id)

    # 1. JSON
    t0 = time.perf_counter()
    json_out = JsonReportGenerator().generate(report)
    lat_json = time.perf_counter() - t0
    assert lat_json < 2.0
    assert len(json_out) > 0

    # 2. Markdown
    t1 = time.perf_counter()
    md_out = MarkdownReportGenerator().generate(report)
    lat_md = time.perf_counter() - t1
    assert lat_md < 2.0
    assert len(md_out) > 0

    # 3. HTML
    t2 = time.perf_counter()
    html_out = HtmlReportGenerator().generate(report)
    lat_html = time.perf_counter() - t2
    assert lat_html < 2.0
    assert len(html_out) > 0
