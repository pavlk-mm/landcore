import asyncio
from openai import AsyncOpenAI
import logging
import os

"""This module provides the LLMService class which encapsulates the logic for
interacting with the OpenAI API."""

class LLMService:
	def __init__(
		self,
		api_key: str,
		concurrency: int = 5,
		base_url: str="https://openrouter.ai/api/v1",
		delay: int = 20,
		response_log_file: str = "failed_llm_responses.log",
		**kwargs
	):
		self.client = AsyncOpenAI(
			base_url=base_url,
			api_key=api_key,
			**kwargs
		)
		self.responses = []
		self.concurrency = concurrency
		self.semaphore = None  # Will be initialized lazily in the event loop
		self.delay = delay
		self.response_logger = logging.getLogger("llm.responses")
		self.response_logger.setLevel(logging.INFO)
		self.response_logger.propagate = False

		if response_log_file:
			response_log_path = os.path.abspath(response_log_file)
			response_log_dir = os.path.dirname(response_log_path)
			if response_log_dir:
				os.makedirs(response_log_dir, exist_ok=True)

			handler_exists = any(
				isinstance(handler, logging.FileHandler)
				and getattr(handler, "baseFilename", None) == response_log_path
				for handler in self.response_logger.handlers
			)
			if not handler_exists:
				file_handler = logging.FileHandler(response_log_path, encoding="utf-8")
				file_handler.setLevel(logging.INFO)
				file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
				self.response_logger.addHandler(file_handler)
	
	def reset_semaphore(self):
		self.semaphore = None

	async def generate(self, prompt: str, model: str, retries: int = 3, **kwargs) -> tuple[bool, str]:
		# Lazy initialization of semaphore to bind it to the current event loop
		if self.semaphore is None:
			self.semaphore = asyncio.Semaphore(self.concurrency)
		
		async with self.semaphore:
			for attempt in range(retries):
				try:
					response = await self.client.chat.completions.create(
						model=model,
						messages=[{"role": "user", "content": prompt}],
						# extra_body={
						# 	"provider": {
						# 		#"ignore": ["sambanova", "deepinfra/fp4"],
						# 		"only" : ["atlas-cloud/fp8", "siliconflow/fp8", "friendli"],
						# 		"allow_fallbacks": False,
						# 		#"order": ["atlas-cloud/fp8", "siliconflow/fp8", "digitalocean", "friendli", "parasail/fp8", "alibaba", "google-vertex", "streamlake", "novita/fp8", "baidu/fp8"]
						# 	}
						# },
						**kwargs
					)
					self.responses.append(response)
					# if response.choices[0].finish_reason == "stop":

					if response.choices[0].message.content is None:
						logging.warning(f"Received response with no content for prompt '...{prompt[-50:].split('\n')[0]}'. Retrying ({attempt + 1}/{retries})...")
						self.response_logger.info(f"Prompt chunk: {prompt.splitlines()[-3]}")
						self.response_logger.warning(f"Full response: {response}")
						if attempt == retries - 1:
							return False, ""
						else:
							continue
					return True, response.choices[0].message.content
				# TODO: Catch specific exceptions related to rate limits and transient errors
				except Exception as e:
					logging.warning(f"Error generating response for prompt '...{prompt[-50:].split('\n')[0]}': {e}. Retrying ({attempt + 1}/{retries})...")
					if attempt == retries - 1:
						return False, ""
					else:
						delay = self.delay #e.body['metadata'].get('retry_after_seconds', self.delay) if hasattr(e, 'body') else self.delay
						await asyncio.sleep(int(delay))



async def _test():
	import os
	api_key = os.getenv("OPENROUTER_API_KEY")
	model = "arcee-ai/trinity-large-preview:free"
	llm_service = LLMService(api_key)
	prompt = "What is the capital of France?"
	success, response = await llm_service.generate(prompt, model=model)
	print(success, response)
	print(llm_service.responses[0])

async def _test_parallel():
	import os
	from tqdm import tqdm
	#semaphore = asyncio.Semaphore(5)
	api_key = os.getenv("OPENROUTER_API_KEY")
	model = "arcee-ai/trinity-large-preview:free"
	llm_service = LLMService(api_key)
	prompts = [
		"What is the capital of France?",
		"What is the capital of Germany?",
		"What is the capital of Italy?",
		"What is the capital of Spain?",
		"What is the capital of Portugal?",
		"What is the capital of Netherlands?",
		"What is the capital of Belgium?",
		"What is the capital of Switzerland?",
		"What is the capital of Austria?",
		"What is the capital of Poland?"
		]

	async def _generate_one(i: int, prompt: str):
		return i, await llm_service.generate(prompt, model=model)

	responses = [None] * len(prompts)
	tasks = [asyncio.create_task(_generate_one(i, prompt)) for i, prompt in enumerate(prompts)]

	with tqdm(total=len(tasks), desc="Generating", unit="prompt") as progress:
		for completed in asyncio.as_completed(tasks):
			i, (success, response) = await completed
			responses[i] = response
			print(f"Received response for prompt {i}: {response}")
			progress.update(1)

	print(*responses, sep="\n")

if __name__ == "__main__":
	#asyncio.run(_test())
	asyncio.run(_test_parallel())
