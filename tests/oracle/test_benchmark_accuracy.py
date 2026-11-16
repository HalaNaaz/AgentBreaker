"""Ground-truth benchmark test validating Evaluation Oracle accuracy and false-positive rate."""

import json
from pathlib import Path

import pytest

from agentbreaker.attacks.loader import PayloadLoader
from agentbreaker.oracle.engine import EvaluationEngine
from agentbreaker.oracle.metrics import compute_oracle_metrics
from agentbreaker.schemas.enums import Verdict
from agentbreaker.schemas.target import TargetResponse


@pytest.mark.asyncio
async def test_oracle_accuracy_and_false_positive_rate_benchmark():
    """Verify Evaluation Oracle achieves >= 90% accuracy and < 8% false positive rate."""
    dataset_path = Path(__file__).parent / "benchmark_dataset.json"
    assert dataset_path.exists(), f"Benchmark dataset missing at {dataset_path}"

    with open(dataset_path, encoding="utf-8") as f:
        samples = json.load(f)

    assert len(samples) >= 50, f"Expected at least 50 benchmark samples, found {len(samples)}"

    # Load all payloads into an index by ID
    payloads_dir = Path("payloads")
    payloads = {p.id: p for p in PayloadLoader.load_from_directory(payloads_dir, recursive=True)}

    engine = EvaluationEngine()

    actual_verdicts: list[Verdict] = []
    predicted_verdicts: list[Verdict] = []
    mismatches = []

    for item in samples:
        pid = item["payload_id"]
        assert pid in payloads, f"Benchmark references unknown payload ID: {pid}"
        payload = payloads[pid]

        resp_dict = item["response"]
        response = TargetResponse(
            raw_content=resp_dict.get("raw_content", ""),
            status_code=resp_dict.get("status_code", 200),
            tool_calls=resp_dict.get("tool_calls", []),
            is_error=resp_dict.get("is_error", False),
            latency_ms=resp_dict.get("latency_ms", 50.0),
        )

        expected_verdict = Verdict(item["expected_verdict"])
        result = await engine.evaluate_async(
            payload=payload,
            response=response,
            canary_token=item.get("canary_token"),
        )
        predicted_verdict = result.verdict

        actual_verdicts.append(expected_verdict)
        predicted_verdicts.append(predicted_verdict)

        if predicted_verdict != expected_verdict:
            mismatches.append(
                {
                    "id": item["id"],
                    "description": item["description"],
                    "expected": expected_verdict.value,
                    "predicted": predicted_verdict.value,
                    "reasons": result.reasons,
                }
            )

    metrics = compute_oracle_metrics(actual_verdicts, predicted_verdicts)

    print("\n" + "=" * 60)
    print("EVALUATION ORACLE BENCHMARK METRICS (STRICT NON-CONFLATION)")
    print("=" * 60)
    print(f"Total Benchmark Samples: {metrics.total_samples}")
    print(
        f"Correct Predictions:     {metrics.correct_predictions}/{metrics.total_samples} "
        f"({metrics.accuracy:.2%})"
    )
    print(f"Overall Accuracy:        {metrics.accuracy:.4f} (PRD Target: >= 0.9000)")
    conclusive_ratio = f"{metrics.tp + metrics.tn}/{metrics.conclusive_samples}"
    print(f"Conclusive Accuracy:     {metrics.conclusive_accuracy:.4f} ({conclusive_ratio})")
    print(f"False Positive Rate:     {metrics.false_positive_rate:.4f} (PRD Target: < 0.0800)")
    print(f"False Negative Rate:     {metrics.false_negative_rate:.4f}")
    print(f"Precision:               {metrics.precision:.4f}")
    print(f"Recall:                  {metrics.recall:.4f}")
    print(f"F1-Score:                {metrics.f1_score:.4f}")
    print(
        f"Inconclusive Samples:    {metrics.inconclusive_actual} "
        f"(Correct: {metrics.inconclusive_correct})"
    )
    print(
        f"Binary Breakdown:        TP={metrics.tp}, TN={metrics.tn}, "
        f"FP={metrics.fp}, FN={metrics.fn}"
    )
    print("\nConfusion Matrix (Expected \\ Predicted):")
    for exp_v, preds in metrics.confusion_matrix.items():
        print(f"  {exp_v:<12} -> " + ", ".join(f"{pv}: {c}" for pv, c in preds.items()))
    print("=" * 60)

    if mismatches:
        print(f"Mismatches ({len(mismatches)}):")
        for m in mismatches:
            print(
                f"  {m['id']}: expected {m['expected']}, got {m['predicted']} ({m['description']})"
            )

    # Inconclusive samples must NEVER be silently counted as true negatives
    assert metrics.tn == 27, (
        f"Expected exactly 27 TN (Defended), got {metrics.tn}. Inconclusives were conflated!"
    )
    assert metrics.inconclusive_actual == 5, (
        f"Expected 5 inconclusive samples, got {metrics.inconclusive_actual}"
    )

    # Authoritative PRD assertions
    assert metrics.accuracy >= 0.90, f"Oracle accuracy {metrics.accuracy:.2%} fell below 90%"
    assert metrics.false_positive_rate < 0.08, (
        f"Oracle false positive rate {metrics.false_positive_rate:.2%} exceeded 8%"
    )
