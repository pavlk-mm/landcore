from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TAG_PATTERN = re.compile(r"</?m(\d+)>")


def build_mention_to_entity(clustering: dict[str, list[str]], doc_index: int) -> dict[str, str]:
	mention_to_entity: dict[str, str] = {}
	for entity_id, mentions in clustering.items():
		for mention_id in mentions:
			if mention_id in mention_to_entity:
				raise ValueError(
					f"Document {doc_index}: mention {mention_id} appears in multiple clusters ({mention_to_entity[mention_id]} and {entity_id})."
				)
			mention_to_entity[mention_id] = entity_id
	return mention_to_entity


def convert_document(document: str, mention_to_entity: dict[str, str], doc_index: int) -> str:
	result: list[str] = []
	open_stack: list[str] = []
	seen_mentions: set[str] = set()

	last_end = 0
	for match in TAG_PATTERN.finditer(document):
		result.append(document[last_end:match.start()])

		tag_text = match.group(0)
		mention_id = f"m{match.group(1)}"

		if mention_id not in mention_to_entity:
			raise ValueError(
				f"Document {doc_index}: mention {mention_id} not found in clustering JSON."
			)
		entity_id = mention_to_entity[mention_id]
		seen_mentions.add(mention_id)

		if tag_text.startswith("</"):
			if not open_stack:
				raise ValueError(
					f"Document {doc_index}: unmatched closing tag {tag_text}."
				)
			expected_mention = open_stack.pop()
			if expected_mention != mention_id:
				raise ValueError(
					f"Document {doc_index}: mismatched closing tag {tag_text}, expected </{expected_mention}>."
				)
			result.append(f"</{entity_id}>")
		else:
			open_stack.append(mention_id)
			result.append(f"<{entity_id}>")

		last_end = match.end()

	result.append(document[last_end:])

	if open_stack:
		raise ValueError(
			f"Document {doc_index}: unclosed mention tags for {', '.join(open_stack)}."
		)

	unused_mentions = sorted(set(mention_to_entity) - seen_mentions)
	if unused_mentions:
		raise ValueError(
			f"Document {doc_index}: clustering JSON contains unused mentions: {', '.join(unused_mentions)}."
		)

	return "".join(result)


def convert_file(input_mml_path: Path, input_json_path: Path, output_eml_path: Path) -> None:
	mml_lines = input_mml_path.read_text(encoding="utf-8").splitlines()
	clusterings = json.loads(input_json_path.read_text(encoding="utf-8"))

	if not isinstance(clusterings, list):
		raise ValueError("Clustering JSON must be a list with one object per document.")
	if len(clusterings) != len(mml_lines):
		raise ValueError(
			f"Document count mismatch: MML has {len(mml_lines)} lines, JSON has {len(clusterings)} documents."
		)

	converted_documents: list[str] = []
	for doc_index, (line, clustering) in enumerate(zip(mml_lines, clusterings), start=1):
		if not isinstance(clustering, dict):
			raise ValueError(f"Document {doc_index}: clustering must be a JSON object.")
		mention_to_entity = build_mention_to_entity(clustering, doc_index)
		converted_documents.append(convert_document(line, mention_to_entity, doc_index))

	output_eml_path.write_text("\n".join(converted_documents) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Convert MML + clustering JSON back to EML."
	)
	parser.add_argument("input_mml", type=Path, help="Input MML file path")
	parser.add_argument("input_json", type=Path, help="Input clustering JSON file path")
	parser.add_argument("output_eml", type=Path, help="Output EML file path")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	convert_file(args.input_mml, args.input_json, args.output_eml)


if __name__ == "__main__":
	main()
