#!/bin/bash

suffix="-corefud.conllu"
outputDir="."
parallel=4

usage() {
	echo "Usage: $0 [--suffix <suffix>] [--output-dir <dir>] [--parallel <num>] [preprocess options] <input_file> [input_file ...]"
	echo ""
	echo "Wrapper options:"
	echo "  --suffix <suffix>          Suffix removed from each input filename (default: -corefud.conllu)"
	echo "  --output-dir <dir>         Shared output directory for all input files (default: .)"
	echo "  --parallel <num>           Number of parallel processes (default: 4)"
	echo ""
	echo "Preprocess options forwarded to preprocess.sh: --skipchunk, --skiptext, --blind, --skipreindex, --format {txt,json,eml} --words <num>"
}

preprocessOptions=()
inputFiles=()

while [[ $# -gt 0 ]]; do
	case "$1" in
		--suffix)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for --suffix" >&2
				usage
				exit 1
			fi
			suffix="$2"
			shift 2
			;;
		--output-dir)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for --output-dir" >&2
				usage
				exit 1
			fi
			outputDir="$2"
			shift 2
			;;
		--skipchunk|--skiptext|--blind|--skipreindex)
			preprocessOptions+=("$1")
			shift
			;;
		--words)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for --words" >&2
				usage
				exit 1
			fi
			preprocessOptions+=("$1" "$2")
			shift 2
			;;
		--format)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for --format" >&2
				usage
				exit 1
			fi
			if [[ "$2" != "txt" && "$2" != "json" && "$2" != "eml" ]]; then
				echo "Invalid value for --format: $2 (expected: txt, json, eml)" >&2
				usage
				exit 1
			fi
			preprocessOptions+=("$1" "$2")
			shift 2
			;;
		-h|--help)
			usage
			exit 0
			;;
		--*)
			echo "Unknown option: $1" >&2
			usage
			exit 1
			;;
		*)
			inputFiles+=("$1")
			shift
			;;
	esac
done

if [ ! -d "$outputDir" ]; then
	mkdir -p "$outputDir"
fi

if [[ ${#inputFiles[@]} -eq 0 ]]; then
	echo "At least one input file must be provided" >&2
	usage
	exit 1
fi

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
preprocessScript="$scriptDir/preprocess.sh"

if [[ ! -f "$preprocessScript" ]]; then
	echo "Cannot find preprocess.sh at: $preprocessScript" >&2
	exit 1
fi

for inputFile in "${inputFiles[@]}"; do
	if [[ ! -f "$inputFile" ]]; then
		echo "Skipping missing input file: $inputFile" >&2
		continue
	fi

	filename="$(basename "$inputFile")"

	if [[ "$filename" != *"$suffix" ]]; then
		echo "Skipping file with unexpected suffix: $inputFile (expected suffix: $suffix)" >&2
		continue
	fi

	echo "Processing: $inputFile"
	echo "  Output dir: $outputDir"

	"$preprocessScript" "${preprocessOptions[@]}" "$inputFile" "$outputDir" &>"$outputDir/${filename%.conllu}.log" &
	status=$?

    # Limit parallel processes
    if [[ $(jobs -r -p | wc -l) -ge $parallel ]]; then
        wait -n
    fi

	if [[ $status -ne 0 ]]; then
		echo "Failed processing $inputFile (exit code: $status)" >&2
	fi
done

wait
echo "All preprocessing tasks completed."
