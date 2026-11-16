"""Unit tests validating Evaluation Oracle metric calculations and edge cases.

Verifies mathematical soundness of multi-class and binary metrics,
including zero denominators, empty datasets, all-positive/all-negative distributions,
and strict non-conflation of inconclusive verdicts with true negatives.
"""

import pytest

from agentbreaker.oracle.metrics import compute_oracle_metrics
from agentbreaker.schemas.enums import Verdict


class TestOracleMetricsCalculations:
    """Test suite for compute_oracle_metrics and edge cases."""

    def test_empty_dataset(self) -> None:
        """Empty input sequences must return zeroed metrics without ZeroDivisionError."""
        metrics = compute_oracle_metrics([], [])
        assert metrics.total_samples == 0
        assert metrics.correct_predictions == 0
        assert metrics.accuracy == 0.0
        assert metrics.tp == 0
        assert metrics.tn == 0
        assert metrics.fp == 0
        assert metrics.fn == 0
        assert metrics.conclusive_samples == 0
        assert metrics.conclusive_accuracy == 0.0
        assert metrics.false_positive_rate == 0.0
        assert metrics.false_negative_rate == 0.0
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0
        assert metrics.f1_score == 0.0

    def test_length_mismatch_raises_value_error(self) -> None:
        """Mismatched sequence lengths must raise ValueError."""
        with pytest.raises(ValueError, match="Length mismatch"):
            compute_oracle_metrics([Verdict.VULNERABLE], [])

    def test_all_positive_dataset_all_correct(self) -> None:
        """All-positive dataset (all actual VULNERABLE) with perfect predictions."""
        actuals = [Verdict.VULNERABLE] * 10
        predictions = [Verdict.VULNERABLE] * 10

        metrics = compute_oracle_metrics(actuals, predictions)

        assert metrics.total_samples == 10
        assert metrics.correct_predictions == 10
        assert metrics.accuracy == 1.0
        assert metrics.tp == 10
        assert metrics.tn == 0
        assert metrics.fp == 0
        assert metrics.fn == 0
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0
        # Zero denominator for FPR (FP + TN == 0): must safely be 0.0
        assert metrics.false_positive_rate == 0.0
        assert metrics.false_negative_rate == 0.0

    def test_all_positive_dataset_mixed_predictions(self) -> None:
        """All-positive dataset with 7 TP, 2 FN (Defended), and 1 predicted Inconclusive."""
        actuals = [Verdict.VULNERABLE] * 10
        predictions = [Verdict.VULNERABLE] * 7 + [Verdict.DEFENDED] * 2 + [Verdict.INCONCLUSIVE] * 1

        metrics = compute_oracle_metrics(actuals, predictions)

        assert metrics.total_samples == 10
        assert metrics.correct_predictions == 7
        assert metrics.accuracy == 0.7
        assert metrics.tp == 7
        assert metrics.fn == 2
        assert metrics.vuln_as_inconclusive == 1
        assert metrics.tn == 0
        assert metrics.fp == 0
        # FNR = FN / (TP + FN) = 2 / (7 + 2) = 2/9
        assert pytest.approx(metrics.false_negative_rate, abs=1e-4) == 2 / 9
        # Recall = 7 / 9
        assert pytest.approx(metrics.recall, abs=1e-4) == 7 / 9
        # FPR is safely 0.0 since FP + TN == 0
        assert metrics.false_positive_rate == 0.0

    def test_all_negative_dataset_all_correct(self) -> None:
        """All-negative dataset (all actual DEFENDED) with perfect predictions."""
        actuals = [Verdict.DEFENDED] * 10
        predictions = [Verdict.DEFENDED] * 10

        metrics = compute_oracle_metrics(actuals, predictions)

        assert metrics.total_samples == 10
        assert metrics.correct_predictions == 10
        assert metrics.accuracy == 1.0
        assert metrics.tp == 0
        assert metrics.tn == 10
        assert metrics.fp == 0
        assert metrics.fn == 0
        assert metrics.false_positive_rate == 0.0
        # Zero denominator for precision/recall (TP + FP == 0, TP + FN == 0)
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0
        assert metrics.f1_score == 0.0

    def test_all_negative_dataset_with_false_positive(self) -> None:
        """All-negative dataset with 8 TN, 2 FP."""
        actuals = [Verdict.DEFENDED] * 10
        predictions = [Verdict.DEFENDED] * 8 + [Verdict.VULNERABLE] * 2

        metrics = compute_oracle_metrics(actuals, predictions)

        assert metrics.total_samples == 10
        assert metrics.correct_predictions == 8
        assert metrics.accuracy == 0.8
        assert metrics.tp == 0
        assert metrics.tn == 8
        assert metrics.fp == 2
        assert metrics.fn == 0
        # FPR = FP / (FP + TN) = 2 / (2 + 8) = 0.20
        assert metrics.false_positive_rate == 0.20
        assert metrics.precision == 0.0

    def test_inconclusive_samples_not_counted_as_true_negatives(self) -> None:
        """CRITICAL: Inconclusive samples must NEVER increment TN or dilute FPR."""
        # 5 actual DEFENDED, 5 actual INCONCLUSIVE
        actuals = [Verdict.DEFENDED] * 5 + [Verdict.INCONCLUSIVE] * 5
        # Predictions: 4 DEFENDED correct, 1 FP (DEFENDED predicted VULNERABLE);
        # 5 INCONCLUSIVE predicted INCONCLUSIVE.
        predictions = [Verdict.DEFENDED] * 4 + [Verdict.VULNERABLE] * 1 + [Verdict.INCONCLUSIVE] * 5

        metrics = compute_oracle_metrics(actuals, predictions)

        # Verification of exact class accounting
        assert metrics.total_samples == 10
        assert metrics.correct_predictions == 9  # 4 Defended + 5 Inconclusive
        assert metrics.accuracy == 0.9

        # Crucial check: TN must be 4, NOT 9!
        assert metrics.tn == 4, f"Expected TN=4, got {metrics.tn}. Inconclusives were conflated!"
        assert metrics.fp == 1
        assert metrics.inconclusive_actual == 5
        assert metrics.inconclusive_correct == 5

        # FPR must be FP / (FP + TN) = 1 / (1 + 4) = 0.20 (20%)
        # If inconclusive samples were counted as TN, FPR would incorrectly dilute to 1/10
        assert metrics.false_positive_rate == 0.20

    def test_mixed_dataset_comprehensive(self) -> None:
        """Comprehensive mixed scenario with all transitions and verdicts."""
        actuals = [
            Verdict.VULNERABLE,  # TP
            Verdict.VULNERABLE,  # TP
            Verdict.VULNERABLE,  # FN (predicted DEFENDED)
            Verdict.VULNERABLE,  # vuln_as_inconclusive
            Verdict.DEFENDED,  # TN
            Verdict.DEFENDED,  # TN
            Verdict.DEFENDED,  # FP (predicted VULNERABLE)
            Verdict.DEFENDED,  # defended_as_inconclusive
            Verdict.INCONCLUSIVE,  # inconclusive_correct
            Verdict.INCONCLUSIVE,  # inconclusive_as_vuln
            Verdict.INCONCLUSIVE,  # inconclusive_as_defended
        ]
        predictions = [
            Verdict.VULNERABLE,  # TP
            Verdict.VULNERABLE,  # TP
            Verdict.DEFENDED,  # FN
            Verdict.INCONCLUSIVE,  # vuln_as_inc
            Verdict.DEFENDED,  # TN
            Verdict.DEFENDED,  # TN
            Verdict.VULNERABLE,  # FP
            Verdict.INCONCLUSIVE,  # def_as_inc
            Verdict.INCONCLUSIVE,  # inc_correct
            Verdict.VULNERABLE,  # inc_as_vuln
            Verdict.DEFENDED,  # inc_as_def
        ]

        metrics = compute_oracle_metrics(actuals, predictions)

        assert metrics.total_samples == 11
        # Correct: 2 VULN + 2 DEF + 1 INC = 5
        assert metrics.correct_predictions == 5
        assert pytest.approx(metrics.accuracy, abs=1e-4) == 5 / 11

        assert metrics.tp == 2
        assert metrics.fn == 1
        assert metrics.vuln_as_inconclusive == 1

        assert metrics.tn == 2
        assert metrics.fp == 1
        assert metrics.defended_as_inconclusive == 1

        assert metrics.inconclusive_actual == 3
        assert metrics.inconclusive_correct == 1
        assert metrics.inconclusive_as_vuln == 1
        assert metrics.inconclusive_as_defended == 1

        # Binary rates
        # FPR = FP / (FP + TN) = 1 / (1 + 2) = 1/3
        assert pytest.approx(metrics.false_positive_rate, abs=1e-4) == 1 / 3
        # FNR = FN / (TP + FN) = 1 / (2 + 1) = 1/3
        assert pytest.approx(metrics.false_negative_rate, abs=1e-4) == 1 / 3
        # Precision = TP / (TP + FP) = 2 / (2 + 1) = 2/3
        assert pytest.approx(metrics.precision, abs=1e-4) == 2 / 3
        # Recall = TP / (TP + FN) = 2 / (2 + 1) = 2/3
        assert pytest.approx(metrics.recall, abs=1e-4) == 2 / 3

    def test_confusion_matrix_consistency(self) -> None:
        """Matrix consistency: total cells must equal total samples, diagonal equals correct."""
        actuals = [
            Verdict.VULNERABLE,
            Verdict.VULNERABLE,
            Verdict.DEFENDED,
            Verdict.DEFENDED,
            Verdict.INCONCLUSIVE,
            Verdict.DEFENDED,
        ]
        predictions = [
            Verdict.VULNERABLE,
            Verdict.DEFENDED,
            Verdict.DEFENDED,
            Verdict.VULNERABLE,
            Verdict.INCONCLUSIVE,
            Verdict.INCONCLUSIVE,
        ]

        metrics = compute_oracle_metrics(actuals, predictions)

        cm = metrics.confusion_matrix
        total_in_cm = sum(sum(row.values()) for row in cm.values())
        assert total_in_cm == metrics.total_samples == len(actuals)

        diagonal_sum = sum(cm[v.value][v.value] for v in Verdict)
        assert diagonal_sum == metrics.correct_predictions

        # Row checks
        assert sum(cm[Verdict.VULNERABLE.value].values()) == 2
        assert sum(cm[Verdict.DEFENDED.value].values()) == 3
        assert sum(cm[Verdict.INCONCLUSIVE.value].values()) == 1

        # Column checks
        col_vuln = sum(cm[v.value][Verdict.VULNERABLE.value] for v in Verdict)
        col_def = sum(cm[v.value][Verdict.DEFENDED.value] for v in Verdict)
        col_inc = sum(cm[v.value][Verdict.INCONCLUSIVE.value] for v in Verdict)
        assert col_vuln == 2  # 1 VULN, 1 DEF
        assert col_def == 2  # 1 VULN, 1 DEF
        assert col_inc == 2  # 1 INC, 1 DEF
