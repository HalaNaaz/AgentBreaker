"""Mathematical validation and computation of Evaluation Oracle benchmark metrics.

This module provides rigorous multi-class and binary metrics calculation
for evaluation oracles, ensuring inconclusive verdicts are not conflated
with true negatives in binary false positive calculations.
"""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from agentbreaker.schemas.enums import Verdict


class OracleMetrics(BaseModel):
    """Encapsulates comprehensive evaluation metrics for benchmark datasets."""

    model_config = ConfigDict(frozen=True)

    total_samples: int = Field(default=0, description="Total evaluated samples.")
    correct_predictions: int = Field(
        default=0, description="Total exact matches across all verdicts."
    )
    accuracy: float = Field(default=0.0, description="Overall 3-class classification accuracy.")

    # Conclusive binary metrics (VULNERABLE is positive, DEFENDED is negative)
    tp: int = Field(default=0, description="True Positives: actual VULN, predicted VULN.")
    tn: int = Field(default=0, description="True Negatives: actual DEFENDED, predicted DEFENDED.")
    fp: int = Field(default=0, description="False Positives: actual DEFENDED, predicted VULN.")
    fn: int = Field(default=0, description="False Negatives: actual VULN, predicted DEFENDED.")

    # Explicit inconclusive accounting
    inconclusive_actual: int = Field(
        default=0, description="Total ground-truth INCONCLUSIVE samples."
    )
    inconclusive_predicted: int = Field(
        default=0, description="Total predicted INCONCLUSIVE samples."
    )
    inconclusive_correct: int = Field(
        default=0, description="Actual INCONCLUSIVE predicted INCONCLUSIVE."
    )
    inconclusive_as_vuln: int = Field(
        default=0, description="Actual INCONCLUSIVE predicted VULNERABLE."
    )
    inconclusive_as_defended: int = Field(
        default=0, description="Actual INCONCLUSIVE predicted DEFENDED."
    )
    vuln_as_inconclusive: int = Field(
        default=0, description="Actual VULNERABLE predicted INCONCLUSIVE."
    )
    defended_as_inconclusive: int = Field(
        default=0, description="Actual DEFENDED predicted INCONCLUSIVE."
    )

    conclusive_samples: int = Field(
        default=0, description="Total decisive pairs (VULNERABLE or DEFENDED)."
    )
    conclusive_accuracy: float = Field(
        default=0.0, description="Accuracy strictly on conclusive pairs."
    )

    false_positive_rate: float = Field(
        default=0.0,
        description="FPR = FP / (FP + TN). Inconclusive samples are excluded from TN.",
    )
    false_negative_rate: float = Field(
        default=0.0,
        description="FNR = FN / (TP + FN). Inconclusive samples are excluded from FN.",
    )
    precision: float = Field(default=0.0, description="Precision = TP / (TP + FP).")
    recall: float = Field(default=0.0, description="Recall = TP / (TP + FN).")
    f1_score: float = Field(default=0.0, description="Harmonic mean of precision and recall.")

    confusion_matrix: dict[str, dict[str, int]] = Field(
        default_factory=lambda: {
            Verdict.VULNERABLE.value: {
                Verdict.VULNERABLE.value: 0,
                Verdict.DEFENDED.value: 0,
                Verdict.INCONCLUSIVE.value: 0,
            },
            Verdict.DEFENDED.value: {
                Verdict.VULNERABLE.value: 0,
                Verdict.DEFENDED.value: 0,
                Verdict.INCONCLUSIVE.value: 0,
            },
            Verdict.INCONCLUSIVE.value: {
                Verdict.VULNERABLE.value: 0,
                Verdict.DEFENDED.value: 0,
                Verdict.INCONCLUSIVE.value: 0,
            },
        },
        description="Full 3x3 confusion matrix mapping [expected][predicted].",
    )


def compute_oracle_metrics(
    actuals: Sequence[Verdict],
    predictions: Sequence[Verdict],
) -> OracleMetrics:
    """Compute mathematically sound multi-class and binary metrics for evaluation verdicts.

    Metric Methodology:
    1. Overall Accuracy: Computed across all classes including INCONCLUSIVE:
       Accuracy = Correct / Total.
    2. Conclusive Binary Metrics:
       Positive class = VULNERABLE
       Negative class = DEFENDED
       - TP: Actual VULNERABLE and Predicted VULNERABLE.
       - TN: Actual DEFENDED and Predicted DEFENDED.
       - FP: Actual DEFENDED and Predicted VULNERABLE.
       - FN: Actual VULNERABLE and Predicted DEFENDED.
    3. Inconclusive Handling:
       Inconclusive samples represent indeterminate responses and are tracked
       separately. They are NOT silently counted as True Negatives in the FPR
       denominator:
       - False Positive Rate: FPR = FP / (FP + TN) where TN only includes actual DEFENDED.
         If FP + TN == 0, FPR evaluates to 0.0.
       - False Negative Rate: FNR = FN / (TP + FN) where FN only includes actual VULNERABLE.
         If TP + FN == 0, FNR evaluates to 0.0.
    4. Zero Denominators:
       All rates (FPR, FNR, precision, recall, F1, accuracy) safely evaluate to 0.0
       when denominators are zero (e.g. empty dataset, all-positive, or all-negative).

    Args:
        actuals: Sequence of expected ground-truth Verdict instances.
        predictions: Sequence of predicted Verdict instances.

    Returns:
        Immutable OracleMetrics instance with complete metric breakdown.

    Raises:
        ValueError: If actuals and predictions have different lengths.
    """
    if len(actuals) != len(predictions):
        raise ValueError(
            f"Length mismatch: {len(actuals)} actuals vs {len(predictions)} predictions"
        )

    total = len(actuals)
    if total == 0:
        return OracleMetrics()

    # Initialize 3x3 confusion matrix
    cm: dict[str, dict[str, int]] = {v1.value: {v2.value: 0 for v2 in Verdict} for v1 in Verdict}

    correct = 0
    tp = 0
    tn = 0
    fp = 0
    fn = 0

    inc_actual = 0
    inc_pred = 0
    inc_correct = 0
    inc_as_vuln = 0
    inc_as_def = 0
    vuln_as_inc = 0
    def_as_inc = 0

    for act, pred in zip(actuals, predictions, strict=True):
        cm[act.value][pred.value] += 1

        if act == pred:
            correct += 1

        if act == Verdict.INCONCLUSIVE:
            inc_actual += 1
            if pred == Verdict.INCONCLUSIVE:
                inc_correct += 1
            elif pred == Verdict.VULNERABLE:
                inc_as_vuln += 1
            elif pred == Verdict.DEFENDED:
                inc_as_def += 1

        if pred == Verdict.INCONCLUSIVE:
            inc_pred += 1
            if act == Verdict.VULNERABLE:
                vuln_as_inc += 1
            elif act == Verdict.DEFENDED:
                def_as_inc += 1

        # Binary conclusive classification
        if act == Verdict.VULNERABLE and pred == Verdict.VULNERABLE:
            tp += 1
        elif act == Verdict.DEFENDED and pred == Verdict.DEFENDED:
            tn += 1
        elif act == Verdict.DEFENDED and pred == Verdict.VULNERABLE:
            fp += 1
        elif act == Verdict.VULNERABLE and pred == Verdict.DEFENDED:
            fn += 1

    conclusive_total = tp + tn + fp + fn
    accuracy = correct / total if total > 0 else 0.0
    conclusive_acc = (tp + tn) / conclusive_total if conclusive_total > 0 else 0.0

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0.0 else 0.0

    return OracleMetrics(
        total_samples=total,
        correct_predictions=correct,
        accuracy=round(accuracy, 6),
        tp=tp,
        tn=tn,
        fp=fp,
        fn=fn,
        inconclusive_actual=inc_actual,
        inconclusive_predicted=inc_pred,
        inconclusive_correct=inc_correct,
        inconclusive_as_vuln=inc_as_vuln,
        inconclusive_as_defended=inc_as_def,
        vuln_as_inconclusive=vuln_as_inc,
        defended_as_inconclusive=def_as_inc,
        conclusive_samples=conclusive_total,
        conclusive_accuracy=round(conclusive_acc, 6),
        false_positive_rate=round(fpr, 6),
        false_negative_rate=round(fnr, 6),
        precision=round(precision, 6),
        recall=round(recall, 6),
        f1_score=round(f1, 6),
        confusion_matrix=cm,
    )
