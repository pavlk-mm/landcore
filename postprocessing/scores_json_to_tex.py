#!/usr/bin/env python3

"""Generate a LaTeX table from a single scores.json file."""

import argparse
import json
import os

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

METRIC_VALUE_MAP = {
    "F1": "f1",
    "P": "precision",
    "R": "recall",
}

STAT_KEYS = {
    "docs",
    "sentences",
    "words",
    "characters",
}


def load_scores(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_stats(path):
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


def format_number(value, digits):
    if value is None:
        return "--"
    if digits == 0:
        return f"{int(round(value))}"
    return f"{value:.{digits}f}"


def parse_metric_values(argument):
    values = [item.strip().upper() for item in argument.split(",") if item.strip()]
    if not values:
        raise ValueError("--metric-values must contain at least one of F1,P,R")

    invalid = [item for item in values if item not in METRIC_VALUE_MAP]
    if invalid:
        raise ValueError(
            f"Invalid metric values: {','.join(invalid)}. Allowed values are F1,P,R"
        )

    return values


def format_metric_cell(metric_payload, selected_metric_values, digits):
    parts = []
    for metric_value in selected_metric_values:
        value_key = METRIC_VALUE_MAP[metric_value]
        parts.append(format_number(metric_payload.get(value_key), digits))
    return " / ".join(parts)


def parse_stats(argument):
    values = [item.strip().lower() for item in argument.split(",") if item.strip()]
    if not values:
        raise ValueError(
            "--include-stats must contain at least one of docs,sentences,words,characters"
        )

    invalid = [item for item in values if item not in STAT_KEYS]
    if invalid:
        raise ValueError(
            "Invalid stats: "
            f"{','.join(invalid)}. Allowed values are docs,sentences,words,characters"
        )

    return values


def extract_stat_value(stats_payload, stat_name):
    if not stats_payload:
        return None

    if stat_name == "docs":
        return stats_payload.get("num_documents")

    averages = stats_payload.get("averages", {})
    return averages.get(stat_name)


def format_stat_cell(value, stat_name, digits):
    if stat_name == "docs":
        if value is None:
            return "--"
        return str(int(value))
    return format_number(value, digits)


def build_table(rows, metrics, include_conll, digits, use_booktabs, stats_to_include):
    columns = ["Corpus"]
    columns.extend([s.upper() for s in stats_to_include])
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
        for stat_name in stats_to_include:
            cells.append(row["stats"].get(stat_name, "--"))
        if include_conll:
            cells.append(format_number(row["conll_score"], digits))
        for metric in metrics:
            cells.append(row["metrics"].get(metric))
        lines.append(" & ".join(["{}" for _ in cells]).format(*cells) + r" \\")

    if use_booktabs:
        lines.append("\\bottomrule")
    else:
        lines.append("\\hline")

    lines.append("\\end{tabular}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a LaTeX table from a single scores.json file."
    )
    parser.add_argument("input", help="Path to scores.json")
    parser.add_argument(
        "--output",
        default=None,
        help="Output .tex file path (default: <input>-table.tex)",
    )
    parser.add_argument(
        "--metric-values",
        default="F1,P,R",
        help="Comma-separated metric value codes to show in each cell (subset of F1,P,R)",
    )
    parser.add_argument(
        "--metrics",
        default=None,
        help="Comma-separated metric names to include (default: from file or built-in)",
    )
    parser.add_argument(
        "--include-stats",
        nargs="?",
        const="docs,sentences,words,characters",
        default=None,
        help=(
            "Include stats columns from stats file. Optionally provide comma-separated "
            "subset/order from docs,sentences,words,characters "
            "(default when provided without value: docs,sentences,words,characters)"
        ),
    )
    parser.add_argument(
        "--stat-file",
        default="text_stats.json",
        help="Path to stats JSON file (default: text_stats.json)",
    )
    parser.add_argument(
        "--include-conll",
        action="store_true",
        help="Include CoNLL score column",
    )
    parser.add_argument(
        "--digits",
        type=int,
        default=0,
        help="Number of decimal digits to display",
    )
    parser.add_argument(
        "--no-booktabs",
        action="store_true",
        help="Use simple hlines instead of booktabs",
    )
    args = parser.parse_args()

    try:
        selected_metric_values = parse_metric_values(args.metric_values)
    except ValueError as error:
        parser.error(str(error))

    stats_to_include = []
    if args.include_stats is not None:
        try:
            stats_to_include = parse_stats(args.include_stats)
        except ValueError as error:
            parser.error(str(error))

    scores = load_scores(args.input)
    files = scores.get("files", {})
    if not files:
        raise SystemExit(f"No files field found in {args.input}")

    stats_files = {}
    if stats_to_include:
        stats_payload = load_stats(args.stat_file)
        stats_files = stats_payload.get("files", {})
        if not stats_files:
            raise SystemExit(f"No files field found in {args.stat_file}")

    if args.metrics:
        metrics = [item.strip() for item in args.metrics.split(",") if item.strip()]
    else:
        metric_names = []
        for payload in files.values():
            metric_names = payload.get("metric_names", [])
            if metric_names:
                break
        metrics = metric_names or DEFAULT_METRICS

    rows = []
    for corpus, payload in files.items():
        metrics_payload = payload.get("metrics", {})
        metric_values = {}
        for metric in metrics:
            metric_values[metric] = format_metric_cell(
                metrics_payload.get(metric, {}),
                selected_metric_values,
                args.digits,
            )

        stat_values = {}
        corpus_stats = stats_files.get(corpus, {})
        for stat_name in stats_to_include:
            stat_values[stat_name] = format_stat_cell(
                extract_stat_value(corpus_stats, stat_name),
                stat_name,
                args.digits,
            )

        rows.append({
            "name": corpus,
            "conll_score": payload.get("conll_score"),
            "stats": stat_values,
            "metrics": metric_values,
        })

    rows.sort(key=lambda row: row["name"])
    table = build_table(
        rows,
        metrics=metrics,
        include_conll=args.include_conll,
        digits=args.digits,
        use_booktabs=not args.no_booktabs,
        stats_to_include=stats_to_include,
    )

    output_path = args.output
    if output_path is None:
        base, _ = os.path.splitext(args.input)
        output_path = f"{base}-table.tex"

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(table)
        handle.write("\n")

    print(f"Wrote table for {len(rows)} corpora to {output_path}")


if __name__ == "__main__":
    main()
