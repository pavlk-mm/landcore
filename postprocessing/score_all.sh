#!/bin/bash
# Run corefud-scorer on all .conllu files in key and system directories

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ $# -ne 2 ]; then
    echo "Usage: $0 <key_dir> <system_dir>"
    exit 1
fi

KEY_DIR="$1"
SYSTEM_DIR="$2"

if [ ! -d "$KEY_DIR" ]; then
    echo "Error: Key directory '$KEY_DIR' does not exist"
    exit 1
fi

if [ ! -d "$SYSTEM_DIR" ]; then
    echo "Error: System directory '$SYSTEM_DIR' does not exist"
    exit 1
fi

# Collect key files
key_files=("$KEY_DIR"/*.conllu)
if [ ! -e "${key_files[0]}" ]; then
    echo "Error: No .conllu files found in '$KEY_DIR'"
    exit 1
fi

# Build a quick lookup for system files by corpus name
# System files are named: <corpus>-fixed_output.conllu
declare -A system_map
for sys_file in "$SYSTEM_DIR"/*-fixed_output.conllu; do
    [ -e "$sys_file" ] || continue
    sys_base=$(basename "$sys_file")
    corpus="${sys_base%-fixed_output.conllu}"
    system_map["$corpus"]="$sys_file"
done

count=0
missing=0

# Key files are named: <corpus>-corefud-minidev.conllu
for key_file in "${key_files[@]}"; do
    key_base=$(basename "$key_file")
    corpus="${key_base%-corefud-minidev.conllu}"
    
    # Handle case where file doesn't match expected pattern
    if [ "$corpus" == "$key_base" ]; then
        corpus="${key_base%.conllu}"
    fi
    
    system_file="${system_map[$corpus]}"

    if [ -n "$system_file" ]; then
        echo "Scoring: $corpus"
        echo "  Key: $key_base"
        echo "  System: $(basename "$system_file")"
        python "$REPO_ROOT/corefud-scorer/corefud-scorer.py" "$key_file" "$system_file" > "${system_file%-fixed_output.conllu}-fixed_output_scores.txt"
        echo ""
        ((count++))
    else
        echo "Warning: No matching system file for $corpus (key: $key_base)" >&2
        ((missing++))
    fi
done

echo "======================="
echo "Scoring complete!"
echo "Matched pairs scored: $count"
if [ $missing -gt 0 ]; then
    echo "Missing system files: $missing"
fi
