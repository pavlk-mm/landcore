#!/bin/bash
# Copy all .txt files from one directory to another

if [ $# -ne 2 ]; then
    echo "Usage: $0 <source_dir> <dest_dir>"
    exit 1
fi

SOURCE_DIR="$1"
DEST_DIR="$2"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' does not exist"
    exit 1
fi

mkdir -p "$DEST_DIR"

count=0
for file in "$SOURCE_DIR"/*.txt; do
    [ -e "$file" ] || continue
    cp "$file" "$DEST_DIR/"
    ((count++))
done

echo "Copied $count .txt files to $DEST_DIR"
