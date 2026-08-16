#!/bin/bash

config="configs/final_deepseek.yaml"
orApiKey=""
orModel=""

usage() {
	echo "Usage: $0 [--config <path>] [--or-api-key <key>] [--or-model <model>]"
	echo ""
	echo "Options:"
	echo "  -c, --config <path>   Path to YAML config file (default: configs/final_deepseek.yaml)"
	echo "      --or-api-key <key> OpenRouter API key forwarded to annotation as --api_key"
	echo "      --or-model <model> Model override forwarded to annotation as --model"
	echo "  -h, --help            Show this help message"
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
	case "$1" in
		-c|--config)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for $1" >&2
				usage
				exit 1
			fi
			config="$2"
			shift 2
			;;
		--or-api-key)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for $1" >&2
				usage
				exit 1
			fi
			orApiKey="$2"
			shift 2
			;;
		--or-model)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for $1" >&2
				usage
				exit 1
			fi
			orModel="$2"
			shift 2
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "Unknown option: $1" >&2
			usage
			exit 1
			;;
	esac
done

if [[ ! -f "$config" ]]; then
	echo "Config file not found: $config" >&2
	exit 1
fi

# Load configuration variables from the config file
eval "$(python demo_src/extract_demo_config_vars.py "$config")"
echo "Loaded configuration from $config:"
echo "examplesBlind: $examplesBlind"
echo "examplesGold: $examplesGold"
echo "data: $data"
echo "skeletonConllus: $skeletonConllus"
echo "referenceConllus: $referenceConllus"
echo "annotationFormat: $annotationFormat"
echo "skipScore: $skipScore"
echo "skipUnchunk: $skipUnchunk"
echo "outputDir: $outputDir"
suffix="-annotated.$annotationFormat"

# Preprocessing with make
for fileDir in "$examplesBlind" "$examplesGold" "$data" "$skeletonConllus" "$referenceConllus"; do
	[[ -n "$fileDir" ]] || continue
	make -f data/Makefile "$fileDir"
done

# Annotation
annotationArgs=(--config "$config")
if [[ -n "$orApiKey" ]]; then
	annotationArgs+=(--api_key "$orApiKey")
fi
if [[ -n "$orModel" ]]; then
	annotationArgs+=(--model "$orModel")
fi
#python src/landcore.py "${annotationArgs[@]}" ##--print_config

# Postprocessing
postprocessArgs=(
	--suffix "$suffix"
	--skeleton-dir "$skeletonConllus"
	--reference-dir "$referenceConllus"
	--format "$annotationFormat"
)
if [[ "$skipScore" == "true" ]]; then
	echo "Skipping scoring step as per configuration."
	postprocessArgs+=(--skipscore)
fi
if [[ "$skipUnchunk" == "true" ]]; then
	echo "Skipping unchunking step as per configuration."
	postprocessArgs+=(--skipunchunk)
fi
postprocessArgs+=("$outputDir/results/ca_ancora$suffix")

bash postprocessing/postprocess_all.sh "${postprocessArgs[@]}"
