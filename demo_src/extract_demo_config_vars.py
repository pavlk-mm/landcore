import shlex
import sys
from pathlib import PurePosixPath

import yaml


def required(config, path):
    node = config
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            raise KeyError(path)
        node = node[key]
    if not isinstance(node, str) or not node:
        raise ValueError(path)
    return node


def derive_skeleton_conllu_dir(data_dir):
    parts = list(PurePosixPath(data_dir).parts)
    parts[-1] = "conllu"
    return str(PurePosixPath(*parts))


def derive_reference_conllu_dir(data_dir):
    if "test" in data_dir.lower():
        return ""  # No reference conllu for test split

    parts = list(PurePosixPath(data_dir).parts)
    if "blind" not in parts:
        raise ValueError(f"Expected 'blind' in data directory path: {data_dir}")
    parts[parts.index("blind")] = "gold"
    parts[-1] = "conllu"
    parts[-2] = "entire"
    return str(PurePosixPath(*parts))


def main():
    if len(sys.argv) != 2:
        print("Usage: python src/extract_demo_config_vars.py <config_path>", file=sys.stderr)
        return 1

    config_path = sys.argv[1]
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    try:
        annotation_format = required(config, "experiment.annotation_format")
        output_dir = required(config, "experiment.directory")
        examples_blind = required(config, "examples.directory_blind")
        examples_gold = required(config, "examples.directory_gold")
        data_dir = required(config, "data.directory")
        skeleton_conllus = derive_skeleton_conllu_dir(data_dir)
        reference_conllus = derive_reference_conllu_dir(data_dir)
        skip_score = "true" if "test" in data_dir else "false"
        skip_unchunk = "true" if "entire" in data_dir else "false"
    except (KeyError, ValueError) as exc:
        print(f"Failed to resolve required config values: {exc}", file=sys.stderr)
        return 1

    for name, value in [
        ("outputDir", output_dir),
        ("annotationFormat", annotation_format),
        ("examplesBlind", examples_blind),
        ("examplesGold", examples_gold),
        ("data", data_dir),
        ("skeletonConllus", skeleton_conllus),
        ("referenceConllus", reference_conllus),
        ("skipScore", skip_score),
        ("skipUnchunk", skip_unchunk),
    ]:
        print(f"{name}={shlex.quote(value)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
