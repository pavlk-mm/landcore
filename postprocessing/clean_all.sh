#!/bin/bash

# Script to clean annotated files using text2text_coref

annotatedDir="./outputs/first_automatic"
skeletonDir="./data/crac_data_original/llm-input_blind-minidev"
outputDir="./outputs/first_automatic"

# Create output directory if it doesn't exist
mkdir -p "$outputDir"

# Find all annotated .txt files in annotated directory
for annotatedFile in "$annotatedDir"/*-annotated.txt; do
    # Extract the base name (e.g., "ko_ecmt" from "ko_ecmt-annotated.txt")
    filename=$(basename "$annotatedFile")
    basename="${filename%-annotated.txt}"
    
    # Construct the corresponding skeleton file name
    skeletonFileName="${basename}-corefud-minidev.conllu"
    skeletonFilePath="$skeletonDir/$skeletonFileName"
    
    # Check if the corresponding skeleton file exists
    if [ -f "$skeletonFilePath" ]; then
        annotatedFilePath="$annotatedFile"
        outputFileName="${basename}-cleaned.txt"
        outputFilePath="$outputDir/$outputFileName"
        
        echo "Processing: $basename"
        echo "  Annotated file: $annotatedFilePath"
        echo "  Skeleton file: $skeletonFilePath"
        echo "  Output file: $outputFilePath"
        
        # Run the cleaning command
        python -m text2text_coref clean "$annotatedFilePath" "$skeletonFilePath" -o "$outputFilePath"
        
        echo "  ✓ Completed"
        echo ""
    else
        echo "Warning: No corresponding skeleton file found for $basename" >&2
    fi
done

echo "All files processed!"
