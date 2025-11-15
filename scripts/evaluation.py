import json
import logging
from typing import Dict, List, Tuple

# Type alias for clarity
PII_DATA = Dict[str, Dict[str, List[str]]]

from typing import Dict, List, Any, Set
from collections import defaultdict
import numpy as np

# Configure logger
logger = logging.getLogger(__name__)


def calculate_pii_metrics(
    predictions: Dict, ground_truth: Dict, test_name: str = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive PII extraction metrics with per-category and aggregate reporting.
    """

    def flatten_entities(data: Dict, test_filter: str = None) -> Dict[str, List[str]]:
        flattened = defaultdict(list)
        for test_key, test_data in data.items():
            if test_filter and test_key != test_filter:
                continue
            for category, entities in test_data.items():
                flattened[category].extend(
                    entities if isinstance(entities, list) else [entities]
                )
        return dict(flattened)

    def calculate_category_metrics(
        pred_entities: List[str], true_entities: List[str]
    ) -> Dict[str, float]:
        pred_set, true_set = set(pred_entities), set(true_entities)

        if not pred_set and not true_set:
            return {
                "precision": 1.0,
                "recall": 1.0,
                "f1": 1.0,
                "tp": 0,
                "fp": 0,
                "fn": 0,
                "support": 0,
            }
        if not pred_set:
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "tp": 0,
                "fp": 0,
                "fn": len(true_set),
                "support": len(true_set),
            }
        if not true_set:
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "tp": 0,
                "fp": len(pred_set),
                "fn": 0,
                "support": 0,
            }

        TP = len(pred_set & true_set)
        FP = len(pred_set - true_set)
        FN = len(true_set - pred_set)

        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": TP,
            "fp": FP,
            "fn": FN,
            "support": len(true_set),
        }

    available_tests = set(predictions.keys()) & set(ground_truth.keys())
    if test_name and test_name not in available_tests:
        raise ValueError(
            f"Test '{test_name}' not found in both prediction and ground truth"
        )

    tests_to_evaluate = [test_name] if test_name else list(available_tests)

    all_results = {}
    overall_metrics = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "support": 0})

    for test in tests_to_evaluate:
        pred_flat = flatten_entities(predictions, test)
        truth_flat = flatten_entities(ground_truth, test)
        all_categories = set(pred_flat.keys()) | set(truth_flat.keys())

        test_results = {}
        for category in sorted(all_categories):
            metrics = calculate_category_metrics(
                pred_flat.get(category, []), truth_flat.get(category, [])
            )
            test_results[category] = metrics
            for key in ["tp", "fp", "fn"]:
                overall_metrics[category][key] += metrics[key]
            overall_metrics[category]["support"] += metrics["support"]

        all_results[test] = test_results

    # Calculate overall metrics
    overall_results = {}
    for category, counts in overall_metrics.items():
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        overall_results[category] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "support": counts["support"],
        }

    # Calculate micro and macro averages
    micro_tp = sum(m["tp"] for m in overall_results.values())
    micro_fp = sum(m["fp"] for m in overall_results.values())
    micro_fn = sum(m["fn"] for m in overall_results.values())

    micro_precision = (
        micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) > 0 else 0.0
    )
    micro_recall = (
        micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) > 0 else 0.0
    )
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if (micro_precision + micro_recall) > 0
        else 0.0
    )

    return {
        "per_test": all_results,
        "overall_per_category": overall_results,
        "summary": {
            "micro": {
                "precision": round(micro_precision, 4),
                "recall": round(micro_recall, 4),
                "f1": round(micro_f1, 4),
            },
            "macro": {
                "precision": round(
                    np.mean([m["precision"] for m in overall_results.values()]), 4
                ),
                "recall": round(
                    np.mean([m["recall"] for m in overall_results.values()]), 4
                ),
                "f1": round(np.mean([m["f1"] for m in overall_results.values()]), 4),
            },
            "total_tests": len(tests_to_evaluate),
            "total_categories": len(overall_results),
        },
    }


def print_metrics_report(metrics: Dict[str, Any]):
    """Print a formatted report of the metrics"""

    logger.info("=" * 80)
    logger.info("PII EXTRACTION EVALUATION REPORT")
    logger.info("=" * 80)

    # Summary metrics
    summary = metrics["summary"]
    logger.info(f"\nOVERALL SUMMARY (Micro/Macro Averages):")
    logger.info(f"Tests Evaluated: {summary['total_tests']}")
    logger.info(f"Categories Found: {summary['total_categories']}")
    logger.info(f"Micro Precision: {summary['micro']['precision']:.4f}")
    logger.info(f"Micro Recall:    {summary['micro']['recall']:.4f}")
    logger.info(f"Micro F1-Score:  {summary['micro']['f1']:.4f}")
    logger.info(f"Macro Precision: {summary['macro']['precision']:.4f}")
    logger.info(f"Macro Recall:    {summary['macro']['recall']:.4f}")
    logger.info(f"Macro F1-Score:  {summary['macro']['f1']:.4f}")

    # Per-category metrics
    logger.info(f"\nPER-CATEGORY METRICS:")
    logger.info("-" * 80)
    logger.info(
        f"{'Category':<20} {'Precision':<10} {'Recall':<10} {'F1-Score':<10} {'Support':<10} {'TP/FP/FN':<15}"
    )
    logger.info("-" * 80)

    for category, cat_metrics in metrics["overall_per_category"].items():
        tp_fp_fn = f"{cat_metrics['tp']}/{cat_metrics['fp']}/{cat_metrics['fn']}"
        logger.info(
            f"{category:<20} {cat_metrics['precision']:<10.4f} {cat_metrics['recall']:<10.4f} "
            f"{cat_metrics['f1']:<10.4f} {cat_metrics['support']:<10} {tp_fp_fn:<15}"
        )

    # Per-test metrics (if multiple tests)
    if len(metrics["per_test"]) > 1:
        logger.info(f"\nPER-TEST BREAKDOWN:")
        logger.info("-" * 80)
        for test_name, test_metrics in metrics["per_test"].items():
            test_f1 = np.mean([m["f1"] for m in test_metrics.values()])
            total_entities = sum(m["support"] for m in test_metrics.values())
            logger.info(
                f"{test_name}: Average F1 = {test_f1:.4f}, Total Entities = {total_entities}"
            )
