import asyncio
from tqdm import tqdm
import logging

from llm_service import LLMService
from prompts import Template, Prompt, ExamplePrompt
from chunks import Chunk
from examples import Example
from response_processing import extract_final_output

class Model:
	def __init__(self, llm_service: LLMService, model_name: str, prompt_template: Template, output_format: str = "plaintext", model_parameters: dict = {}):
		self.llm_service = llm_service
		self.model_name = model_name
		self.prompt_template = prompt_template
		self.model_parameters = model_parameters
		self.output_format = output_format

	def construct_prompt(self, input_chunk: Chunk, prompt_values: dict = {}) -> Prompt:
		return Prompt(self.prompt_template, input_chunk, prompt_values)

	async def generate_async(self, input_chunk: Chunk, prompt_values: dict = {}) -> Chunk:
		prompt = self.construct_prompt(input_chunk, prompt_values)
		rendered_prompt = prompt.render()
		logging.info(f"Sending request to LLM for input chunk with metadata {input_chunk.metadata}.")
		logging.debug(f"Constructed PROMPT for input chunk with metadata {input_chunk.metadata}:\n{rendered_prompt}")
		success, response = await self.llm_service.generate(rendered_prompt, model=self.model_name, **self.model_parameters)
		logging.info(f"Generated response for input chunk with metadata {input_chunk.metadata} (Success: {success}).")
		logging.debug(f"Received RESPONSE for input chunk with metadata {input_chunk.metadata} (Success: {success}):\n{response}")
		if self.output_format == "mmle" and isinstance(response, str):
			response = extract_final_output(response)
		return Chunk(
			response,
			metadata={"input_chunk": input_chunk, "success": success, "corpus": input_chunk.metadata.get("corpus"), "index": input_chunk.metadata.get("index"), "model": self.model_name},
			parse_json=(self.output_format == "json")
		)

	def generate(self, input_chunk: Chunk, prompt_values: dict = {}) -> Chunk:
		return asyncio.run(self.generate_async(input_chunk, prompt_values=prompt_values))

	async def _generate_indexed_chunk(self, index: int, input_chunk: Chunk, prompt_values: dict = {}) -> Chunk:
		return index, await self.generate_async(input_chunk, prompt_values=prompt_values)

	async def _generate_corpus(self, corpus_name: str, input_chunks: list[Chunk], prompt_values: dict = {}, progresses: list[tqdm] = [], show_progress: bool = False) -> list[Chunk]:
		logging.info(f"Starting generation for corpus '{corpus_name}' with {len(input_chunks)} chunks.")
		with tqdm(
			total=len(input_chunks),
			desc=f"Generating for '{corpus_name}'",
			unit="chunk",
			disable=not show_progress
		) as progress:
			return corpus_name, await self.generate_all_async(input_chunks, prompt_values=prompt_values, progresses=progresses + [progress])

	def generate_all(self, input_chunks: list[Chunk], prompt_values: dict = {}, show_progress: bool = False) -> list[Chunk]:
		with tqdm(total=len(input_chunks), desc="Generating", unit="chunk", disable=not show_progress) as progress:
			return asyncio.run(self.generate_all_async(input_chunks, prompt_values=prompt_values, progresses=[progress]))

	async def generate_all_async(self, input_chunks: list[Chunk], prompt_values: dict = {}, progresses: list[tqdm] = []) -> list[Chunk]:
		tasks = [asyncio.create_task(self._generate_indexed_chunk(i, chunk, prompt_values=prompt_values)) for i, chunk in enumerate(input_chunks)]
		responses = [None] * len(tasks)
		for completed in asyncio.as_completed(tasks):
			index, response = await completed
			responses[index] = response
			for progress in progresses:
				progress.update(1)
		return responses

	def generate_by_corpus(self, input_chunks_by_corpus: dict[str, list[Chunk]], prompt_values: dict = {}, show_progress: bool = False, show_separate_progresses: bool = False) -> dict[str, list[Chunk]]:
		with tqdm(
			total=sum(len(chunks) for chunks in input_chunks_by_corpus.values()),
			desc="Generating chunks",
			unit="chunk",
			disable=not show_progress
		) as progress:
			return asyncio.run(self.generate_by_corpus_async(
				input_chunks_by_corpus,
				prompt_values=prompt_values,
				progresses=[progress],
				show_separate_progresses=show_separate_progresses
			))

	async def generate_by_corpus_async(self, input_chunks_by_corpus: dict[str, list[Chunk]], prompt_values: dict = {}, progresses: list[tqdm] = [], show_separate_progresses: bool = False) -> dict[str, list[Chunk]]:
		results = {}
		tasks = [asyncio.create_task(self._generate_corpus(
				corpus,
				chunks,
				prompt_values=prompt_values,
				progresses=progresses,
				show_progress=show_separate_progresses
			)) for corpus, chunks in input_chunks_by_corpus.items()
		]
		for completed in asyncio.as_completed(tasks):
			corpus, responses = await completed
			logging.info(f"Completed generation for corpus '{corpus}'.")
			results[corpus] = responses
		return results

class Pipeline(Model):
	def __init__(self, models: list[Model]):
		self.models = models
	async def generate_async(self, input_chunk: Chunk, prompt_values: dict = {}) -> Chunk:
		current_chunk = input_chunk
		for model in self.models:
			current_chunk = await model.generate_async(current_chunk, prompt_values=prompt_values)
		return current_chunk

class ExampleModel(Model):
	def __init__(self,
			llm_service: LLMService,
			model_name: str,
			prompt_template: Template,
			examples: list[Example],
			input_format: str = "plaintext",
			what_in_input: list[str] = ["blind_tokens"],
			output_format: str = "plaintext",
			what_in_output: list[str] = ["clusters_token_offsets", "clusters_text_mentions"],
			model_parameters: dict = {}
		):
		super().__init__(
			llm_service,
			model_name,
			prompt_template,
			output_format=output_format,
			model_parameters=model_parameters
		)
		self.examples = examples
		self.input_format = input_format
		self.what_in_input = what_in_input
		self.what_in_output = what_in_output

	def construct_prompt(self, input_chunk: Chunk, prompt_values: dict = {}) -> Prompt:
		return ExamplePrompt(
			self.prompt_template,
			input_chunk,
			self.examples,
			prompt_values,
			input_format=self.input_format,
			what_in_input=self.what_in_input,
			output_format=self.output_format,
			what_in_output=self.what_in_output
		)

class MultiCorpusExampleModel(Model):
	def __init__(self,
			llm_service: LLMService,
			model_name: str,
			prompt_templates_by_corpus: dict[str, Template],
			examples_by_corpus: dict[str, list[Example]],
			template_variable_values_by_corpus: dict[str, dict[str, str]] = None,
			input_format: str = "plaintext",
			what_in_input: list[str] = ["blind_tokens"],
			output_format: str = "plaintext",
			what_in_output: list[str] = ["clusters_token_offsets", "clusters_text_mentions"],
			model_parameters: dict = {}
		):
		super().__init__(
			llm_service,
			model_name,
			prompt_templates_by_corpus["default"],
			output_format=output_format,
			model_parameters=model_parameters
		)
		self.input_format = input_format
		self.what_in_input = what_in_input
		self.what_in_output = what_in_output
		self.examples_by_corpus = examples_by_corpus
		self.prompt_templates_by_corpus = prompt_templates_by_corpus
		self.template_variable_values_by_corpus = template_variable_values_by_corpus or {}

	def construct_prompt(self, input_chunk: Chunk, prompt_values: dict = {}) -> Prompt:
		corpus_name = input_chunk.metadata.get("corpus")
		if corpus_name is None:
			raise ValueError("Input chunk is missing 'corpus' metadata required for selecting examples.")
		examples = self.examples_by_corpus.get(corpus_name)
		if examples is None:
			raise ValueError(f"No examples found for corpus '{corpus_name}'.")
		variable_values = self.template_variable_values_by_corpus.get(corpus_name, {})
		variable_values.update(prompt_values)
		return ExamplePrompt(
			self.prompt_templates_by_corpus.get(corpus_name, self.prompt_templates_by_corpus["default"]),
			input_chunk,
			examples,
			variable_values,
			input_format=self.input_format,
			what_in_input=self.what_in_input,
			output_format=self.output_format,
			what_in_output=self.what_in_output
		)

def _test_single():
	import os
	api_key = os.getenv("OPENROUTER_API_KEY")
	llm_service = LLMService(api_key)
	template = Template("What is the capital of {$DATA}?")
	model = Model(llm_service, "arcee-ai/trinity-large-preview:free", template)
	input_chunk = Chunk("France")
	output_chunk = asyncio.run(model.generate_async(input_chunk))
	print(output_chunk.text)

def _test_parallel():
	import os
	api_key = os.getenv("OPENROUTER_API_KEY")
	llm_service = LLMService(api_key)
	template = Template("What is the capital of {$DATA}?")
	model = Model(llm_service, "arcee-ai/trinity-large-preview:free", template)
	input_chunks_by_corpus = {
		"corpus1": [Chunk("France"), Chunk("Germany"), Chunk("Italy"), Chunk("Austria"), Chunk("Poland"),
					Chunk("Switzerland"), Chunk("Belgium"), Chunk("Netherlands"), Chunk("Portugal"), Chunk("Spain")],
		"corpus2": [Chunk("Spain"), Chunk("Belgium"), Chunk("Switzerland"),
			  		Chunk("Austria"), Chunk("China"), Chunk("the UK"), Chunk("the USA"), Chunk("Czechia")]
	}
	output_chunks_by_corpus = model.generate_by_corpus(input_chunks_by_corpus, show_progress=True, show_separate_progresses=True)
	for corpus, output_chunks in output_chunks_by_corpus.items():
		print(f"Corpus: {corpus}")
		for output_chunk in output_chunks:
			print(f"  Input: {output_chunk.metadata['input_chunk'].text} -> Output: {output_chunk.text}")

def _test_pipeline():
	import os
	api_key = os.getenv("OPENROUTER_API_KEY")
	llm_service = LLMService(api_key)
	template1 = Template("What is the capital of {$DATA}? Answer with just the name of the city, no punctuation.")
	model1 = Model(llm_service, "arcee-ai/trinity-large-preview:free", template1)

	template2 = Template("What is the population of {$DATA}?")
	model2 = Model(llm_service, "arcee-ai/trinity-large-preview:free", template2)

	pipeline = Pipeline([model1, model2])
	input_chunk = Chunk("France")
	output_chunk = asyncio.run(pipeline.generate_async(input_chunk))
	print(output_chunk.text)

def _test_pipeline_parallel():
	import os
	api_key = os.getenv("OPENROUTER_API_KEY")
	llm_service = LLMService(api_key)
	template1 = Template("What is the capital of {$DATA}? Answer with just the name of the city, no punctuation.")
	model1 = Model(llm_service, "arcee-ai/trinity-large-preview:free", template1)

	template2 = Template("What is the population of {$DATA}? Answer with just the number, no punctuation.")
	model2 = Model(llm_service, "arcee-ai/trinity-large-preview:free", template2)

	pipeline = Pipeline([model1, model2])
	input_chunks_by_corpus = {
		"corpus1": [Chunk("France"), Chunk("Germany"), Chunk("Italy"), Chunk("Austria"), Chunk("Poland"),
					Chunk("Switzerland"), Chunk("Belgium"), Chunk("Netherlands"), Chunk("Portugal"), Chunk("Spain")],
		"corpus2": [Chunk("Spain"), Chunk("Belgium"), Chunk("Switzerland"),
			  		Chunk("Austria"), Chunk("China"), Chunk("the UK"), Chunk("the USA"), Chunk("Czechia")],
		"corpus3": [Chunk("Canada"), Chunk("China"), Chunk("India"), Chunk("Russia"), Chunk("Brazil")]
	}
	output_chunks_by_corpus = pipeline.generate_by_corpus(input_chunks_by_corpus, show_progress=True, show_separate_progresses=True)
	for corpus, output_chunks in output_chunks_by_corpus.items():
		print(f"Corpus: {corpus}")
		for output_chunk in output_chunks:
			print(f"  Input: {output_chunk.metadata['input_chunk'].text} -> Output: {output_chunk.text} (Success: {output_chunk.metadata['success']})")

def _test_example_model():
	import os
	api_key = os.getenv("OPENROUTER_API_KEY")
	llm_service = LLMService(api_key)
	template = Template("""What is the capital of {$DATA}? Answer with just the name of the city, no punctuation.
Here are some examples:
Example 1: {$EXAMPLE_1_INPUT} -> {$EXAMPLE_1_OUTPUT}
Example 2: {$EXAMPLE_2_INPUT} -> {$EXAMPLE_2_OUTPUT}
Example 3: {$EXAMPLE_3_INPUT} -> {$EXAMPLE_3_OUTPUT}
""")
	examples = [
		Example(Chunk("France"), Chunk("Paris")),
		Example(Chunk("Germany"), Chunk("Berlin")),
		Example(Chunk("Italy"), Chunk("Rome"))
	]
	model = ExampleModel(llm_service, "arcee-ai/trinity-large-preview:free", template, examples)
	input_chunk = Chunk("Spain")
	output_chunk = asyncio.run(model.generate_async(input_chunk))
	print(output_chunk.text)

if __name__ == "__main__":
	#_test_single()
	#_test_pipeline()
	#_test_parallel()
	#_test_pipeline_parallel()
	_test_example_model()
