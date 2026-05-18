#!/usr/bin/env python3

"""Append a LaTeX table block with caption and \\input path to a .tex file."""

import argparse
from pathlib import Path


def build_table_block(caption: str, input_path: str, placement: str, size_macro: str) -> str:
    lines = [f"\\begin{{table}}[{placement}]"]
    if size_macro:
        lines.append(f"\\{size_macro}")
    lines.extend(
        [
            "\\centering",
            f"\\caption{{{caption}}}",
            f"\\input{{{input_path}}}",
            "\\end{table}",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Append a LaTeX table block to a .tex file."
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target .tex file to append to (e.g., outputs/individual-tables.tex)",
    )
    parser.add_argument(
        "--caption",
        required=True,
        help="Caption text for the table",
    )
    parser.add_argument(
        "--input-path",
        required=True,
        help="Path used inside \\input{...} (e.g., my_run/scores-table.tex)",
    )
    parser.add_argument(
        "--placement",
        default="ht",
        help="LaTeX table placement specifier (default: ht)",
    )
    parser.add_argument(
        "--size",
        default="small",
        help="Size macro without backslash, e.g. small, footnotesize (default: small)",
    )
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="Skip appending if the same \\input path is already present in target file",
    )
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        raise SystemExit(f"Target file does not exist: {target}")

    content = target.read_text(encoding="utf-8")
    input_marker = f"\\input{{{args.input_path}}}"

    if args.skip_if_exists and input_marker in content:
        print(f"Skipped: table with {input_marker} already exists in {target}")
        return

    block = build_table_block(
        caption=args.caption,
        input_path=args.input_path,
        placement=args.placement,
        size_macro=args.size,
    )

    prefix = "\n\n" if content and not content.endswith("\n") else "\n"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(prefix)
        handle.write(block)
        handle.write("\n")

    print(f"Appended table block to {target}")


if __name__ == "__main__":
    main()
