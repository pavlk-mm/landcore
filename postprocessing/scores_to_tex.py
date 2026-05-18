#!/usr/bin/env python3

"""Generate a LaTeX table from experiment scores.json files."""

import argparse
import json
import os
from statistics import mean

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


def find_score_files(root):
    score_files = []
    if os.path.isfile(root) and root.endswith("scores.json"):
        return [root]

    for entry in os.listdir(root):
        candidate = os.path.join(root, entry, "scores.json")
        if os.path.isfile(candidate):
            score_files.append(candidate)
    return sorted(score_files)


def load_scores(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def latex_escape(text):
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
        .replace("$", r"\$")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


def aggregate_experiment(scores, metric_value):
    files = scores.get("files", {})
    if not files:
        return {
            "conll_score": None,
            "metrics": {},
        }

    conll_scores = []
    metric_values = {}

    for _, payload in files.items():
        if payload.get("conll_score") is not None:
            conll_scores.append(payload["conll_score"])
        for metric, values in payload.get("metrics", {}).items():
            value = values.get(metric_value)
            if value is None:
                continue
            metric_values.setdefault(metric, []).append(value)

    aggregated_metrics = {
        metric: mean(values) for metric, values in metric_values.items() if values
    }

    return {
        "conll_score": mean(conll_scores) if conll_scores else None,
        "metrics": aggregated_metrics,
    }


def format_number(value, digits):
    if value is None:
        return "--"
    return f"{value:.{digits}f}"


def build_table(rows, metrics, include_conll, digits, use_booktabs):
    columns = ["Experiment"]
    if include_conll:
        columns.append("CoNLL")
    columns.extend([m.upper() for m in metrics])

    column_spec = "l" + "r" * (len(columns) - 1)
    lines = []
    if use_booktabs:
        lines.append("\\begin{tabular}{%s}" % column_spec)
        lines.append("\\toprule")
    else:
        lines.append("\\begin{tabular}{%s}" % column_spec)
        lines.append("\\hline")

    lines.append(" & ".join(["{}" for _ in columns]).format(*columns) + r" \\")

    if use_booktabs:
        lines.append("\\midrule")
    else:
        lines.append("\\hline")

    for row in rows:
        cells = [latex_escape(row["name"])]
        if include_conll:
            cells.append(format_number(row["conll_score"], digits))
        for metric in metrics:
            cells.append(format_number(row["metrics"].get(metric), digits))
        lines.append(" & ".join(["{}" for _ in cells]).format(*cells) + r" \\")

    if use_booktabs:
        lines.append("\\bottomrule")
    else:
        lines.append("\\hline")

    lines.append("\\end{tabular}")
    return "\n".join(lines)


def filter_rows_by_keyword(rows, keyword):
    keyword_lower = keyword.lower()
    return [row for row in rows if keyword_lower in row["name"].lower()]


def main():
    parser = argparse.ArgumentParser(
        description="Generate a LaTeX table from experiment scores.json files."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory containing experiment folders with scores.json",
    )
    parser.add_argument(
        "--output",
        default="scores-table.tex",
        help="Output .tex file path",
    )
    parser.add_argument(
        "--metric-value",
        choices=["f1", "precision", "recall"],
        default="f1",
        help="Metric value to show in the table",
    )
    parser.add_argument(
        "--metrics",
        default=",".join(DEFAULT_METRICS),
        help="Comma-separated metric names to include",
    )
    parser.add_argument(
        "--include-conll",
        action="store_true",
        help="Include CoNLL score column",
    )
    parser.add_argument(
        "--digits",
        type=int,
        default=2,
        help="Number of decimal digits to display",
    )
    parser.add_argument(
        "--no-booktabs",
        action="store_true",
        help="Use simple hlines instead of booktabs",
    )
    args = parser.parse_args()

    metrics = [item.strip() for item in args.metrics.split(",") if item.strip()]
    score_files = find_score_files(args.root)
    if not score_files:
        raise SystemExit(f"No scores.json files found under {args.root}")

    rows = []
    for path in score_files:
        scores = load_scores(path)
        experiment_name = os.path.basename(os.path.dirname(path))
        aggregated = aggregate_experiment(scores, args.metric_value)
        rows.append({
            "name": experiment_name,
            "conll_score": aggregated["conll_score"],
            "metrics": aggregated["metrics"],
        })

    rows.sort(key=lambda row: row["name"])
    all_rows = rows
    small_rows = filter_rows_by_keyword(rows, "small")
    dev_rows = filter_rows_by_keyword(rows, "dev")

    tables = [
        build_table(
            all_rows,
            metrics=metrics,
            include_conll=args.include_conll,
            digits=args.digits,
            use_booktabs=not args.no_booktabs,
        ),
        build_table(
            small_rows,
            metrics=metrics,
            include_conll=args.include_conll,
            digits=args.digits,
            use_booktabs=not args.no_booktabs,
        ),
        build_table(
            dev_rows,
            metrics=metrics,
            include_conll=args.include_conll,
            digits=args.digits,
            use_booktabs=not args.no_booktabs,
        ),
    ]

    output_text = "\n\n".join(tables)

    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(output_text)
        handle.write("\n")

    print(
        f"Wrote 3 tables to {args.output} "
        f"(all: {len(all_rows)}, small: {len(small_rows)}, dev: {len(dev_rows)})"
    )


if __name__ == "__main__":
    main()
