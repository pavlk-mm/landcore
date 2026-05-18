#!/bin/bash

# Script to convert cleaned text to CoNLL-U format using text2text_coref

cleanedDir="./outputs/first_automatic"
skeletonDir="./data/crac_data_original/llm-input_blind-minidev"
outputDir="./outputs/first_automatic"

# Create output directory if it doesn't exist
mkdir -p "$outputDir"

# Find all cleaned .txt files in cleaned directory
for cleanedFile in "$cleanedDir"/*-cleaned.txt; do
    # Extract the base name (e.g., "ko_ecmt" from "ko_ecmt-cleaned.txt")
    filename=$(basename "$cleanedFile")
    basename="${filename%-cleaned.txt}"
    
    # Construct the corresponding skeleton file name
    skeletonFileName="${basename}-corefud-minidev.conllu"
    skeletonFilePath="$skeletonDir/$skeletonFileName"
    
    # Check if the corresponding skeleton file exists
    if [ -f "$skeletonFilePath" ]; then
        cleanedFilePath="$cleanedFile"
        outputFileName="${basename}-output.conllu"
        outputFilePath="$outputDir/$outputFileName"
        
        echo "Processing: $basename"
        echo "  Cleaned file: $cleanedFilePath"
        echo "  Skeleton file: $skeletonFilePath"
        echo "  Output file: $outputFilePath"
        
        # Run the text2conllu command
        python -m text2text_coref text2conllu "$cleanedFilePath" "$skeletonFilePath" -o "$outputFilePath"
        
        echo "  ✓ Completed"
        echo ""
    else
        echo "Warning: No corresponding skeleton file found for $basename" >&2
    fi
done

echo "All files processed!"
