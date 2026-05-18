from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TAG_PATTERN = re.compile(r"</?e(\d+)>")


def entity_sort_key(entity_id: str) -> int:
	return int(entity_id[1:])


def sort_clustering_entities(clustering: dict[str, list[str]]) -> dict[str, list[str]]:
	return {entity_id: clustering[entity_id] for entity_id in sorted(clustering, key=entity_sort_key)}


def convert_document(document: str, doc_index: int) -> tuple[str, dict[str, list[str]]]:
	"""Convert one EML document into MML and produce mention clustering."""
	next_mention_id = 1
	open_stack: list[tuple[str, str]] = []
	clustering: dict[str, list[str]] = {}
	result: list[str] = []

	last_end = 0
	for match in TAG_PATTERN.finditer(document):
		result.append(document[last_end:match.start()])

		tag_text = match.group(0)
		entity_num = match.group(1)
		entity_id = f"e{entity_num}"

		if tag_text.startswith("</"):
			if not open_stack:
				raise ValueError(
					f"Document {doc_index}: unmatched closing tag {tag_text}."
				)

			open_entity_id, mention_id = open_stack.pop()
			if open_entity_id != entity_id:
				raise ValueError(
					f"Document {doc_index}: mismatched closing tag {tag_text}, expected </{open_entity_id}>."
				)

			result.append(f"</{mention_id}>")
		else:
			mention_id = f"m{next_mention_id}"
			next_mention_id += 1

			open_stack.append((entity_id, mention_id))
			clustering.setdefault(entity_id, []).append(mention_id)
			result.append(f"<{mention_id}>")

		last_end = match.end()

	result.append(document[last_end:])

	if open_stack:
		unclosed_entities = sorted({entity for entity, _ in open_stack})
		raise ValueError(
			f"Document {doc_index}: unclosed tags for entities {', '.join(sorted(unclosed_entities))}."
		)

	return "".join(result), clustering


def format_clusterings_json(clusterings: list[dict[str, list[str]]], human_readable: bool) -> str:
	sorted_clusterings = [sort_clustering_entities(clustering) for clustering in clusterings]

	if not human_readable:
		return json.dumps(sorted_clusterings, ensure_ascii=False) + "\n"

	# Keep valid JSON with one entity mapping per line inside each document cluster object.
	lines = ["["]
	for index, clustering in enumerate(sorted_clusterings):
		suffix = "," if index < len(sorted_clusterings) - 1 else ""
		lines.append("\t{")
		items = list(clustering.items())
		for item_index, (entity_id, mentions) in enumerate(items):
			item_suffix = "," if item_index < len(items) - 1 else ""
			mentions_json = json.dumps(mentions, ensure_ascii=False)
			lines.append(f'\t\t"{entity_id}": {mentions_json}{item_suffix}')
		lines.append(f"\t}}{suffix}")
	lines.append("]")
	return "\n".join(lines) + "\n"


def convert_file(
	input_path: Path,
	output_mml_path: Path,
	output_json_path: Path,
	human_readable_json: bool = False,
) -> None:
	lines = input_path.read_text(encoding="utf-8").splitlines()

	converted_documents: list[str] = []
	clusterings: list[dict[str, list[str]]] = []

	for doc_index, line in enumerate(lines, start=1):
		converted, clustering = convert_document(line, doc_index)
		converted_documents.append(converted)
		clusterings.append(clustering)

	output_mml_path.write_text("\n".join(converted_documents) + "\n", encoding="utf-8")
	output_json_path.write_text(
		format_clusterings_json(clusterings, human_readable_json),
		encoding="utf-8",
	)


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Convert EML files to MML with per-document mention IDs and clustering JSON."
	)
	parser.add_argument("input_eml", type=Path, help="Input EML file path")
	parser.add_argument("output_mml", type=Path, help="Output MML file path")
	parser.add_argument("output_json", type=Path, help="Output clustering JSON file path")
	parser.add_argument(
		"--human_readable_json",
		action="store_true",
		help="Write JSON with one entity mapping per line inside each document cluster object.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	convert_file(
		args.input_eml,
		args.output_mml,
		args.output_json,
		human_readable_json=args.human_readable_json,
	)


if __name__ == "__main__":
	main()
