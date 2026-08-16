#!/bin/bash


export PYTHONPATH="."

suffix="-annotated.eml"
skeletonDir="data/crac_data_original/llm-gold-minidev"
referenceDir="data/crac_data_original/llm-gold-minidev"
skeletonSuffix="-corefud.conllu"
referenceSuffix="-corefud.conllu"
parallel=4
skipScore=false

usage() {
    echo "Usage: $0 [--suffix <suffix>] [--skeleton-dir <dir>] [--reference-dir <dir>] [--skeleton-suffix <suffix>] [--reference-suffix <suffix>] [--parallel <num>] [--skipscore] [postprocess options] <annotated_file> [annotated_file ...]"
    echo ""
    echo "Wrapper options:"
    echo "  --suffix <suffix>          Suffix removed from each input filename (default: -annotated.eml)"
    echo "  --skeleton-dir <dir>       Directory for auto-constructed skeleton files (default: data/crac_data_original/llm-gold-minidev)"
    echo "  --reference-dir <dir>      Directory for auto-constructed reference files (default: data/crac_data_original/llm-gold-minidev)"
    echo "  --skeleton-suffix <suffix> Suffix appended to base for skeleton files (default: -corefud.conllu)"
    echo "  --reference-suffix <suffix> Suffix appended to base for reference files (default: -corefud.conllu)"
    echo "  --parallel <num>           Number of parallel processes (default: 4)"
    echo "  --skipscore               Skip scoring step and generating tables (default: false)"
    echo ""
    echo "Auto construction:"
    echo "  base = input filename without <suffix>"
    echo "  skeleton = <skeleton-dir>/<base><skeleton-suffix>"
    echo "  reference = <reference-dir>/<base><reference-suffix>"
    echo ""
    echo "Any other --option is forwarded to postprocess.sh (e.g. --skipclean, --skipscore, --rmcleaned)."
}

postprocessOptions=()
annotatedFiles=()

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
        --skeleton-dir)
            if [[ $# -lt 2 ]]; then
                echo "Missing value for --skeleton-dir" >&2
                usage
                exit 1
            fi
            skeletonDir="$2"
            shift 2
            ;;
        --reference-dir)
            if [[ $# -lt 2 ]]; then
                echo "Missing value for --reference-dir" >&2
                usage
                exit 1
            fi
            referenceDir="$2"
            shift 2
            ;;
        --skeleton-suffix)
            if [[ $# -lt 2 ]]; then
                echo "Missing value for --skeleton-suffix" >&2
                usage
                exit 1
            fi
            skeletonSuffix="$2"
            shift 2
            ;;
        --reference-suffix)
            if [[ $# -lt 2 ]]; then
                echo "Missing value for --reference-suffix" >&2
                usage
                exit 1
            fi
            referenceSuffix="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --skipscore)
            skipScore=true
            postprocessOptions+=("--skipscore")
            shift
            ;;
        --parallel)
            if [[ $# -lt 2 ]]; then
                echo "Missing value for --parallel" >&2
                usage
                exit 1
            fi
            parallel="$2"
            shift 2
            ;;
		--format)
			if [[ $# -lt 2 ]]; then
				echo "Missing value for --format" >&2
				usage
				exit 1
			fi
			if [[ "$2" != "txt" && "$2" != "json" && "$2" != "eml" && "$2" != "conllu" ]]; then
				echo "Invalid value for --format: $2 (expected: txt, json, eml, conllu)" >&2
				usage
				exit 1
			fi
			postprocessOptions+=("$1" "$2")
			shift 2
			;;
        --*)
            postprocessOptions+=("$1")
            shift
            ;;
        *)
            annotatedFiles+=("$1")
            shift
            ;;
    esac
done

if [[ ${#annotatedFiles[@]} -eq 0 ]]; then
    echo "At least one annotated file must be provided" >&2
    usage
    exit 1
fi

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
postprocessScript="$scriptDir/postprocess.sh"
aggregateScoreScript="$scriptDir/aggregate_scores.py"
oneTableScript="$scriptDir/scores_json_to_tex.py"
allTableScript="$scriptDir/scores_to_tex.py"
appendTableScript="$scriptDir/append_table_block.py"
metricsTabeleScript="$scriptDir/scores_to_tex_by_metric.py"

if [[ ! -f "$postprocessScript" ]]; then
    echo "Cannot find postprocess.sh at: $postprocessScript" >&2
    exit 1
fi

for annotated in "${annotatedFiles[@]}"; do
    if [[ ! -f "$annotated" ]]; then
        echo "Skipping missing input file: $annotated" >&2
        continue
    fi

    filename="$(basename "$annotated")"

    if [[ "$filename" != *"$suffix" ]]; then
        echo "Skipping file with unexpected suffix: $annotated (expected suffix: $suffix)" >&2
        continue
    fi

    base="${filename%$suffix}"
    skeletonConllu="$skeletonDir/$base$skeletonSuffix"
    referenceConllu="$referenceDir/$base$referenceSuffix"

    if [[ ! -f "$skeletonConllu" ]]; then
        echo "Skipping $annotated: skeleton file not found: $skeletonConllu" >&2
        continue
    fi

    if [[ ! -f "$referenceConllu" ]]; then
        echo "Skipping $annotated: reference file not found: $referenceConllu" >&2
        continue
    fi

    echo "Processing: $annotated"
    echo "  Skeleton:  $skeletonConllu"
    echo "  Reference: $referenceConllu"
    "$postprocessScript" "${postprocessOptions[@]}" "$annotated" "$skeletonConllu" "$referenceConllu" &> "${annotated%.txt}.log" &
    status=$?
    
    # Limit parallel processes
    if [[ $(jobs -r -p | wc -l) -ge $parallel ]]; then
        wait -n
    fi

    if [[ $status -ne 0 ]]; then
        echo "Failed processing $annotated (exit code: $status)" >&2
    fi
done
wait

if [[ "$skipScore" == true ]]; then
    echo "Skipping scoring and table generation as per --skipscore option."
    exit 0
fi

if [[ ! -f "$aggregateScoreScript" ]]; then
    echo "Cannot find aggregate_scores.py at: $aggregateScoreScript" >&2
    exit 1
fi
directory="$(dirname "${annotatedFiles[0]}")"
experimentDirectory="$(dirname "$directory")"
experimentName="$(basename "$experimentDirectory")"
aggregatedTablesDirectory="$(dirname "$experimentDirectory")"

python "$aggregateScoreScript" --root "$directory" --output "$experimentDirectory/scores.json"

if [[ ! -f "$oneTableScript" ]]; then
    echo "Cannot find scores_json_to_tex.py at: $oneTableScript" >&2
    exit 1
fi
python "$oneTableScript" --include-conll "$experimentDirectory/scores.json" --output "$experimentDirectory/scores-table.tex"

if [[ ! -f "$allTableScript" ]]; then
    echo "Cannot find scores_to_tex.py at: $allTableScript" >&2
    exit 1
fi
python "$allTableScript" --include-conll --root "$aggregatedTablesDirectory" --output "$aggregatedTablesDirectory/scores-table.tex"

if [[ ! -f "$appendTableScript" ]]; then
    echo "Cannot find append_table_block.py at: $appendTableScript" >&2
    exit 1
fi
# echo "$directory"
# echo "$(dirname "$directory")"
tableCaption=${experimentName//_/\\_}
echo "Appending table block for experiment: $experimentName"
python "$appendTableScript" --target "$aggregatedTablesDirectory/individual-tables.tex" --input-path "$experimentName/scores-table.tex" --caption "F1 / P / R scores for each corpus. $tableCaption"

if [[ ! -f "$metricsTabeleScript" ]]; then
    echo "Cannot find scores_by_metric_to_tex.py at: $metricsTabeleScript" >&2
    exit 1
fi
python "$metricsTabeleScript" --root "$aggregatedTablesDirectory" --output "$aggregatedTablesDirectory/scores-by-metric-tables.tex" --size tiny --digits 0
