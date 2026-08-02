#!/bin/bash

set -euo pipefail

output_dir=""
parallel=1
human_readable_json=false
mention_prefix="m"
store_mentions=false
input_files=()

usage() {
	echo "Usage: $0 [--output-dir <dir>] [--parallel <num>] [--human_readable_json] [--mention_prefix <prefix>] [--store_mentions] <input_eml> [input_eml ...]"
	echo ""
	echo "Options:"
	echo "  --output-dir <dir>         Output directory for generated .mml/.json files (default: same dir as input file)"
	echo "  --parallel <num>           Number of parallel conversions to run (default: 1)"
	echo "  --human_readable_json      Forward this flag to eml2mml.py"
	echo "  --mention_prefix <prefix>  Forward this flag to eml2mml.py (default: 'm')"
	echo "  --store_mentions		   Forward this flag to eml2mml.py (store mention text in JSON output)"
	echo "  -h, --help                 Show this help message"
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--output-dir)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for --output-dir" >&2
				usage
				exit 1
			fi
			output_dir="$2"
			shift 2
			;;
		--parallel)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for --parallel" >&2
				usage
				exit 1
			fi
			parallel="$2"
			if ! [[ "$parallel" =~ ^[1-9][0-9]*$ ]]; then
				echo "Invalid --parallel value: $parallel (must be a positive integer)" >&2
				exit 1
			fi
			shift 2
			;;
		--human_readable_json)
			human_readable_json=true
			shift
			;;
		--store_mentions)
			store_mentions=true
			shift
			;;
		-h|--help)
			usage
			exit 0
			;;
		--mention_prefix)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for --mention_prefix" >&2
				usage
				exit 1
			fi
			mention_prefix="$2"
			shift 2
			;;
		--*)
			echo "Unknown option: $1" >&2
			usage
			exit 1
			;;
		*)
			input_files+=("$1")
			shift
			;;
	esac
done

if [[ ${#input_files[@]} -eq 0 ]]; then
	echo "At least one input .eml file must be provided" >&2
	usage
	exit 1
fi

if [[ -n "$output_dir" ]]; then
	mkdir -p "$output_dir"
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
eml2mml_script="$script_dir/eml2mml.py"
project_dir="$(cd "$script_dir/.." && pwd)"

if [[ ! -f "$eml2mml_script" ]]; then
	echo "Cannot find eml2mml.py at: $eml2mml_script" >&2
	exit 1
fi

if [[ -n "${VIRTUAL_ENV:-}" ]] && [[ -x "$VIRTUAL_ENV/bin/python" ]]; then
	python_cmd="$VIRTUAL_ENV/bin/python"
elif [[ -x "$project_dir/.venv/bin/python" ]]; then
	python_cmd="$project_dir/.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
	python_cmd="python"
elif command -v python3 >/dev/null 2>&1; then
	python_cmd="python3"
else
	echo "Neither python nor python3 is available in PATH." >&2
	exit 1
fi

run_conversion() {
	local input_file="$1"

	if [[ ! -f "$input_file" ]]; then
		echo "Skipping missing input file: $input_file" >&2
		return 0
	fi

	if [[ "$input_file" != *.eml ]]; then
		echo "Skipping non-.eml file: $input_file" >&2
		return 0
	fi

	local base_name
	base_name="$(basename "$input_file" .eml)"

	local target_dir
	if [[ -n "$output_dir" ]]; then
		target_dir="$output_dir"
	else
		target_dir="$(dirname "$input_file")"
	fi

	local output_mml="$target_dir/$base_name.mml"
	local output_json="$target_dir/$base_name.json"

	local cmd=("$python_cmd" "$eml2mml_script" "$input_file" "$output_mml" "$output_json")
	if [[ "$human_readable_json" == true ]]; then
		cmd+=("--human_readable_json")
	fi
	if [[ -n "$mention_prefix" ]]; then
		cmd+=("--mention_prefix" "$mention_prefix")
	fi
	if [[ "$store_mentions" == true ]]; then
		cmd+=("--store_mentions")
	fi

	echo "Converting: $input_file"
	"${cmd[@]}"
	echo "  -> $output_mml"
	echo "  -> $output_json"
}

for input_file in "${input_files[@]}"; do
	run_conversion "$input_file" &
	if [[ $(jobs -r -p | wc -l) -ge $parallel ]]; then
		wait -n
	fi
done

wait
echo "All conversions completed."
