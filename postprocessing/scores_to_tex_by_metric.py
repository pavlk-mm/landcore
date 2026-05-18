#!/usr/bin/env python3

"""Generate one LaTeX table per metric (including CoNLL) from experiment scores.json files.

Default layout:
- rows: experiments
- columns: corpora

The tables can also be transposed across the main diagonal.
Output: a single .tex file containing multiple table environments.
"""

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

AVERAGE_LABEL = "Average"


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


def format_number(value, digits):
    if value is None:
        return "--"
    return f"{value:.{digits}f}"


def format_table_cell(value, digits, highlight=False):
    formatted = format_number(value, digits)
    if value is None or not highlight:
        return formatted
    return rf"\maxValue{{{formatted}}}"


def compute_average(values):
    present_values = [value for value in values if value is not None]
    if not present_values:
        return None
    return sum(present_values) / len(present_values)


def parse_metrics(argument):
    if not argument:
        return []
    metrics = [item.strip().lower() for item in argument.split(",") if item.strip()]
    return metrics or DEFAULT_METRICS


def parse_name_list(arguments):
    if not arguments:
        return None

    selected = []
    for item in arguments:
        selected.extend(part.strip() for part in item.split(",") if part.strip())

    if not selected:
        return None

    return list(dict.fromkeys(selected))


def filter_experiment_names(experiment_names, keyword):
    keyword_lower = keyword.lower()
    return [name for name in experiment_names if keyword_lower in name.lower()]


def filter_selected_names(available_names, selected_names):
    if not selected_names:
        return available_names

    available_name_set = set(available_names)
    return [name for name in selected_names if name in available_name_set]


def collect_experiments(score_files, metric_value, metrics):
    experiments = {}
    corpora_set = set()

    for path in score_files:
        experiment_name = os.path.basename(os.path.dirname(path))
        scores = load_scores(path)
        files = scores.get("files", {})

        experiment_data = {
            "conll": {},
            "metrics": {metric: {} for metric in metrics},
        }

        for corpus_name, payload in files.items():
            corpora_set.add(corpus_name)
            experiment_data["conll"][corpus_name] = payload.get("conll_score")

            payload_metrics = payload.get("metrics", {})
            for metric in metrics:
                metric_payload = payload_metrics.get(metric, {})
                experiment_data["metrics"][metric][corpus_name] = metric_payload.get(metric_value)

        experiments[experiment_name] = experiment_data

    return experiments, sorted(corpora_set)


def build_tabular(
    rows,
    columns,
    data_lookup,
    digits,
    use_booktabs,
    row_header,
    max_by_corpus=None,
    corpus_for_cell=None,
):
    column_spec = "l" + "r" * len(columns)
    lines = [f"\\begin{{tabular}}{{{column_spec}}}"]

    # if use_booktabs:
    #     lines.append("\\toprule")
    # else:
    #     lines.append("\\hline")

    header_cells = [latex_escape(row_header)] + [
        f"\\columnName{{{latex_escape(column)}}}" for column in columns
    ]
    lines.append(" & ".join(header_cells) + r" \\")

    if use_booktabs:
        lines.append("\\midrule")
    else:
        lines.append("\\hline")

    for row_name in rows:
        cells = [f"\\rowName{{{latex_escape(row_name)}}}"]
        for column_name in columns:
            value = data_lookup(row_name, column_name)
            highlight = False
            if max_by_corpus is not None and corpus_for_cell is not None and value is not None:
                corpus_name = corpus_for_cell(row_name, column_name)
                max_value = max_by_corpus.get(corpus_name)
                highlight = max_value is not None and abs(value - max_value) < 1e-9
            cells.append(format_table_cell(value, digits, highlight=highlight))
        lines.append(" & ".join(cells) + r" \\")

    # if use_booktabs:
    #     lines.append("\\bottomrule")
    # else:
    #     lines.append("\\hline")

    lines.append("\\end{tabular}")
    return "\n".join(lines)


def build_table_environment(tabular, caption, placement, size_macro):
    lines = [f"\\begin{{table}}[{placement}]"]
    if size_macro:
        lines.append(f"\\{size_macro}")
    lines.extend([
        "\\centering",
        f"\\caption{{{caption}}}",
        tabular,
        "\\end{table}",
    ])
    return "\n".join(lines)


def compute_max_by_corpus(group_rows, corpora, data_lookup):
    max_by_corpus = {}
    for corpus_name in corpora:
        values = [
            data_lookup(experiment_name, corpus_name)
            for experiment_name in group_rows
        ]
        present_values = [value for value in values if value is not None]
        max_by_corpus[corpus_name] = max(present_values) if present_values else None
    return max_by_corpus


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate one table per metric (including CoNLL) with experiments as rows "
            "and corpora as columns, or transpose the layout diagonally."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory containing experiment folders with scores.json",
    )
    parser.add_argument(
        "--output",
        default="scores-by-metric.tex",
        help="Output .tex file path",
    )
    parser.add_argument(
        "--metric-value",
        choices=["f1", "precision", "recall"],
        default="f1",
        help="Metric value used for non-CoNLL metrics",
    )
    parser.add_argument(
        "--metrics",
        default="",#",".join(DEFAULT_METRICS),
        help="Comma-separated metric names to include after CoNLL",
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
    parser.add_argument(
        "--placement",
        default="ht",
        help="LaTeX table placement specifier (default: ht)",
    )
    parser.add_argument(
        "--size",
        default="normalsize",
        help="Size macro without backslash, e.g. small, footnotesize",
    )
    parser.add_argument(
        "--caption-prefix",
        default="Scores by corpus for metric",
        help="Caption prefix used as '<prefix>: <METRIC>'",
    )
    parser.add_argument(
        "--transpose",
        "--diagonal",
        action="store_true",
        help=(
            "Transpose each table across the main diagonal so corpora become rows "
            "and experiments become columns"
        ),
    )
    parser.add_argument(
        "--highlight-max",
        action="store_true",
        help=r"Wrap the maximum score for each corpus in \maxValue{}",
    )
    parser.add_argument(
        "--experiments",
        nargs="+",
        default=None,
        help=(
            "Restrict the output to the given experiment names. Accepts a space- "
            "or comma-separated list."
        ),
    )
    parser.add_argument(
        "--corpora",
        nargs="+",
        default=None,
        help=(
            "Restrict the output to the given corpus names. Accepts a space- or "
            "comma-separated list."
        ),
    )
    parser.add_argument(
        "--include-average",
        action="store_true",
        help=(
            "Append an Average row/column computed as the arithmetic mean across "
            "the displayed corpora for each experiment."
        ),
    )
    args = parser.parse_args()

    metrics = parse_metrics(args.metrics)
    score_files = find_score_files(args.root)
    if not score_files:
        raise SystemExit(f"No scores.json files found under {args.root}")

    experiments, corpora = collect_experiments(
        score_files,
        metric_value=args.metric_value,
        metrics=metrics,
    )

    experiment_names = sorted(experiments.keys())
    selected_experiments = parse_name_list(args.experiments)
    if selected_experiments:
        experiment_names = filter_selected_names(
            experiment_names,
            selected_experiments,
        )
        if not experiment_names:
            raise SystemExit(
                "No experiments matched --experiments: "
                + ", ".join(selected_experiments)
            )

    selected_corpora = parse_name_list(args.corpora)
    if selected_corpora:
        corpora = filter_selected_names(corpora, selected_corpora)
        if not corpora:
            raise SystemExit(
                "No corpora matched --corpora: "
                + ", ".join(selected_corpora)
            )

    dev_experiment_names = filter_experiment_names(experiment_names, "dev")
    small_experiment_names = filter_experiment_names(experiment_names, "small")

    grouped_experiments = [
        ("dev", dev_experiment_names),
        ("small", small_experiment_names),
    ]

    metric_order = ["conll"] + metrics
    tables = []

    for group_name, group_rows in grouped_experiments:
        if not group_rows:
            continue

        for metric in metric_order:
            if metric == "conll":
                def base_data_lookup(experiment_name, corpus_name):
                    return experiments[experiment_name]["conll"].get(corpus_name)

                caption_metric_name = "CoNLL"
            else:
                def base_data_lookup(experiment_name, corpus_name, metric_name=metric):
                    return experiments[experiment_name]["metrics"][metric_name].get(corpus_name)

                caption_metric_name = metric.upper()

            display_corpora = corpora + ([AVERAGE_LABEL] if args.include_average else [])

            def lookup_with_average(experiment_name, corpus_name, lookup=base_data_lookup):
                if corpus_name == AVERAGE_LABEL:
                    return compute_average(
                        lookup(experiment_name, current_corpus)
                        for current_corpus in corpora
                    )
                return lookup(experiment_name, corpus_name)

            max_by_corpus = None
            if args.highlight_max:
                max_by_corpus = compute_max_by_corpus(group_rows, display_corpora, lookup_with_average)

            if args.transpose:
                def data_lookup(corpus_name, experiment_name, lookup=lookup_with_average):
                    return lookup(experiment_name, corpus_name)

                def corpus_for_cell(corpus_name, experiment_name):
                    return corpus_name

                table_rows = display_corpora
                table_columns = group_rows
                row_header = "Corpus"
            else:
                data_lookup = lookup_with_average

                def corpus_for_cell(experiment_name, corpus_name):
                    return corpus_name

                table_rows = group_rows
                table_columns = display_corpora
                row_header = "Experiment"

            tabular = build_tabular(
                rows=table_rows,
                columns=table_columns,
                data_lookup=data_lookup,
                digits=args.digits,
                use_booktabs=not args.no_booktabs,
                row_header=row_header,
                max_by_corpus=max_by_corpus,
                corpus_for_cell=corpus_for_cell,
            )

            table_env = build_table_environment(
                tabular=tabular,
                caption=f"{args.caption_prefix} ({group_name}): {caption_metric_name}",
                placement=args.placement,
                size_macro=args.size,
            )
            tables.append(table_env)

    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write("\n\n".join(tables))
        handle.write("\n")

    selection_parts = []
    if selected_experiments is not None:
        selection_parts.append(f"selected_experiments={len(experiment_names)}")
    if selected_corpora is not None:
        selection_parts.append(f"selected_corpora={len(corpora)}")
    selected_summary = f" ({', '.join(selection_parts)})" if selection_parts else ""

    print(
        f"Wrote {len(tables)} tables to {args.output} "
        f"for dev={len(dev_experiment_names)}, small={len(small_experiment_names)} experiments "
        f"and {len(corpora)} corpora{selected_summary}"
    )


if __name__ == "__main__":
    main()
