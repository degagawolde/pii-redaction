# evaluation.py
from collections import defaultdict
import json


class PIIEvaluator:
    def __init__(self, gold_labels_path):
        # Load and parse the gold standard annotations (assuming JSON format)
        with open(gold_labels_path, "r") as f:
            self.gold_labels = json.load(f)

    def compare_and_score(self, document_id: str, predicted_entities: list[dict]):
        """Compares predicted PII entities against gold labels for a single document."""

        gold_entities = self.gold_labels.get(document_id, [])

        # Convert entities to a unique, comparable format (e.g., set of tuples)
        gold_set = {(e["start"], e["end"], e["type"]) for e in gold_entities}
        pred_set = {(e["start"], e["end"], e["type"]) for e in predicted_entities}

        # Calculation of True Positives (TP), False Positives (FP), False Negatives (FN)
        TP = len(gold_set.intersection(pred_set))
        FP = len(pred_set.difference(gold_set))
        FN = len(gold_set.difference(pred_set))

        return TP, FP, FN

    def calculate_metrics(self, TP_total: int, FP_total: int, FN_total: int) -> dict:
        """Calculates Precision, Recall, and F1-Score."""

        # Precision (P)
        if TP_total + FP_total == 0:
            precision = 1.0  # Or 0.0, depending on convention for no predictions
        else:
            precision = TP_total / (TP_total + FP_total)

        # Recall (R)
        if TP_total + FN_total == 0:
            recall = 1.0
        else:
            recall = TP_total / (TP_total + FN_total)

        # F1-Score
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)

        return {
            "Precision": precision,
            "Recall": recall,
            "F1-Score": f1,
            "Total TP": TP_total,
            "Total FP": FP_total,
            "Total FN": FN_total,
        }
