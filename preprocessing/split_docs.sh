#!/bin/bash
# Script which splits the files by document, so that each document is in a
#separate file. This is useful for parallel processing of documents.

inputFile="$1"
outputDir="$2"
if [ -z "$inputFile" ] || [ -z "$outputDir" ]; then
	echo "Usage: $0 <input-file> <output-dir>"
	exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$outputDir"
basename=$(basename "$inputFile" .txt)

split -l 1 -d -a 3 --additional-suffix=.txt "$inputFile" "$outputDir/${basename}_"
