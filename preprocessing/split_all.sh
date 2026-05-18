#!/bin/bash
# Script for splitting all .txt files in a directory into multiple output splits

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPLIT_SCRIPT="$SCRIPT_DIR/split_data.py"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <directory> [--shuffle] [--split-ratio RATIO] [--format FORMAT] [--upper-bounds BOUNDS] [--seed SEED]"
    echo "  directory: Directory containing .txt files to split"
    echo "  --shuffle: Optional flag to shuffle data before splitting"
    echo "  --split-ratio: Optional ratios for n-1 splits, comma-separated (default: 0.125,0.125)"
    echo "  --format: Input format for split_data.py: txt|conllu (default: txt)"
    echo "  --upper-bounds: Optional upper bound(s) for n-1 splits, e.g. 10000"
    echo "  --seed: Random seed used when --shuffle is enabled (default: 42)"
    echo "  --output-dirs: Comma-separated output directories for each split (default: tuning,train)"
    echo "  --allow-empty-splits: Allow splits to be empty if split ratios are small"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIRS_CSV="tuning,small,train"

# Parse additional arguments
SHUFFLE_FLAG=""
SPLIT_RATIO="0.125,0.125"
FORMAT="txt"
UPPER_BOUNDS="25000,10000"
SEED="42"
ALLOW_EMPTY_SPLITS=""
shift
while [ $# -gt 0 ]; do
    case "$1" in
        --shuffle)
            SHUFFLE_FLAG="--shuffle"
            shift
            ;;
        --allow-empty-splits)
            ALLOW_EMPTY_SPLITS="--allow-empty-splits"
            shift
            ;;
        --split-ratio)
            SPLIT_RATIO="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --upper-bounds)
            UPPER_BOUNDS="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --output-dirs)
            OUTPUT_DIRS_CSV="$2"
            shift 2
            ;;
        *)
            echo "Error: Unknown argument '$1'"
            exit 1
            ;;
    esac
done

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Directory '$INPUT_DIR' does not exist"
    exit 1
fi

# Parse output directories and create them
IFS=',' read -r -a OUTPUT_DIRS <<< "$OUTPUT_DIRS_CSV"
if [ ${#OUTPUT_DIRS[@]} -eq 0 ]; then
    echo "Error: --output-dirs must contain at least one directory"
    exit 1
fi

for dir in "${OUTPUT_DIRS[@]}"; do
    if [ -z "$dir" ]; then
        echo "Error: --output-dirs contains an empty directory name"
        exit 1
    fi
    mkdir -p "$dir"
done

IFS=',' read -r -a SPLIT_RATIO_VALUES <<< "$SPLIT_RATIO"
expected_output_dirs=$((${#SPLIT_RATIO_VALUES[@]} + 1))
if [ ${#OUTPUT_DIRS[@]} -ne "$expected_output_dirs" ]; then
    echo "Error: --output-dirs must provide exactly $expected_output_dirs directories for split-ratio '$SPLIT_RATIO'"
    exit 1
fi

echo "Splitting files from: $INPUT_DIR"
echo "Output directories: $OUTPUT_DIRS_CSV"
echo "Split ratio: $SPLIT_RATIO"
echo "Format: $FORMAT"
if [ -n "$UPPER_BOUNDS" ]; then
    echo "Upper bounds: $UPPER_BOUNDS"
fi
if [ -n "$SHUFFLE_FLAG" ]; then
    echo "Shuffling: enabled"
    echo "Seed: $SEED"
fi
echo ""

# Counter for processed files
count=0

# Find and process all .txt files
for file in "$INPUT_DIR"/*.$FORMAT; do
    # Skip if no files match the pattern
    [ -e "$file" ] || continue
    
    filename=$(basename "$file")
    basename_no_ext="${filename%-train.$FORMAT}"
    
    split_output_files=()
    for i in "${!OUTPUT_DIRS[@]}"; do
        output_dir="${OUTPUT_DIRS[$i]}"
        split_output_files+=("$output_dir/${basename_no_ext}.$FORMAT")
    done
    
    echo "Processing: $filename"

    split_cmd=(
        python "$SPLIT_SCRIPT" "$file"
        --output-files "${split_output_files[@]}"
        --split-ratio "$SPLIT_RATIO"
        --format auto
        --seed "$SEED"
    )

    if [ -n "$UPPER_BOUNDS" ]; then
        split_cmd+=(--upper-bounds "$UPPER_BOUNDS")
    fi
    if [ -n "$SHUFFLE_FLAG" ]; then
        split_cmd+=(--shuffle)
    fi
    if [ -n "$ALLOW_EMPTY_SPLITS" ]; then
        split_cmd+=(--allow-empty-splits)
    fi
    if "${split_cmd[@]}"; then
        ((count++))
    else
        echo "Error processing $filename"
    fi
    echo ""
done

echo "======================="
echo "Processing complete!"
echo "Total files processed: $count"
