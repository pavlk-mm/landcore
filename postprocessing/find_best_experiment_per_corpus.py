#!/usr/bin/env python3

"""Find the best experiment per corpus for a selected metric.

The script scans experiment folders that contain a scores.json file and, for each
corpus, reports the experiment with the highest value of the requested metric.
"""

import argparse
import json
import os
from collections import defaultdict
from typing import Dict, List, Optional

DEFAULT_METRICS = [
    "muc",
    "bcub",
    "ceafe",
    "ceafm",
    "blanc",
    "lea",
    "mor",
    "zero",
]


def find_score_files(root: str) -> List[str]:
    """Return scores.json files directly under experiment folders in root."""
    if os.path.isfile(root) and root.endswith("scores.json"):
        return [root]

    score_files: List[str] = []
    for entry in os.listdir(root):
        candidate = os.path.join(root, entry, "scores.json")
        if os.path.isfile(candidate):
            score_files.append(candidate)
    return sorted(score_files)


def load_scores(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def get_metric_value(payload: Dict, metric: str, metric_value: str) -> Optional[float]:
    if metric == "conll":
        return payload.get("conll_score")

    metric_payload = payload.get("metrics", {}).get(metric, {})
    return metric_payload.get(metric_value)


def collect_candidates(score_files: List[str], metric: str, metric_value: str):
    candidates_by_corpus = defaultdict(list)

    for path in score_files:
        experiment_name = os.path.basename(os.path.dirname(path))
        scores = load_scores(path)
        files_payload = scores.get("files", {})

        for corpus_name, payload in files_payload.items():
            value = get_metric_value(payload, metric=metric, metric_value=metric_value)
            if value is None:
                continue

            candidates_by_corpus[corpus_name].append(
                {
                    "experiment": experiment_name,
                    "value": float(value),
                    "score_file": path,
                }
            )

    return candidates_by_corpus


def select_best(candidates_by_corpus):
    best_by_corpus = {}

    for corpus_name, candidates in candidates_by_corpus.items():
        best_value = max(item["value"] for item in candidates)
        best_candidates = [
            item for item in candidates if item["value"] == best_value
        ]
        best_candidates.sort(key=lambda item: item["experiment"])

        best_by_corpus[corpus_name] = {
            "value": best_value,
            "best_experiment": best_candidates[0]["experiment"],
            "ties": [item["experiment"] for item in best_candidates],
            "num_candidates": len(candidates),
        }

    return best_by_corpus


def print_results(best_by_corpus, metric: str, metric_value: str, digits: int) -> None:
    if not best_by_corpus:
        print("No metric values found for the selected metric.")
        return

    header = f"Best experiments per corpus for {metric}.{metric_value}"
    print(header)
    print("=" * len(header))
    average_value = sum(record["value"] for record in best_by_corpus.values()) / len(best_by_corpus)
    print(f"Average {metric}.{metric_value}: {average_value:.{digits}f}\n")

    for corpus_name in sorted(best_by_corpus):
        record = best_by_corpus[corpus_name]
        value_str = f"{record['value']:.{digits}f}"
        ties = record["ties"]
        if len(ties) > 1:
            tie_info = f" (tie: {', '.join(ties)})"
        else:
            tie_info = ""

        print(
            f"{corpus_name}: {record['best_experiment']} -> {value_str}"
            f" [{record['num_candidates']} experiments]{tie_info}"
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Find the best experiment per corpus for a selected metric."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory containing experiment folders with scores.json",
    )
    parser.add_argument(
        "--metric",
        default="conll",
        help=(
            "Metric name to optimize. Use 'conll' for CoNLL score or one of: "
            + ", ".join(DEFAULT_METRICS)
        ),
    )
    parser.add_argument(
        "--metric-value",
        choices=["f1", "precision", "recall"],
        default="f1",
        help="Sub-value used for non-CoNLL metrics",
    )
    parser.add_argument(
        "--digits",
        type=int,
        default=2,
        help="Number of decimals when printing metric values",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional output path for JSON results",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    metric = args.metric.strip().lower()

    score_files = find_score_files(args.root)
    if not score_files:
        raise SystemExit(f"No scores.json files found under {args.root}")

    candidates_by_corpus = collect_candidates(
        score_files,
        metric=metric,
        metric_value=args.metric_value,
    )
    best_by_corpus = select_best(candidates_by_corpus)

    print_results(
        best_by_corpus,
        metric=metric,
        metric_value=args.metric_value,
        digits=args.digits,
    )

    if args.output_json:
        output_payload = {
            "root": os.path.abspath(args.root),
            "metric": metric,
            "metric_value": args.metric_value,
            "best_by_corpus": best_by_corpus,
        }

        output_directory = os.path.dirname(args.output_json)
        if output_directory:
            os.makedirs(output_directory, exist_ok=True)

        with open(args.output_json, "w", encoding="utf-8") as handle:
            json.dump(output_payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
            handle.write("\n")

        print(f"Wrote JSON output to {args.output_json}")


if __name__ == "__main__":
    main()
