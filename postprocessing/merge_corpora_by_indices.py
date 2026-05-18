#!/usr/bin/env python3

"""Merge two directories of *-annotated.txt corpora using YAML line indices.

For each corpus file, lines with indices listed in the YAML file are taken from one
source directory, and all other lines are taken from the other source directory.
"""

import argparse
import logging
import os
from pathlib import Path

import yaml


DEFAULT_SUFFIX = "-annotated.txt"


def list_corpus_files(directory: Path, suffix: str) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in directory.glob(f"*{suffix}"):
        corpus_name = path.name[: -len(suffix)]
        files[corpus_name] = path
    return files


def load_indices(path: Path) -> dict[str, set[int]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    if not isinstance(payload, dict):
        raise ValueError("Indices YAML must be a mapping: corpus_name -> list_of_line_indices")

    result: dict[str, set[int]] = {}
    for corpus_name, values in payload.items():
        if values is None:
            result[str(corpus_name)] = set()
            continue
        if not isinstance(values, list):
            raise ValueError(f"Indices for corpus '{corpus_name}' must be a list")

        index_set: set[int] = set()
        for value in values:
            if not isinstance(value, int):
                raise ValueError(f"Index '{value}' in corpus '{corpus_name}' is not an integer")
            if value < 0:
                raise ValueError(f"Index '{value}' in corpus '{corpus_name}' is negative")
            index_set.add(value)
        result[str(corpus_name)] = index_set

    return result


def read_lines(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def merge_lines(
    lines_from_indexed_source: list[str],
    lines_from_other_source: list[str],
    selected_indices: set[int],
    corpus_name: str,
) -> list[str]:
    if len(lines_from_indexed_source) != len(lines_from_other_source):
        raise ValueError(
            f"Corpus '{corpus_name}' has different line counts between sources: "
            f"{len(lines_from_indexed_source)} vs {len(lines_from_other_source)}"
        )

    max_index = len(lines_from_indexed_source) - 1
    invalid_indices = sorted(index for index in selected_indices if index > max_index)
    if invalid_indices:
        raise ValueError(
            f"Corpus '{corpus_name}' has out-of-range indices: {invalid_indices[:10]}"
            + (" ..." if len(invalid_indices) > 10 else "")
        )

    merged: list[str] = []
    for i in range(len(lines_from_indexed_source)):
        if i in selected_indices:
            merged.append(lines_from_indexed_source[i])
        else:
            merged.append(lines_from_other_source[i])
    return merged


def write_lines(path: Path, lines: list[str]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line)
            handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Merge corpora from two directories using YAML line indices. "
            "Files must use the -annotated.txt naming pattern."
        )
    )
    parser.add_argument("source_a", help="First source directory")
    parser.add_argument("source_b", help="Second source directory")
    parser.add_argument("indices_yaml", help="YAML file: corpus_name -> list of line indices")
    parser.add_argument("output_dir", help="Output directory for merged corpora")
    parser.add_argument(
        "--indexed-source",
        choices=["a", "b"],
        default="a",
        help=(
            "Which source provides lines for indices listed in YAML (default: a). "
            "The other source provides all remaining lines."
        ),
    )
    parser.add_argument(
        "--suffix",
        default=DEFAULT_SUFFIX,
        help=f"Corpus file suffix (default: {DEFAULT_SUFFIX})",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Skip corpora missing in one source instead of failing",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    source_a = Path(args.source_a)
    source_b = Path(args.source_b)
    indices_path = Path(args.indices_yaml)
    output_dir = Path(args.output_dir)

    if not source_a.is_dir():
        raise SystemExit(f"Not a directory: {source_a}")
    if not source_b.is_dir():
        raise SystemExit(f"Not a directory: {source_b}")
    if not indices_path.is_file():
        raise SystemExit(f"Indices file does not exist: {indices_path}")

    indices_by_corpus = load_indices(indices_path)
    files_a = list_corpus_files(source_a, args.suffix)
    files_b = list_corpus_files(source_b, args.suffix)

    all_corpora = sorted(set(files_a.keys()) | set(files_b.keys()) | set(indices_by_corpus.keys()))

    missing_messages: list[str] = []
    corpora_to_process: list[str] = []
    for corpus_name in all_corpora:
        missing = []
        if corpus_name not in files_a:
            missing.append("source_a")
        if corpus_name not in files_b:
            missing.append("source_b")

        if missing:
            missing_messages.append(f"{corpus_name}: missing in {', '.join(missing)}")
            if args.allow_missing:
                continue
            continue

        corpora_to_process.append(corpus_name)

    if missing_messages and not args.allow_missing:
        details = "\n".join(missing_messages)
        raise SystemExit(f"Cannot merge due to missing corpora:\n{details}")

    output_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    for corpus_name in corpora_to_process:
        indices = indices_by_corpus.get(corpus_name, set())

        lines_a = read_lines(files_a[corpus_name])
        lines_b = read_lines(files_b[corpus_name])

        if args.indexed_source == "a":
            merged = merge_lines(lines_a, lines_b, indices, corpus_name)
        else:
            merged = merge_lines(lines_b, lines_a, indices, corpus_name)

        output_path = output_dir / f"{corpus_name}{args.suffix}"
        write_lines(output_path, merged)
        logging.info(
            "Merged %s (%d lines, %d index-selected) -> %s",
            corpus_name,
            len(merged),
            len(indices),
            output_path,
        )
        processed += 1

    if args.allow_missing and missing_messages:
        logging.warning("Skipped corpora with missing files:\n%s", "\n".join(missing_messages))

    logging.info("Done. Merged %d corpora into %s", processed, output_dir)


if __name__ == "__main__":
    main()
