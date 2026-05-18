#!/usr/bin/env python3

"""Aggregate coref scorer outputs into a single JSON file."""

import argparse
import glob
import json
import os
import re

parser = argparse.ArgumentParser(
	description="Aggregate *-scores.txt files into a JSON file."
)
parser.add_argument(
	"--root",
	default=".",
	help="Root directory to search for score files (default: current directory)",
)
parser.add_argument(
	"--output",
	default="scores.json",
	help="Output JSON path (default: scores.json)",
)

METRIC_NAMES = {
    "muc",
    "bcub",
    "ceafe",
    "ceafm",
    "blanc",
    "lea",
    "mor",
    "zero",
}

METRIC_LINE_RE = re.compile(
    r"^Recall:\s*([0-9.]+)\s*Precision:\s*([0-9.]+)\s*F1:\s*([0-9.]+)$",
    re.IGNORECASE,
)
CONLL_RE = re.compile(r"^CoNLL score:\s*([0-9.]+)$", re.IGNORECASE)
METRICS_HEADER_RE = re.compile(r"^The following metrics will be evaluated:\s*(.+)$", re.IGNORECASE)


def parse_score_file(path):
    metrics = {}
    conll_score = None
    current_metric = None
    metric_names = []

    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line == "":
                continue

            match = METRICS_HEADER_RE.match(line)
            if match:
                metric_names = [item.strip() for item in match.group(1).split(",") if item.strip()]
                continue

            lower = line.lower()
            if lower in metric_names:
                current_metric = lower
                metrics.setdefault(current_metric, {})
                continue

            match = METRIC_LINE_RE.match(line)
            if match and current_metric:
                recall, precision, f1 = match.groups()
                metrics[current_metric] = {
                    "recall": float(recall),
                    "precision": float(precision),
                    "f1": float(f1),
                }
                current_metric = None
                continue

            match = CONLL_RE.match(line)
            if match:
                conll_score = float(match.group(1))
                continue

    return {
        "metric_names": metric_names,
        "metrics": metrics,
        "conll_score": conll_score,
    }


def collect_score_files(root_dir):
    pattern = os.path.join(root_dir, "**", "*-scores.txt")
    return sorted(glob.glob(pattern, recursive=True))


def main():
    args = parser.parse_args()

    score_files = collect_score_files(args.root)
    if not score_files:
        raise SystemExit(f"No *-scores.txt files found under {args.root}")

    aggregated = {}
    for path in score_files:
        basename = os.path.basename(path)
        corpus = basename.replace("-scores.txt", "")
        aggregated[corpus] = {
            "path": os.path.relpath(path, args.root),
            **parse_score_file(path),
        }

    output_directory = os.path.dirname(args.output)
    if output_directory and not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_payload = {
        "root": os.path.relpath(args.root, output_directory),
        "files": aggregated
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output_payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
        handle.write("\n")

    print(f"Wrote {len(aggregated)} score files to {args.output}")


if __name__ == "__main__":
    main()
