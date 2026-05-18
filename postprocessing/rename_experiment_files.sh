suffix="_b"
directory="."
shopt -s nullglob

usage() {
	echo "Usage: $0 [OPTIONS] DIRECTORY"
	echo "Options:"
    echo "  --suffix SUFFIX                Suffix to append to names (files and directories, default: '_b')"
	echo "  -h, --help                     Show this help message and exit"
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --suffix) suffix="$2"; shift ;;
        -h|--help) usage; exit 0 ;;
        *) directory="$1" ;;
    esac
    shift
done

for path in "$directory"/*; do
    if [[ -f "$path" ]]; then
        if [[ "$path" == *.* ]]; then
            base="${path%.*}"
            ext="${path##*.}"
            mv "$path" "${base}${suffix}.${ext}"
        else
            mv "$path" "${path}${suffix}"
        fi
    elif [[ -d "$path" ]]; then
        mv "$path" "${path}${suffix}"
    fi
done
