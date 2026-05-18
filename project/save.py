from chunks import Chunk

import os
import yaml
import logging
import json

def save_corpus_results(
	corpus_name: str,
	chunks: list[Chunk],
	output_directory: str,
	corpus_name_suffix: str = "-annotated.txt",
	format: str = "plaintext"
):
	output_path = os.path.join(output_directory, f"{corpus_name}{corpus_name_suffix}")

	with open(output_path, 'w', encoding='utf-8') as f:
		if format == "json":
			json_chunks = [chunk.json_dict for chunk in chunks]
			json.dump(json_chunks, f, ensure_ascii=False, indent=2)
		else:
			for chunk in chunks:
				if chunk is not None:
					f.write(f"{chunk.text.replace('\n', ' ')}\n")
				else:
					f.write("\n")
	logging.info(f"Results for corpus '{corpus_name}' saved to {output_path}.")

def save_all_results(chunks_by_corpus: dict[str, list[Chunk]], output_directory: str, corpus_name_suffix: str = "-annotated.txt", format: str = "txt"):
	for corpus_name, chunks in chunks_by_corpus.items():
		save_corpus_results(corpus_name, chunks, output_directory, corpus_name_suffix, format)

def save_failure_report(failed_chunks_by_corpus: dict[str, list[int]], output_directory: str, report_name: str = "failed_chunks.yaml"):
	report_path = os.path.join(output_directory, report_name)
	with open(report_path, 'w', encoding='utf-8') as f:
		yaml.dump(failed_chunks_by_corpus, f)
	logging.info(f"Failure report saved to {report_path}.")
