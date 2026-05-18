#!/bin/bash

set -euo pipefail

SOURCE_DIR="${1:-./data/blind/dev/chunked_1500}"
DEST_DIR="${2:-./data/blind/dev/chunked_1500/by_corpus}"
SUFFIX="-chunked.txt"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' does not exist"
    exit 1
fi

mkdir -p "$DEST_DIR"

count=0

for file in "$SOURCE_DIR"/*"$SUFFIX"; do
    [ -e "$file" ] || continue

    filename=$(basename "$file")
    corpus_name="${filename%$SUFFIX}"
    corpus_dir="$DEST_DIR/$corpus_name"

    mkdir -p "$corpus_dir"
    cp "$file" "$corpus_dir/$filename"

    count=$((count + 1))
done

if [ "$count" -eq 0 ]; then
    echo "No files matching '*$SUFFIX' found in $SOURCE_DIR"
    exit 1
fi

echo "Copied $count files to $DEST_DIR"