#!/bin/bash

# Script to fix CoNLLU files using Udapi blocks.

inputDir="./outputs/first_automatic"
outputDir="./outputs/first_automatic"

# Create output directory if it doesn't exist
mkdir -p "$outputDir"

# Find all cleaned .txt files in cleaned directory
for inputFile in "$inputDir"/*-output.conllu; do
    # Extract the base name (e.g., "ko_ecmt" from "ko_ecmt-output.conllu")
    filename=$(basename "$inputFile")
    basename="${filename%-output.conllu}"

    echo "Processing: $basename"
    udapy -s corefud.MergeSameSpan corefud.FixEntityAcrossNewdoc < "$inputFile" > "$outputDir/${basename}-fixed_output.conllu"
    echo "  ✓ Completed"
done

echo "All files processed!"
