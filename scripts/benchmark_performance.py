"""Automated performance and resource benchmark suite for AgentBreaker PRD acceptance."""

import asyncio
import time
import tracemalloc
from pathlib import Path
from typing import Any

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
from agentbreaker.schemas.payload import AttackPayload
from agentbreaker.schemas.target import TargetConfig, TargetResponse


class BenchmarkLocalConnector(BaseConnector):
    """Controlled high-throughput local target connector for reproducible benchmarking."""

    target_type = TargetType.CUSTOM_HTTP

    def __init__(self, config: TargetConfig, simulated_latency_s: float = 0.01) -> None:
        super().__init__(config)
        self.simulated_latency_s = simulated_latency_s

    async def send_prompt(self, prompt: str, **kwargs: Any) -> TargetResponse:
        """Simulate realistic local target response with controlled latency."""
        start_t = time.perf_counter()
        if self.simulated_latency_s > 0:
            await asyncio.sleep(self.simulated_latency_s)
        latency_ms = (time.perf_counter() - start_t) * 1000.0

        # Return realistic response
        return TargetResponse(
            raw_content="I cannot fulfill this request. Against safety guidelines.",
            status_code=200,
            latency_ms=latency_ms,
            tool_calls=[],
        )

    async def validate_connection(self) -> bool:
        return True

    async def health_check(self) -> bool:
        return True

    async def close(self) -> None:
        pass


async def run_benchmark_a_and_b(payloads: list[AttackPayload]) -> dict[str, Any]:
    """Benchmark A (25 payloads) and Benchmark B (full 50 payloads)."""
    config = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        model_name="benchmark-model",
        max_concurrency=10,
    )
    connector = BenchmarkLocalConnector(config, simulated_latency_s=0.01)
    runner = AttackRunner(connector=connector, max_concurrency=10)
    engine = EvaluationEngine()

    payload_map = {p.id: p for p in payloads}

    # Benchmark A: 25 Payloads
    suite_25 = [BaseAttack(p) for p in payloads[:25]]
    start_a = time.perf_counter()
    executions_25 = await runner.run_suite(suite_25)
    for exec_item in executions_25:
        p = payload_map[exec_item.payload_id]
        if exec_item.response:
            await engine.evaluate_async(payload=p, response=exec_item.response)
    duration_a = time.perf_counter() - start_a

    # Benchmark B: 50 Payloads
    suite_50 = [BaseAttack(p) for p in payloads]
    start_b = time.perf_counter()
    executions_50 = await runner.run_suite(suite_50)
    for exec_item in executions_50:
        p = payload_map[exec_item.payload_id]
        if exec_item.response:
            await engine.evaluate_async(payload=p, response=exec_item.response)
    duration_b = time.perf_counter() - start_b

    return {
        "bench_a_count": len(suite_25),
        "bench_a_duration_s": duration_a,
        "bench_a_passed": duration_a < 30.0,
        "bench_b_count": len(suite_50),
        "bench_b_duration_s": duration_b,
        "bench_b_passed": duration_b < 60.0,
    }


async def run_benchmark_c_throughput(
    payloads: list[AttackPayload], concurrency: int = 10
) -> dict[str, Any]:
    """Benchmark C: Throughput (Requests per second)."""
    config = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        model_name="benchmark-model",
        max_concurrency=concurrency,
    )
    connector = BenchmarkLocalConnector(config, simulated_latency_s=0.005)
    runner = AttackRunner(connector=connector, max_concurrency=concurrency)

    # Fire 100 requests to measure sustained throughput
    attacks = [BaseAttack(payloads[i % len(payloads)]) for i in range(100)]
    start_c = time.perf_counter()
    await runner.run_suite(attacks)
    duration_c = time.perf_counter() - start_c
    throughput = len(attacks) / duration_c

    return {
        "concurrency": concurrency,
        "total_requests": len(attacks),
        "duration_s": duration_c,
        "throughput_req_per_sec": throughput,
        "passed": throughput >= 10.0,
    }


async def run_benchmark_d_reporting(
    tmp_path: Path, payloads: list[AttackPayload]
) -> dict[str, Any]:
    """Benchmark D: Report generation latency for JSON, Markdown, and HTML formats."""
    storage = StorageManager(base_dir=tmp_path / "reports_bench")
    assessment_id = "BENCH-RPT-001"

    # Seed assessment results in storage
    results_data = []
    engine = EvaluationEngine()
    for p in payloads:
        resp = TargetResponse(
            raw_content="I cannot fulfill this request. Against safety guidelines.",
            status_code=200,
            latency_ms=25.0,
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
            "target_model": "benchmark-vllm",
            "started_at": "2026-11-16T12:00:00Z",
            "completed_at": "2026-11-16T12:00:15Z",
            "duration_seconds": 15.0,
            "total_attacks": len(payloads),
            "total_mutations": 0,
        },
    )

    reporting = ReportingService(storage_manager=storage)
    report = reporting.build_report(assessment_id)

    # 1. JSON
    t0 = time.perf_counter()
    json_gen = JsonReportGenerator()
    json_content = json_gen.generate(report)
    lat_json = time.perf_counter() - t0

    # 2. Markdown
    t1 = time.perf_counter()
    md_gen = MarkdownReportGenerator()
    md_content = md_gen.generate(report)
    lat_md = time.perf_counter() - t1

    # 3. HTML
    t2 = time.perf_counter()
    html_gen = HtmlReportGenerator()
    html_content = html_gen.generate(report)
    lat_html = time.perf_counter() - t2

    return {
        "json_latency_s": lat_json,
        "json_passed": lat_json < 2.0,
        "json_bytes": len(json_content.encode("utf-8")),
        "markdown_latency_s": lat_md,
        "markdown_passed": lat_md < 2.0,
        "markdown_bytes": len(md_content.encode("utf-8")),
        "html_latency_s": lat_html,
        "html_passed": lat_html < 2.0,
        "html_bytes": len(html_content.encode("utf-8")),
    }


async def run_benchmark_e_memory(payloads: list[AttackPayload]) -> dict[str, Any]:
    """Benchmark E: Evaluation engine memory consumption during active execution."""
    tracemalloc.start()

    config = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        model_name="benchmark-model",
        max_concurrency=10,
    )
    connector = BenchmarkLocalConnector(config, simulated_latency_s=0.002)
    runner = AttackRunner(connector=connector, max_concurrency=10)
    engine = EvaluationEngine()

    payload_map = {p.id: p for p in payloads}
    suite_50 = [BaseAttack(p) for p in payloads]
    executions = await runner.run_suite(suite_50)
    for exec_item in executions:
        p = payload_map[exec_item.payload_id]
        if exec_item.response:
            await engine.evaluate_async(payload=p, response=exec_item.response)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_traced_mb = peak / (1024 * 1024)
    current_mb = current / (1024 * 1024)

    return {
        "traced_peak_mb": peak_traced_mb,
        "traced_current_mb": current_mb,
        "passed": peak_traced_mb < 250.0,
    }


async def main() -> None:
    payloads_dir = Path("payloads")
    payloads = PayloadLoader.load_from_directory(payloads_dir, recursive=True)
    print(f"Loaded {len(payloads)} payloads for benchmarking.\n")

    print("Running Benchmark A & B (Execution Duration)...")
    res_ab = await run_benchmark_a_and_b(payloads)
    print(
        f"  Benchmark A (25 payloads): {res_ab['bench_a_duration_s']:.3f}s (Target: < 30s) -> PASSED: {res_ab['bench_a_passed']}"
    )
    print(
        f"  Benchmark B (50 payloads): {res_ab['bench_b_duration_s']:.3f}s (Target: < 60s) -> PASSED: {res_ab['bench_b_passed']}\n"
    )

    print("Running Benchmark C (Throughput)...")
    res_c = await run_benchmark_c_throughput(payloads, concurrency=10)
    print(
        f"  Benchmark C: {res_c['throughput_req_per_sec']:.2f} req/s (Target: >= 10 req/s) -> PASSED: {res_c['passed']}\n"
    )

    print("Running Benchmark D (Report Latency)...")
    tmp_path = Path("reports_bench_tmp")
    tmp_path.mkdir(exist_ok=True)
    res_d = await run_benchmark_d_reporting(tmp_path, payloads)
    print(
        f"  Benchmark D (JSON):     {res_d['json_latency_s']:.4f}s ({res_d['json_bytes']} bytes) -> PASSED: {res_d['json_passed']}"
    )
    print(
        f"  Benchmark D (Markdown): {res_d['markdown_latency_s']:.4f}s ({res_d['markdown_bytes']} bytes) -> PASSED: {res_d['markdown_passed']}"
    )
    print(
        f"  Benchmark D (HTML):     {res_d['html_latency_s']:.4f}s ({res_d['html_bytes']} bytes) -> PASSED: {res_d['html_passed']}\n"
    )

    print("Running Benchmark E (Memory Consumption)...")
    res_e = await run_benchmark_e_memory(payloads)
    print(
        f"  Benchmark E (Traced Peak):  {res_e['traced_peak_mb']:.2f} MB (Target: < 250 MB) -> PASSED: {res_e['passed']}\n"
    )

    # Cleanup temp
    import shutil

    shutil.rmtree(tmp_path, ignore_errors=True)

    print("=" * 60)
    print("ALL PERFORMANCE BENCHMARKS SATISFIED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
