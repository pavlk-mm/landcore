#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat <<'EOF'
Usage:
	copy_rename_suffix.sh --old-suffix SUFFIX --new-suffix SUFFIX FILE [FILE ...]

Description:
	Renames each provided file by replacing --old-suffix with --new-suffix
	at the end of its filename.

Options:
	--old-suffix, ----old-suffix  Suffix to replace (must match filename end)
	--new-suffix                   Replacement suffix
EOF
}

old_suffix=""
new_suffix=""
files=()

while [[ $# -gt 0 ]]; do
	case "$1" in
		--old-suffix|----old-suffix)
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
				files+=("$1")
				shift
			done
			;;
		-*)
			echo "Unknown argument: $1" >&2
			usage >&2
			exit 2
			;;
		*)
			files+=("$1")
			shift
			;;
	esac
done

if [[ -z "$old_suffix" || -z "$new_suffix" || ${#files[@]} -eq 0 ]]; then
	echo "Missing required arguments." >&2
	usage >&2
	exit 2
fi

renamed_count=0

for path in "${files[@]}"; do
	if [[ ! -f "$path" ]]; then
		echo "Skipping '$path': file does not exist." >&2
		continue
	fi

	dir="$(dirname "$path")"
	base="$(basename "$path")"
	if [[ "$base" != *"$old_suffix" ]]; then
		echo "Skipping '$base': does not end with '$old_suffix'." >&2
		continue
	fi
	new_base="${base%$old_suffix}$new_suffix"
	mv "$path" "$dir/$new_base"
	renamed_count=$((renamed_count + 1))
done

if [[ $renamed_count -eq 0 ]]; then
	echo "No files were renamed." >&2
	exit 1
fi
