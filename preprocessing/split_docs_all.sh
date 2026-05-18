#!/bin/bash
# Script that runs split_docs.sh for all files in a directory.

if [ $# -ne 2 ]; then
	echo "Usage: $0 <input-dir> <output-dir>"
	exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"

if [ ! -d "$INPUT_DIR" ]; then
	echo "Error: Input directory '$INPUT_DIR' does not exist"
	exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPLIT_DOCS_SCRIPT="$SCRIPT_DIR/split_docs.sh"

if [ ! -f "$SPLIT_DOCS_SCRIPT" ]; then
	echo "Error: split_docs.sh not found at '$SPLIT_DOCS_SCRIPT'"
	exit 1
fi

mkdir -p "$OUTPUT_DIR"

count=0
failed=0

for inputFile in "$INPUT_DIR"/*; do
	[ -e "$inputFile" ] || continue
	[ -f "$inputFile" ] || continue

	filename=$(basename "$inputFile")
	echo "Processing: $filename"

	if bash "$SPLIT_DOCS_SCRIPT" "$inputFile" "$OUTPUT_DIR"; then
		((count++))
	else
		echo "Error: Failed processing $filename" >&2
		((failed++))
	fi
done

echo "======================="
echo "Processing complete!"
echo "Files processed: $count"
if [ $failed -gt 0 ]; then
	echo "Files failed: $failed"
fi
