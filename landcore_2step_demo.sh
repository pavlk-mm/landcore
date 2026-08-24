#!/bin/bash

config="configs/final_2step.yaml"
orApiKey=""
orModel=""

usage() {
	echo "Usage: $0 [--config <path>] [--or-api-key <key>] [--or-model <model>]"
	echo ""
	echo "Options:"
	echo "  -c, --config <path>   Path to YAML config file (default: configs/final_2step.yaml)"
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
echo "    examplesBlind: $examplesBlind"
echo "    examplesGold: $examplesGold"
echo "    data: $data"
echo "    skeletonConllus: $skeletonConllus"
echo "    referenceConllus: $referenceConllus"
echo "    annotationFormat: $annotationFormat"
echo "    skipScore: $skipScore"
echo "    skipUnchunk: $skipUnchunk"
echo "    outputDir: $outputDir"
suffix="-annotated.$annotationFormat"
intermediateFormat="mml"
examplesIntermediate="${examplesGold%/}"
if [[ "${examplesIntermediate##*/}" == "$annotationFormat" ]]; then
	examplesIntermediate="${examplesIntermediate%/*}/$intermediateFormat"
else
	echo "Expected examplesGold to end with '$annotationFormat', got: $examplesGold" >&2
	exit 1
fi
intermediateOutputDir="$outputDir/$intermediateFormat"
dataIntermediate="$intermediateOutputDir/results"
promptIdentification="prompt_templates/mention_identification.txt"

# Preprocessing with make
echo "PREPROCESSING..."
for fileDir in "$examplesBlind" "$examplesGold" "$examplesIntermediate" "$data" "$skeletonConllus" "$referenceConllus"; do
	[[ -n "$fileDir" ]] || continue
	make -f data/Makefile "$fileDir"
done

# Annotation
echo "ANNOTATION..."
echo "Mention identification..."
annotationArgs=(--config "$config")
if [[ -n "$orApiKey" ]]; then
	annotationArgs+=(--api_key "$orApiKey")
fi
if [[ -n "$orModel" ]]; then
	annotationArgs+=(--model "$orModel")
fi
annotationArgs+=(--output_dir "$intermediateOutputDir")
annotationArgs+=(--annotation_format "$intermediateFormat")
annotationArgs+=(--examples_directory_gold "$examplesIntermediate")
annotationArgs+=(--prompt_template "$promptIdentification")
python src/landcore.py "${annotationArgs[@]}" #--print_config

echo "Mention clustering..."
annotationArgs=(--config "$config")
if [[ -n "$orApiKey" ]]; then
	annotationArgs+=(--api_key "$orApiKey")
fi
if [[ -n "$orModel" ]]; then
	annotationArgs+=(--model "$orModel")
fi
annotationArgs+=(--examples_directory_blind "$examplesIntermediate")
annotationArgs+=(--data_directory "$dataIntermediate")
python src/landcore.py "${annotationArgs[@]}" #--print_config

# Postprocessing
echo "POSTPROCESSING..."
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
shopt -s nullglob
resultFiles=("$outputDir"/results/*"$suffix")
shopt -u nullglob

if [[ ${#resultFiles[@]} -eq 0 ]]; then
	echo "No result files found for pattern: $outputDir/results/*$suffix" >&2
	exit 1
fi

postprocessArgs+=("${resultFiles[@]}")

bash postprocessing/postprocess_all.sh "${postprocessArgs[@]}"
