from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys


TAG_PATTERN = re.compile(r"</?e(\d+)>")
MENTION_ABBREVIATION = "m"


def entity_sort_key(entity_id: str) -> int:
	return int(entity_id[1:])


def sort_clustering_entities(clustering: dict[str, list[str]]) -> dict[str, list[str]]:
	return {entity_id: clustering[entity_id] for entity_id in sorted(clustering, key=entity_sort_key)}


def convert_document(document: str, doc_index: int, mention_prefix: str = MENTION_ABBREVIATION, store_mentions: bool = False) -> tuple[str, dict[str, list[str]], dict[str, list[str]]]:
	"""Convert one EML document into MML and produce mention clustering."""
	next_mention_id = 1
	open_stack: list[tuple[str, str]] = []
	clustering: dict[str, list[str]] = {}
	result: list[str] = []
	mention_tokens: dict[str, list[str]] = {}
	mention_start: dict[str, int] = {}

	last_end = 0
	for match in TAG_PATTERN.finditer(document):
		result.append(document[last_end:match.start()])

		tag_text = match.group(0)
		entity_num = match.group(1)
		entity_id = f"e{entity_num}"

		if tag_text.startswith("</"):
			match_index = -1
			for idx in range(len(open_stack) - 1, -1, -1):
				if open_stack[idx][0] == entity_id:
					match_index = idx
					break

			if match_index == -1:
				print(
					f"Warning: Document {doc_index}: unmatched closing tag {tag_text}; skipping.",
					file=sys.stderr,
				)
			else:
				_, mention_id = open_stack.pop(match_index)
				if match_index != len(open_stack):
					print(
						f"Warning: Document {doc_index}: non-proper nesting around {tag_text}; applying tolerant close.",
						file=sys.stderr,
					)
				result.append(f"</{mention_id}>")
			if store_mentions and mention_id in mention_start:
				text_inside = document[mention_start.pop(mention_id):match.start()]
				clean_text = TAG_PATTERN.sub("", text_inside)
				mention_tokens[mention_id] = [t for t in clean_text.split() if t]
		else:
			mention_id = f"{mention_prefix}{next_mention_id}"
			next_mention_id += 1

			open_stack.append((entity_id, mention_id))
			clustering.setdefault(entity_id, []).append(mention_id)
			result.append(f"<{mention_id}>")
			if store_mentions:
				mention_start[mention_id] = match.end()

		last_end = match.end()

	result.append(document[last_end:])

	if open_stack:
		unclosed_entities = sorted({entity for entity, _ in open_stack})
		print(
			f"Warning: Document {doc_index}: unclosed tags for entities {', '.join(unclosed_entities)}; auto-closing.",
			file=sys.stderr,
		)
		for _, mention_id in reversed(open_stack):
			result.append(f"</{mention_id}>")
			if store_mentions and mention_id in mention_start:
				text_inside = document[mention_start.pop(mention_id):]
				clean_text = TAG_PATTERN.sub("", text_inside)
				mention_tokens[mention_id] = [t for t in clean_text.split() if t]

	return "".join(result), clustering, mention_tokens


def format_clusterings_json(
	clusterings: list[dict[str, list[str]]],
	human_readable: bool,
	mention_tokens_list: list[dict[str, list[str]]] | None = None,
) -> str:
	sorted_clusterings = [sort_clustering_entities(clustering) for clustering in clusterings]

	if not human_readable:
		docs = []
		for i, clustering in enumerate(sorted_clusterings):
			doc: dict = dict(clustering)
			if mention_tokens_list is not None:
				doc["mentions"] = mention_tokens_list[i]
			docs.append(doc)
		return json.dumps(docs, ensure_ascii=False) + "\n"

	# Keep valid JSON with one entity mapping per line inside each document cluster object.
	lines = ["["]
	for index, clustering in enumerate(sorted_clusterings):
		suffix = "," if index < len(sorted_clusterings) - 1 else ""
		lines.append("\t{")
		items = list(clustering.items())
		all_items_count = len(items) + (1 if mention_tokens_list is not None else 0)
		for item_index, (entity_id, mentions) in enumerate(items):
			item_suffix = "," if item_index < all_items_count - 1 else ""
			mentions_json = json.dumps(mentions, ensure_ascii=False)
			lines.append(f'\t\t"{entity_id}": {mentions_json}{item_suffix}')
		if mention_tokens_list is not None:
			mention_tokens = mention_tokens_list[index]
			lines.append('\t\t"mentions": {')
			mention_items = list(mention_tokens.items())
			for m_idx, (mention_id, tokens) in enumerate(mention_items):
				m_suffix = "," if m_idx < len(mention_items) - 1 else ""
				lines.append(f'\t\t\t"{mention_id}": {json.dumps(tokens, ensure_ascii=False)}{m_suffix}')
			lines.append('\t\t}')
		lines.append(f"\t}}{suffix}")
	lines.append("]")
	return "\n".join(lines) + "\n"


def convert_file(
	input_path: Path,
	output_mml_path: Path,
	output_json_path: Path,
	human_readable_json: bool = False,
	mention_prefix: str = MENTION_ABBREVIATION,
	store_mentions: bool = False,
) -> None:
	lines = input_path.read_text(encoding="utf-8").splitlines()

	converted_documents: list[str] = []
	clusterings: list[dict[str, list[str]]] = []
	mention_tokens_list: list[dict[str, list[str]]] = []

	for doc_index, line in enumerate(lines, start=1):
		converted, clustering, mention_tokens = convert_document(line, doc_index, mention_prefix, store_mentions)
		converted_documents.append(converted)
		clusterings.append(clustering)
		mention_tokens_list.append(mention_tokens)

	output_mml_path.write_text("\n".join(converted_documents) + "\n", encoding="utf-8")
	output_json_path.write_text(
		format_clusterings_json(
			clusterings,
			human_readable_json,
			mention_tokens_list if store_mentions else None,
		),
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
	parser.add_argument(
		"--mention_prefix", type=str, default=MENTION_ABBREVIATION, help="Prefix for generated mention IDs (default: 'm')"
	)
	parser.add_argument(
		"--store_mentions",
		action="store_true",
		help="Include a 'mentions' object in the JSON output mapping each mention ID to its tokens.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	convert_file(
		args.input_eml,
		args.output_mml,
		args.output_json,
		human_readable_json=args.human_readable_json,
		mention_prefix=args.mention_prefix,
		store_mentions=args.store_mentions,
	)


if __name__ == "__main__":
	main()
