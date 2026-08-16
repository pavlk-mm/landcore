#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# - clean (skeleton needed)
# - text2conllu (other formats, skeleton needed)
# - fix conllu (Udapi blocks)
# - score (skeleton needed)

skipClean=false
skipConllu=false
skipUnchunk=false
skipFix=false
skipScore=false
rmCleaned=false
rmConllu=false
rmUnchunked=false
rmFinal=false
mode="text2conllu"
format="txt"

usage() {
	echo "Usage: $0 [--format {txt,eml,json}] [--skipclean] [--skipconllu] [--skipunchunk] [--skipfix] [--skipscore] [--rmcleaned] [--rmconllu] [--rmunchunked] [--rmfinal] <annotated> <skeleton_conllu> <reference_conllu>"
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--format)
			case "$2" in
				txt)
					mode="text2conllu"
					format="txt"
					shift 2
					;;
				json)
					mode="json2conllu"
					format="json"
					shift 2
					;;
				eml)
					mode="eml2conllu"
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
		--skipclean)
			skipClean=true
			shift
			;;
		--skipconllu)
			skipConllu=true
			shift
			;;
		--skipunchunk)
			skipUnchunk=true
			shift
			;;
		--skipfix)
			skipFix=true
			shift
			;;
		--skipscore)
			skipScore=true
			shift
			;;
		--rmcleaned)
			rmCleaned=true
			shift
			;;
		--rmconllu)
			rmConllu=true
			shift
			;;
		--rmunchunked)
			rmUnchunked=true
			shift
			;;
		--rmfinal)
			rmFinal=true
			shift
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
			break
			;;
	esac
done

if [[ $# -ne 3 ]]; then
	echo "Expected 3 positional arguments, got $#" >&2
	usage
	exit 1
fi

annotated="$1"
skeletonConllu="$2"
referenceConllu="$3"

basename="${annotated%%-*}"
cleaned="${basename}-cleaned.${format}"
collu="${basename}-cleaned.conllu"
unchunked="${basename}-unchunked.conllu"
finalConllu="${basename}-final.conllu"
scores="${basename}-scores.txt"
generatedCleaned=false
generatedConllu=false
generatedUnchunked=false
generatedFinal=false

if "$skipClean"; then
	echo "Skipping cleaning step"
	cleaned="$annotated"
else
	echo "Cleaning annotated file: $annotated"
	python -m text2text_coref clean --format "$format" "$annotated" "$skeletonConllu" -o "$cleaned"
	generatedCleaned=true
fi

if "$skipConllu"; then
	echo "Skipping text2conllu step"
	collu="$cleaned"
else
	echo "Converting cleaned file to CoNLL-U format: $cleaned"
	python -m text2text_coref "$mode" "$cleaned" "$skeletonConllu" -o "$collu"
	generatedConllu=true
fi

if "$skipUnchunk"; then
	echo "Skipping unchunking step"
	unchunked="$collu"
else
	echo "Unchunking CoNLL-U file: $collu"
	udapy -s .postprocessing.Unchunk < "$collu" > "$unchunked"
	generatedUnchunked=true
fi

if "$skipFix"; then
	echo "Skipping Udapi fixing step"
	finalConllu="$unchunked"
else
	echo "Fixing CoNLL-U file with Udapi: $unchunked"
	udapy -s corefud.MergeSameSpan corefud.FixInterleaved same_entity_only=0 corefud.FixEntityAcrossNewdoc < "$unchunked" > "$finalConllu"
	generatedFinal=true
fi

if "$skipScore"; then
	echo "Skipping scoring step"
else
	echo "Scoring final CoNLL-U file against reference: $finalConllu vs $referenceConllu"
	python "$REPO_ROOT/corefud-scorer/corefud-scorer.py" "$referenceConllu" "$finalConllu" > "$scores"
fi

if "$rmCleaned" && "$generatedCleaned"; then
	echo "Removing intermediate cleaned file: $cleaned"
	rm -f "$cleaned"
fi

if "$rmConllu" && "$generatedConllu"; then
	echo "Removing intermediate CoNLL-U file: $collu"
	rm -f "$collu"
fi

if "$rmUnchunked" && "$generatedUnchunked"; then
	echo "Removing intermediate unchunked CoNLL-U file: $unchunked"
	rm -f "$unchunked"
fi

if "$rmFinal" && "$generatedFinal"; then
	echo "Removing intermediate final CoNLL-U file: $finalConllu"
	rm -f "$finalConllu"
fi
