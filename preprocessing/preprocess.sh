#!/bin/bash

# - chunk docs (Udapi block)
# - conllu2text (other formats)

skipChunk=false
skipText=false
skipReindex=true
blind=false
words=500
mode="conllu2text"
format="txt"

usage() {
	echo "Usage: $0 [--skipchunk] [--skiptext] [--skipreindex] [--blind] [--words <num>] [--format {txt,json,eml}] <input-file> <output-dir>"
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--skipchunk)
			skipChunk=true
			shift
			;;
		--skiptext)
			skipText=true
			shift
			;;
		-h|--help)
			usage
			exit 0
			;;
		--blind)
			blind=true
			shift
			;;
		--words)
			words="$2"
			shift 2
			;;
		--skipreindex)
			skipReindex=true
			shift
			;;
		--format)
			case "$2" in
				txt)
					mode="conllu2text"
					format="txt"
					shift 2
					;;
				json)
					mode="conllu2json"
					format="json"
					shift 2
					;;
				eml)
					mode="conllu2eml"
					format="eml"
					shift 2
					;;
				*)
					echo "Invalid format: $2" >&2
					usage
					exit 1
					;;
			esac
			;;
		--*)
			echo "Unknown option: $1" >&2
			usage
			exit 1
			;;
		*)
			break
			;;
	esac
done

if [[ $# -lt 2 ]]; then
	usage
	exit 1
fi

input_file="$1"
output_dir="$2"

if [ ! -f "$output_dir" ]; then
	mkdir -p "$output_dir"
fi

name="$(basename "$input_file")"
name="${name%%-*}"
chunked="${output_dir}/${name}-chunked.conllu"
reindexed="${output_dir}/${name}-reindexed.conllu"
text="${output_dir}/${name}-chunked_reindexed.${format}"

if "$skipChunk"; then
	echo "Skipping chunking step"
	chunked="$input_file"
else
	echo "Chunking documents in $input_file to $chunked"
	udapy -s .preprocessing.DeleteBridgingAndSplitAntes .preprocessing.Chunker words="$words" <"$input_file" >"$chunked"
fi


if "$skipReindex"; then
	echo "Skipping reindexing step"
	reindexed="$chunked"
else
	echo "Reindexing entities inCoNLL-U file: $chunked"
	udapy -s corefud.IndexClusters < "$chunked" > "$reindexed"
fi

if "$skipText"; then
	echo "Skipping text extraction step"
	text="$reindexed"
else
	echo "Extracting text from $reindexed to $text"
	if "$blind"; then
		python -m text2text_coref "$mode" "$reindexed" --blind -o "$text"
	else
		python -m text2text_coref "$mode" "$reindexed" --sequential_ids --zero_mentions -o "$text"
	fi
fi
