import os
import re
import logging

from config import Config, LANGUAGES
import load
import examples
import chunks
import prompts
import llm_service
import save
import models

DOC_WITH_MULTIPLE_ENTITIES_MINIMAL_LENGTH = 300
EML_MML_LENGTH_RATIO_THRESHOLD = 0.7

def get_language_code_from_corpus_name(corpus_name):
	"""Extract language code from corpus name assuming format langcode-*.txt"""
	match = re.match(r'([a-z]{2,4})\_.*', corpus_name)
	if match:
		return match.group(1)
	else:
		raise ValueError(f"Corpus name {corpus_name} does not match expected format.")

def load_train_corpora(config: Config) -> dict[str, list[examples.Example]]:
	suffix_gold = choose_extension(config.experiment.annotation_format)
	gold_texts = load.load_corpora_from_directory(config.examples.directory_gold, suffix=suffix_gold)
	suffix_blind = choose_extension(config.data.input_format)
	blind_texts = load.load_corpora_from_directory(config.examples.directory_blind, suffix=suffix_blind)
	logging.info(f"Loaded gold corpora: {list(gold_texts.keys())} from directory: {config.examples.directory_gold}")
	logging.info(f"Loaded blind corpora: {list(blind_texts.keys())} from directory: {config.examples.directory_blind}")
	examples_by_corpus = {}
	for corpus_name in gold_texts:
		if corpus_name not in blind_texts:
			raise ValueError(f"Corpus '{corpus_name}' is present in gold input directory but not in blind input directory.")
		examples_by_corpus[corpus_name] = examples.construct(
			blind_texts[corpus_name],
			gold_texts[corpus_name],
			number=config.examples.number,
			choose_strategy=config.examples.choose_strategy,
			# context_strategy=config.examples.context_strategy, # TODO: Add context strategy to config
			# left_context_size=config.examples.left_context_size, # TODO: Add left context size to config
			# right_context_size=config.examples.right_context_size # TODO: Add right context size to config
		)
		example = examples_by_corpus[corpus_name][0]
		logging.info(f"Prepared example for corpus '{corpus_name}' ({len(example.blind)} chars, {len(example.gold.split())} words): {example.blind[:80]}... -> {example.gold[:80]}...")
	corpora_with_empty_tokens = find_corpora_with_empty_tokens(config, gold_texts, minimum=5)
	corpora_with_empty_tokens.discard("en_gum")
	logging.info(f"Corpora with empty tokens: {corpora_with_empty_tokens}")
	print(f"Corpora with empty tokens: {corpora_with_empty_tokens}")
	return examples_by_corpus, corpora_with_empty_tokens

def load_and_prepare_data(config: Config) -> dict[str, list[chunks.Chunk]]:
	corpora = load.load_corpora_from_directory(config.data.directory, suffix=choose_extension(config.data.input_format))
	data_by_corpus = {}
	for corpus_name, texts in corpora.items():
		data_by_corpus[corpus_name] = chunks.construct(
			texts,
			metadata={"corpus": corpus_name},
			# doc_ids=doc_ids,
			# context_strategy=config.data.context_strategy, # TODO: Add context strategy to config
			# left_context_size=config.data.left_context_size, # TODO: Add left context size to config
			# right_context_size=config.data.right_context_size # TODO: Add right context size to config
		)
	return data_by_corpus

def find_variables_in_template(template: str) -> list[str]:
	"""Find all variables in the template string."""
	return re.findall(r"\{(\$?\w+)\}", template)

def load_prompt_templates(config: Config) -> dict[str, prompts.Template]:
	if isinstance(config.prompt.template, str):
		with open(config.prompt.template, 'r', encoding='utf-8') as f:
			template_str = f.read()
		variables = find_variables_in_template(template_str)
		logging.info(f"Loaded prompt template from {config.prompt.template} with variables: {variables}")
		#print(template_str)
		return {"default": prompts.Template(template_str, variables)}
	elif isinstance(config.prompt.template, dict):
		templates = {}
		for corpus_name, template_path in config.prompt.template.items():
			with open(template_path, 'r', encoding='utf-8') as f:
				template_str = f.read()
			variables = find_variables_in_template(template_str)
			logging.info(f"Loaded prompt template for corpus '{corpus_name}' from {template_path} with variables: {variables}")
			templates[corpus_name] = prompts.Template(template_str, variables)
		return templates

def initialize_llm_service(config: Config) -> llm_service.LLMService:
	logging.info(f"Initializing {config.api.provider} API for model: {config.llm.model}")
	response_log_file = os.path.join(config.experiment.directory, "failed_llm_responses.log")
	return llm_service.LLMService(
		api_key=config.get_api_key(), 
		concurrency=config.run.concurrency,
		base_url=config.api.base_url,
		#delay=config.api.delay,
		response_log_file=response_log_file
	)

def load_instructions(config: Config) -> dict[str, str]:
	instruction_directory = config.prompt.instructions_directory
	if instruction_directory is not None:
		instructions = load.load_instructions_from_directory(instruction_directory)
		logging.info(f"Loaded instructions for corpora: {list(instructions.keys())} from directory: {instruction_directory}")
		return instructions
	else:
		logging.info("No instructions directory specified in config. Continuing without loading instructions.")
		return {}

def contains_empty_tokens(config: Config, chunks: list[str], minimum: int = 1) -> bool:
	if chunks is None:
		return False
	count = 0
	empty_token_pattern = r"##\w*\|" if config.experiment.annotation_format in {"plaintext", "txt"} else r"##"
	for chunk in chunks:
		if isinstance(chunk, dict):
			chunk = " ".join(chunk["tokens"])
		if re.search(empty_token_pattern, chunk):
			count += 1
			if count >= minimum:
				return True
	return False

def find_corpora_with_empty_tokens(config: Config, data_by_corpus: dict[str, list[str]], minimum: int = 1) -> set[str]:
	if data_by_corpus is None:
		return set()
	return {corpus_name for corpus_name, chunks in data_by_corpus.items() if contains_empty_tokens(config, chunks, minimum)}

def prepare_variables_for_corpus(corpus_name: str, config: Config, corpora_with_empty_tokens: set[str] = None) -> dict[str, str]:
	if config.data.language == "auto":
		language_code = get_language_code_from_corpus_name(corpus_name)
	else:
		language_code = config.data.language
	variables = {
		"$LANGUAGE": LANGUAGES.get(language_code, language_code),
		"$EMPTY_TOKENS_INSTRUCTIONS": load_instructions(config).get("improved_empty_tokens.txt", "") if corpora_with_empty_tokens is not None and corpus_name in corpora_with_empty_tokens else ""
	}
	return variables

def prepare_variables_for_corpora(corpus_names: list[str], config: Config, corpora_with_empty_tokens: set[str] = None) -> dict[str, dict[str, str]]:
	variables_by_corpus = {}
	for corpus_name in corpus_names:
		variables_by_corpus[corpus_name] = prepare_variables_for_corpus(corpus_name, config, corpora_with_empty_tokens)
	return variables_by_corpus

def construct_model(
		config: Config,
		llm_service: llm_service.LLMService,
		prompt_templates_by_corpus: dict[str, prompts.Template],
		examples_by_corpus: dict[str, list[examples.Example]] = None,
		corpora_with_empty_tokens: set[str] = None
	) -> models.Model:
	model_parameters = config.llm.parameters.to_dict() if hasattr(config.llm, "parameters") else {}
	if examples_by_corpus is not None:
		template_variable_values_by_corpus = prepare_variables_for_corpora(examples_by_corpus.keys(), config, corpora_with_empty_tokens)
		return models.MultiCorpusExampleModel(
			llm_service,
			config.llm.model,
			prompt_templates_by_corpus,
			examples_by_corpus,
			template_variable_values_by_corpus,
			model_parameters=model_parameters,
			input_format=config.data.input_format,
			what_in_input=config.prompt.what_in_input if hasattr(config.prompt, "what_in_input") else {"blind_tokens"},
			output_format=config.experiment.annotation_format,
			what_in_output=config.prompt.what_in_output if hasattr(config.prompt, "what_in_output") else {"clusters_token_offsets", "clusters_text_mentions", "tokens"}
		)
	else:
		return models.Model(llm_service, config.llm.model, prompt_template, output_format=config.experiment.annotation_format, model_parameters=model_parameters)

def run_model(config: Config, model: models.Model, chunks_by_corpus: dict[str, list[chunks.Chunk]]) -> dict[str, list[chunks.Chunk]]:
	logging.info(f"Running model: {config.llm.model}")
	return model.generate_by_corpus(chunks_by_corpus, show_progress=config.run.show_progress, show_separate_progresses=config.run.show_separate_progress_bars)

def find_all_failed_chunks(results_by_corpus: dict[str, list[chunks.Chunk]]) -> dict[str, list[int]]:
	failed_chunks_by_corpus = {}
	for corpus_name, chunks in results_by_corpus.items():
		failed_indices = [chunk.metadata.get("index") for chunk in chunks if not chunk.metadata.get("success", False)]
		if failed_indices:
			failed_chunks_by_corpus[corpus_name] = failed_indices
	return failed_chunks_by_corpus

def find_failed_chunks_by_indices(results_by_corpus: dict[str, list[chunks.Chunk]], indices_by_corpus: dict[str, list[int]]) -> dict[str, list[int]]:
	failed_chunks_by_corpus = {}
	for corpus_name, indices in indices_by_corpus.items():
		if corpus_name not in results_by_corpus:
			logging.warning(f"Corpus '{corpus_name}' is present in indices but not in results. Skipping.")
			continue
		chunks = results_by_corpus[corpus_name]
		failed_indices = [indices[i] for i in range(len(chunks)) if not chunks[i].metadata.get("success", False)]
		if failed_indices:
			failed_chunks_by_corpus[corpus_name] = failed_indices
	return failed_chunks_by_corpus

def find_failed_chunks(results_by_corpus: dict[str, list[chunks.Chunk]], indices_by_corpus: dict[str, list[int]] = None) -> dict[str, list[int]]:
	if indices_by_corpus is not None:
		return find_failed_chunks_by_indices(results_by_corpus, indices_by_corpus)
	else:
		return find_all_failed_chunks(results_by_corpus)

def merge_input_with_successful_output_chunks_all(output_chunks: dict[str, list[chunks.Chunk]], input_chunks: dict[str, list[chunks.Chunk]]) -> dict[str, list[chunks.Chunk]]:
	merged_chunks = {}
	for corpus_name, corpus_output_chunks in output_chunks.items():
		corpus_input_chunks = input_chunks[corpus_name]
		merged_chunks[corpus_name] = []
		for input_chunk, output_chunk in zip(corpus_input_chunks, corpus_output_chunks):
			if output_chunk.metadata.get("success", False):
				merged_chunks[corpus_name].append(output_chunk)
			else:
				merged_chunks[corpus_name].append(input_chunk)
	return merged_chunks

def merge_input_with_successful_output_chunks_indices(output_chunks: dict[str, list[chunks.Chunk]], input_chunks: dict[str, list[chunks.Chunk]], indices_by_corpus: dict[str, list[int]]) -> dict[str, list[chunks.Chunk]]:
	merged_chunks = {}
	for corpus_name, corpus_input_chunks in input_chunks.items():
		merged_chunks[corpus_name] = [input_chunk for input_chunk in corpus_input_chunks]
		if corpus_name in indices_by_corpus:
			for i, output_chunk in zip(indices_by_corpus[corpus_name], output_chunks[corpus_name]):
				if i < len(corpus_input_chunks):
					merged_chunks[corpus_name][i] = output_chunk
					logging.info(f"Chunk {i} for corpus '{corpus_name}' replaced with an annotated result.")
				else:
					logging.warning(f"Index {i} for corpus '{corpus_name}' is out of range. Skipping.")
	return merged_chunks

def merge_successful_with_input_chunks(output_chunks: dict[str, list[chunks.Chunk]], input_chunks: dict[str, list[chunks.Chunk]], indices_by_corpus: dict[str, list[int]] = None) -> dict[str, list[chunks.Chunk]]:
	if indices_by_corpus is not None:
		return merge_input_with_successful_output_chunks_indices(output_chunks, input_chunks, indices_by_corpus)
	else:
		return merge_input_with_successful_output_chunks_all(output_chunks, input_chunks)

def choose_extension(annotation_format: str) -> str:
	if annotation_format == "json":
		return ".json"
	elif annotation_format == "plaintext":
		return ".txt"
	elif annotation_format == "eml":
		return ".eml"
	elif annotation_format == "mml":
		return ".mml"
	elif annotation_format == "mmle":
		return ".mmle"
	else:
		logging.warning(f"Unknown annotation format '{annotation_format}'. Defaulting to 'txt'.")
		return ".txt"

def export(config: Config, chunks_by_corpus: dict[str, list[chunks.Chunk]], failed_chunk_indices_by_corpus: dict[str, list[int]], attempt: int = None):
	# Check if the directory exists, if not, create it
	with open(os.path.join(config.experiment.directory, "config.yaml"), 'w', encoding='utf-8') as f:
		f.write(config.dump())
	failure_report_name = f"failed_chunks_attempt_{attempt + 1}.yaml" if attempt is not None else "failed_chunks.yaml"
	dir_name = f"attempt_{attempt + 1}" if attempt is not None else "results"
	results_directory = os.path.join(config.experiment.directory, dir_name)

	save.save_failure_report(failed_chunk_indices_by_corpus, config.experiment.directory, report_name=failure_report_name)

	if not os.path.exists(results_directory):
		os.makedirs(results_directory)
	corpus_name_suffix = "-annotated" + choose_extension(config.experiment.annotation_format)
	save.save_all_results(chunks_by_corpus, results_directory, corpus_name_suffix, format=config.experiment.annotation_format)

def load_indices_to_process(config: Config) -> dict[str, list[int]]:
	if config.data.only_indices_file is not None:
		return load.load_indices_by_corpus(config.data.only_indices_file)
	else:
		return None

def filter_chunks_by_indices(chunks_by_corpus: dict[str, list[chunks.Chunk]], indices_by_corpus: dict[str, list[int]] = None) -> dict[str, list[chunks.Chunk]]:
	if indices_by_corpus is None:
		return chunks_by_corpus
	filtered_chunks_by_corpus = {}
	for corpus_name, chunks in chunks_by_corpus.items():
		if corpus_name in indices_by_corpus:
			indices_to_process = indices_by_corpus[corpus_name]
			filtered_chunks_by_corpus[corpus_name] = [chunks[i] for i in indices_to_process]
		# else:
		# 	filtered_chunks_by_corpus[corpus_name] = []
	return filtered_chunks_by_corpus

def check_chunk(config: Config, output_chunk: chunks.Chunk, input_chunk: chunks.Chunk, chunk_index: int, corpus_name: str) -> bool:
	if output_chunk.tokens is None:
		logging.warning(f"Chunk {chunk_index} for corpus '{corpus_name}' has no text in the output. Marking as failed and keeping original text.")
		return False

	elif output_chunk.text.strip() == "":
		logging.warning(f"Chunk {chunk_index} for corpus '{corpus_name}' has empty text in the output. Marking as failed and keeping original text.")
		return False

	elif config.experiment.annotation_format in {"plaintext", "eml", "mml"} \
		and config.data.input_format != "mml" \
		and len(output_chunk.text) < len(input_chunk.text):
		logging.warning(f"Chunk {chunk_index} for corpus '{corpus_name}' has shorter text in the output than in the input. Marking as failed and keeping original text.")
		return False
	
	elif config.experiment.annotation_format == "eml" \
		and config.data.input_format == "mml" \
		and (len(output_chunk.text) > len(input_chunk.text) \
	    or len(output_chunk.text) < len(input_chunk.text) * EML_MML_LENGTH_RATIO_THRESHOLD \
		or output_chunk.text[-1] != input_chunk.text[-1]
		): # Allow some decrease in length due to tags, but not too much
		logging.warning(f"Chunk {chunk_index} for corpus '{corpus_name}' has longer text in the output than in the input. Marking as failed and keeping original text.")
		return False

	elif config.experiment.annotation_format == "plaintext" \
		and "|" not in output_chunk.text:
		logging.warning(f"Chunk {chunk_index} for corpus '{corpus_name}' does not contain '|' in the output. Marking as failed and keeping original text.")
		return False

	elif config.experiment.annotation_format in {"plaintext", "eml", "mml"} \
		and re.search(r"\< \# Example \d ", output_chunk.text):
		logging.warning(f"Chunk {chunk_index} for corpus '{corpus_name}' contains an unprocessed example in the output. Marking as failed and keeping original text.")
		return False

	elif config.experiment.annotation_format == "mmle" \
		and len(input_chunk.text) > DOC_WITH_MULTIPLE_ENTITIES_MINIMAL_LENGTH \
		and not re.search(r"\n", output_chunk.text):
		logging.warning(f"Chunk {chunk_index} for corpus '{corpus_name}' is long but the output contains only one cluster. Marking as failed and keeping original text.")
		return False

	else:
		return True

def check_all_chunks(config: Config, chunks_by_corpus: dict[str, list[chunks.Chunk]], input_chunks_by_corpus: dict[str, list[chunks.Chunk]]):
	for corpus_name in chunks_by_corpus:
		output_chunks = chunks_by_corpus[corpus_name]
		input_chunks = input_chunks_by_corpus[corpus_name]
		if len(output_chunks) != len(input_chunks):
			raise ValueError(f"Number of output chunks for corpus '{corpus_name}' does not match number of input chunks. Output: {len(output_chunks)}, Input: {len(input_chunks)}")
		for i, (output_chunk, input_chunk) in enumerate(zip(output_chunks, input_chunks)):
			if not check_chunk(config, output_chunk, input_chunk, i, corpus_name):
				if config.experiment.annotation_format != "json":
					output_chunk.metadata["success"] = False
				output_chunk.tokens = input_chunk.tokens
	return chunks_by_corpus

def check_chunks_with_indices(config: Config, chunks_by_corpus: dict[str, list[chunks.Chunk]], input_chunks_by_corpus: dict[str, list[chunks.Chunk]], indices_by_corpus: dict[str, list[int]]):
	for corpus_name in indices_by_corpus:
		if corpus_name not in chunks_by_corpus:
			raise ValueError(f"Corpus '{corpus_name}' is present in indices but not in output chunks.")
		if corpus_name not in input_chunks_by_corpus:
			raise ValueError(f"Corpus '{corpus_name}' is present in indices but not in input chunks.")
		output_chunks = chunks_by_corpus[corpus_name]
		input_chunks = input_chunks_by_corpus[corpus_name]
		indices = indices_by_corpus[corpus_name]
		for i, output_chunk in zip(indices, output_chunks):
			if i >= len(input_chunks):
				logging.warning(f"Index {i} for corpus '{corpus_name}' is out of range for input chunks. Skipping.")
				continue
			input_chunk = input_chunks[i]
			if not check_chunk(config, output_chunk, input_chunk, i, corpus_name):
				if config.experiment.annotation_format != "json":
					output_chunk.metadata["success"] = False
				output_chunk.tokens = input_chunk.tokens
	return chunks_by_corpus

def check_chunks(config: Config, chunks_by_corpus: dict[str, list[chunks.Chunk]], input_chunks_by_corpus: dict[str, list[chunks.Chunk]], indices_by_corpus: dict[str, list[int]] = None):
	if indices_by_corpus is not None:
		return check_chunks_with_indices(config, chunks_by_corpus, input_chunks_by_corpus, indices_by_corpus)
	else:
		return check_all_chunks(config, chunks_by_corpus, input_chunks_by_corpus)

def run_attempt(
	config: Config,
	input_data: dict[str, list[chunks.Chunk]],
	model: models.Model,
	llm: llm_service.LLMService,
	indices: dict[str, list[int]] = None
	) -> tuple[dict[str, list[chunks.Chunk]], dict[str, list[int]]]:
	filtered_data = filter_chunks_by_indices(input_data, indices)
	llm.reset_semaphore()
	results = run_model(config, model, filtered_data)
	checked_results = check_chunks(config, results, input_data, indices)
	failed_chunks = find_failed_chunks(checked_results, indices)
	return checked_results, failed_chunks

def count_indices(indices_by_corpus: dict[str, list[int]]) -> int:
	if indices_by_corpus is None:
		return 0
	return sum(len(indices) for indices in indices_by_corpus.values())

# def update_data_with_results(input_data: dict[str, list[chunks.Chunk]], results: dict[str, list[chunks.Chunk]], indices_by_corpus: dict[str, list[int]] = None) -> dict[str, list[chunks.Chunk]]:
# 	updated_data = {}
# 	for corpus_name, input_chunks in input_data.items():
# 		if corpus_name in results:
# 			result_chunks = results[corpus_name]
# 			if indices_by_corpus is not None and corpus_name in indices_by_corpus:
# 				indices = indices_by_corpus[corpus_name]
# 				updated_chunks = []
# 				for i, input_chunk in enumerate(input_chunks):
# 					if i in indices:
# 						result_index = indices.index(i)
# 						if result_index < len(result_chunks):
# 							updated_chunks.append(result_chunks[result_index])
# 						else:
# 							logging.warning(f"Result index {result_index} for corpus '{corpus_name}' is out of range for result chunks. Keeping original chunk.")
# 							updated_chunks.append(input_chunk)
# 					else:
# 						updated_chunks.append(input_chunk)
# 				updated_data[corpus_name] = updated_chunks
# 			else:
# 				updated_data[corpus_name] = result_chunks
# 		else:
# 			logging.info(f"Corpus '{corpus_name}' is present in input data but not in results. Keeping original chunks.")
# 			updated_data[corpus_name] = input_chunks
# 	return updated_data

def update_chunk_texts(chunks_by_corpus: dict[str, list[chunks.Chunk]], new_texts_by_corpus: dict[str, list[chunks.Chunk]]):
	for corpus_name, chunks in chunks_by_corpus.items():
		if corpus_name in new_texts_by_corpus:
			new_texts = new_texts_by_corpus[corpus_name]
			if len(chunks) != len(new_texts):
				logging.warning(f"Number of chunks for corpus '{corpus_name}' does not match number of new texts. Skipping update for this corpus.")
				continue
			for chunk, new_text in zip(chunks, new_texts):
				chunk.text = new_text

def run_attempts(
	config: Config,
	input_data: dict[str, list[chunks.Chunk]],
	model: models.Model,
	llm: llm_service.LLMService,
	indices: dict[str, list[int]] = None
	) -> tuple[dict[str, list[chunks.Chunk]], dict[str, list[int]], dict[str, list[int]]]:

	for attempt in range(config.run.attempts):
		logging.info(f"Starting attempt {attempt + 1}/{config.run.attempts}...")
		print(f"Starting attempt {attempt + 1}/{config.run.attempts}...")
		output_chunks, failed_chunk_indices = run_attempt(config, input_data, model, llm, indices)
		result_chunks = merge_successful_with_input_chunks(output_chunks, input_data, indices)

		if config.run.save_intermediate:
			export(config, result_chunks, failed_chunk_indices, attempt=attempt)
			print(f"Intermediate results for attempt {attempt + 1} saved.")

		if not failed_chunk_indices:
			logging.info(f"All chunks processed successfully on attempt {attempt + 1}.")
			return result_chunks, failed_chunk_indices

		elif indices is not None and count_indices(failed_chunk_indices) == count_indices(indices):
			logging.warning(f"No more chunks were processed successfully on attempt {attempt + 1}. Stopping attempts.")
			return result_chunks, failed_chunk_indices

		logging.warning(f"Attempt {attempt + 1} completed with {count_indices(failed_chunk_indices)} failed chunks across {len(failed_chunk_indices)} corpora. Retrying to process failed chunks...")
		print(f"Attempt {attempt + 1} completed with {count_indices(failed_chunk_indices)} failed chunks across {len(failed_chunk_indices)} corpora. Retrying to process failed chunks...")

		indices = failed_chunk_indices
		input_data = result_chunks
		#update_chunk_texts(input_data, result_chunks)

	logging.warning(f"Maximum number of attempts ({config.run.attempts}) reached. Stopping attempts with {count_indices(failed_chunk_indices)} failed chunks across {len(failed_chunk_indices)} corpora.")
	print(f"Maximum number of attempts ({config.run.attempts}) reached. Stopping attempts with {count_indices(failed_chunk_indices)} failed chunks across {len(failed_chunk_indices)} corpora.")
	return result_chunks, failed_chunk_indices

def run(config: Config):
	# TODO: Implement the run logic
	templates = load_prompt_templates(config)
	examples, corpora_with_empty_tokens = load_train_corpora(config)
	data = load_and_prepare_data(config)
	indices = load_indices_to_process(config)

	llm = initialize_llm_service(config)
	model = construct_model(config, llm, templates, examples, corpora_with_empty_tokens)

	result_chunks, failed_chunk_indices = run_attempts(config, data, model, llm, indices)


	# results = run_model(config, model, filtered_data)
	# checked_results = check_chunks(results, data, indices)
	# failed_chunks = find_failed_chunks(checked_results, indices)
	
	export(config, result_chunks, failed_chunk_indices)
