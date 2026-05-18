#!/bin/bash

set -euo pipefail

SOURCE_DIR="${1:-./data/blind/dev/by_corpus}"
DEST_DIR="${2:-./configs/by_corpus}"
CONFIG_FILE="${3:-./configs/config_deepseek_whole_recall_prompt_reindexed_zero_longest_eml_3examples.yaml}"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' does not exist"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file '$CONFIG_FILE' does not exist"
    exit 1
fi

mkdir -p "$DEST_DIR"

count=0
config_name=$(basename "$CONFIG_FILE")

for corpus_dir in "$SOURCE_DIR"/*; do
    [ -d "$corpus_dir" ] || continue

    corpus_name=$(basename "$corpus_dir")
    target_dir="$DEST_DIR/$corpus_name"

    mkdir -p "$target_dir"
    cp "$CONFIG_FILE" "$target_dir/$config_name"

    count=$((count + 1))
done

if [ "$count" -eq 0 ]; then
    echo "No corpus subdirectories found in $SOURCE_DIR"
    exit 1
fi

echo "Copied $config_name into $count directories under $DEST_DIR"