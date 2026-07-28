"""Load text chunks from the input files."""

import os
import yaml
import json

def load_indices_by_corpus(file_path: str) -> dict:
	with open(file_path, 'r', encoding='utf-8') as f:
		return yaml.safe_load(f)

def load_json_corpus(file_path: str) -> list[str]:
	"""Load text chunks from a JSON file."""
	with open(file_path, 'r', encoding='utf-8') as f:
		data = json.load(f)

	doc_ids = []
	for i, item in enumerate(data):
		if "doc_id" in item:
			doc_ids.append(item["doc_id"])
			# del item["doc_id"]
		else:
			doc_ids.append(str(i))
	return data

def load_corpus(file_path: str) -> list[str]:
	"""Load text chunks from the input file."""
	with open(file_path, 'r', encoding='utf-8') as f:
		return [line.strip() for line in f]

def extract_corpus_name(file_path: str) -> str:
	"""Extract the corpus name from the file path."""
	return os.path.basename(file_path).split('-')[0]

def load_corpora(file_paths: list[str], format: str = 'plaintext') -> dict[str, list[str]]:
	"""Load text chunks from multiple input files and organize them by corpus name."""
	corpora = {}
	for file_path in file_paths:
		corpus_name = extract_corpus_name(file_path)
		if format == 'json':
			corpora[corpus_name] = load_json_corpus(file_path)
		else:
			corpora[corpus_name] = load_corpus(file_path)
	return corpora

def find_all_corpora(directory: str, suffix: str = '.txt', include_subdirectories: bool = False) -> list[str]:
	"""Find all text files in the given directory and return their paths."""
	corpora_files = []
	for root, _, files in os.walk(directory):
		if not include_subdirectories and root != directory:
			continue
		for file in files:
			if file.endswith(suffix):
				corpora_files.append(os.path.join(root, file))
	return corpora_files

def load_corpora_from_directory(directory: str, suffix: str = '.txt', include_subdirectories: bool = False) -> dict[str, list[str]]:
	"""Load text chunks from all text files in the given directory and organize them by corpus name."""
	corpora_files = find_all_corpora(directory, suffix, include_subdirectories)
	return load_corpora(corpora_files, format=suffix.split('.')[-1])

def load_instruction(file_path: str) -> str:
	"""Load instruction text from the given file."""
	with open(file_path, 'r', encoding='utf-8') as f:
		return f.read()

def load_instructions_from_directory(directory: str, suffix: str = '.txt') -> dict[str, str]:
	"""Load instruction texts from all text files in the given directory and organize them by corpus name."""
	instructions = {}
	for root, _, files in os.walk(directory):
		for file in files:
			if file.endswith(suffix):
				instructions[file] = load_instruction(os.path.join(root, file))
	return instructions

def _test():
	corpora = load_corpora_from_directory('data/annotated/dev')
	for corpus_name, texts in corpora.items():
		print(f"Corpus: {corpus_name},\tNumber of texts: {len(texts)},\tFirst text: {texts[0][:80]}...")
	print(f"Number of corpora loaded: {len(corpora)}")

if __name__ == "__main__":
	_test()
