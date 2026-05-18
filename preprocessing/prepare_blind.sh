#!/bin/bash
# Script for creating blind versions of CoNLL-U files using text2text_coref

if [ $# -lt 2 ]; then
    echo "Usage: $0 <input-directory> <blind-directory>"
    echo "  input-directory: Directory containing .conllu files to blindify"
    echo "  blind-directory: Output directory for blind .txt files"
    exit 1
fi

INPUT_DIR="$1"
BLIND_DIR="$2"

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Directory '$INPUT_DIR' does not exist"
    exit 1
fi

# Create blind output directory
mkdir -p "$BLIND_DIR"

echo "Creating blind versions from: $INPUT_DIR"
echo "Output directory: $BLIND_DIR"
echo ""

# Counter for processed files
count=0
failed=0

# Find and process all .conllu files
for file in "$INPUT_DIR"/*.conllu; do
    # Skip if no files match the pattern
    [ -e "$file" ] || continue
    
    filename=$(basename "$file")
    output_file="$BLIND_DIR/${filename%.conllu}.txt"
    
    echo "Processing: $filename"
    
    if text2text_coref conllu2text "$file" --blind -o "$output_file"; then
        ((count++))
        echo "  -> $output_file"
    else
        echo "  Error: Failed to process $filename"
        ((failed++))
    fi
    echo ""
done

echo "======================="
echo "Processing complete!"
echo "Total files processed: $count"
if [ $failed -gt 0 ]; then
    echo "Failed: $failed"
fi
