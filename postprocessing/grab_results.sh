#!/bin/bash

set -euo pipefail

usage() {
	cat <<'EOF'
Usage:
  grab_results.sh --output-dir DIR --old-suffix OLD --new-suffix NEW FILE [FILE...]

Description:
  Copies FILEs into DIR, renaming each basename by replacing OLD suffix with NEW,
  and creates a zip archive with all copied files.

Example:
  grab_results.sh \
    --output-dir ./outputs/final \
    --old-suffix -final.conllu \
    --new-suffix -corefud-minidev.conllu \
    ./outputs/run1/ca_ancora-final.conllu ./outputs/run1/cs_pdt-final.conllu
EOF
}

output_dir="."
old_suffix="-final.conllu"
new_suffix="-corefud-minidev.conllu"
input_files=()

while [[ $# -gt 0 ]]; do
	case "$1" in
		--output-dir)
			output_dir="$2"
			shift 2
			;;
		--old-suffix)
			old_suffix="$2"
			shift 2
			;;
		--new-suffix)
			new_suffix="$2"
			shift 2
			;;
		-h|--help)
			usage
			exit 0
			;;
		--)
			shift
			while [[ $# -gt 0 ]]; do
				input_files+=("$1")
				shift
			done
			;;
		-*)
			echo "Unknown option: $1" >&2
			usage >&2
			exit 1
			;;
		*)
			input_files+=("$1")
			shift
			;;
	esac
done

if [[ -z "$output_dir" || -z "$old_suffix" || -z "$new_suffix" || ${#input_files[@]} -eq 0 ]]; then
	echo "Missing required arguments." >&2
	usage >&2
	exit 1
fi

mkdir -p "$output_dir"

copied_files=()

for input_file in "${input_files[@]}"; do
	if [[ ! -f "$input_file" ]]; then
		echo "Input file does not exist: $input_file" >&2
		exit 1
	fi

	base_name="$(basename "$input_file")"
	if [[ "$base_name" != *"$old_suffix" ]]; then
		echo "Input file does not end with old suffix '$old_suffix': $input_file" >&2
		exit 1
	fi

	new_name="${base_name%"$old_suffix"}${new_suffix}"
	destination="$output_dir/$new_name"
	cp "$input_file" "$destination"
	copied_files+=("$new_name")
done

zip_name="$(basename "${output_dir%/}").zip"
zip_path="$output_dir/$zip_name"

if command -v zip >/dev/null 2>&1; then
	(
		cd "$output_dir"
		zip -q -r "$zip_name" "${copied_files[@]}"
	)
else
	python3 - <<'PY' "$output_dir" "$zip_path" "${copied_files[@]}"
import os
import sys
import zipfile

output_dir = sys.argv[1]
zip_path = sys.argv[2]
files = sys.argv[3:]

with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for name in files:
        archive.write(os.path.join(output_dir, name), arcname=name)
PY
fi

echo "Copied ${#copied_files[@]} files to '$output_dir' and created '$zip_path'."
