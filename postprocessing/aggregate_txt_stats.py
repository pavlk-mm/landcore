#!/usr/bin/env python3

"""Aggregate per-document statistics from text files into a JSON file."""

import argparse
import glob
import json
import os


parser = argparse.ArgumentParser(
    description="Aggregate document statistics from files matching a suffix into a JSON file."
)
parser.add_argument(
    "--root",
    default=".",
    help="Directory containing input files (default: current directory)",
)
parser.add_argument(
    "--output",
    default="text_stats.json",
    help="Output JSON path (default: text_stats.json)",
)
parser.add_argument(
    "--suffix",
    default="-corefud.txt",
    help="Filename suffix to include (default: -corefud.txt)",
)


def count_document_stats(document):
    return {
        "words": len(document.split()),
        "sentences": document.count("."),
        "characters": len(document),
    }


def parse_text_file(path):
    document_stats = []

    with open(path, "r", encoding="utf-8") as handle:
        for index, raw_line in enumerate(handle, start=1):
            document = raw_line.rstrip("\n").rstrip("\r")
            stats = count_document_stats(document)
            document_stats.append(
                {
                    "index": index,
                    **stats,
                }
            )

    num_documents = len(document_stats)
    total_words = sum(item["words"] for item in document_stats)
    total_sentences = sum(item["sentences"] for item in document_stats)
    total_characters = sum(item["characters"] for item in document_stats)

    if num_documents == 0:
        averages = {
            "words": 0.0,
            "sentences": 0.0,
            "characters": 0.0,
        }
    else:
        averages = {
            "words": total_words / num_documents,
            "sentences": total_sentences / num_documents,
            "characters": total_characters / num_documents,
        }

    return {
        "num_documents": num_documents,
        "averages": averages,
        "documents": document_stats,
    }


def collect_text_files(root_dir, suffix):
    if not suffix:
        raise ValueError("--suffix must be a non-empty string")

    pattern = os.path.join(root_dir, f"*{suffix}")
    return sorted(glob.glob(pattern))


def main():
    args = parser.parse_args()

    text_files = collect_text_files(args.root, args.suffix)
    if not text_files:
        raise SystemExit(f"No files ending with '{args.suffix}' found in {args.root}")

    aggregated = {}
    for path in text_files:
        basename = os.path.basename(path)
        file_key = basename[: -len(args.suffix)]
        aggregated[file_key] = {
            "path": os.path.relpath(path, args.root),
            **parse_text_file(path),
        }

    output_directory = os.path.dirname(args.output)
    if output_directory and not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_payload = {
        "root": os.path.relpath(args.root, output_directory),
        "files": aggregated,
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output_payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
        handle.write("\n")

    print(f"Wrote statistics for {len(aggregated)} files to {args.output}")


if __name__ == "__main__":
    main()
