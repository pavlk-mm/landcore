"""Constructing examples for prompting using the data from gold files."""

import random
import json_repair
from chunks import Chunk

class Example(Chunk):
	def __init__(self, blind: str, gold: str, **kwargs):
		super().__init__(gold, **kwargs)
		self._blind_tokens = None
		if isinstance(blind, dict):
			json_dict = self.json_dict
			json_dict["blind_tokens"] = blind["tokens"]
			self.json_dict = json_dict
		elif isinstance(blind, str):
			if "parse_json" in kwargs and kwargs["parse_json"]:
				blind_json_dict = json_repair.loads(blind)
				self._blind_tokens = blind_json_dict["tokens"]
			else:
				self._blind_tokens = blind.split(" ")
		else:
			raise ValueError(f"Invalid type fot blind: {type(blind)}. Expected str or dict.")
	
	@property
	def json_dict(self) -> dict:
		json_dict = super().json_dict
		json_dict["blind_tokens"] = self._blind_tokens
		return json_dict
	
	@json_dict.setter
	def json_dict(self, json_dict: dict):
		if "doc_id" in json_dict:
			self.metadata["doc_id"] = json_dict.get("doc_id", None)
		if "tokens" in json_dict:
			self._tokens = json_dict.get("tokens", [])
		if "clusters_token_offsets" in json_dict:
			self._clusters_token_offsets = json_dict.get("clusters_token_offsets", [])
		if "clusters_text_mentions" in json_dict:
			self._clusters_text_mentions = json_dict.get("clusters_text_mentions", [])
		if "blind_tokens" in json_dict:
			self._blind_tokens = json_dict.get("blind_tokens", [])
	
	@property
	def gold(self):
		return self.text
	@gold.setter
	def gold(self, value):
		self.text = value
	
	@property
	def blind(self):
		return " ".join(self._blind_tokens) if self._blind_tokens is not None else ""
	@blind.setter
	def blind(self, value):
		self._blind_tokens = value.split(" ") if value is not None else []

	def blind_text_with_context(self, prefix: str = "", before_text: str = "", after_text: str = "", suffix: str = "", separator: str = "\n") -> str:
		return f"{prefix}{before_text}{self.blind}{after_text}{suffix}"

	def gold_text_with_context(self, prefix: str = "", before_text: str = "", after_text: str = "", suffix: str = "", separator: str = "\n") -> str:
		return f"{prefix}{before_text}{self.gold}{after_text}{suffix}"
	
	def get_dict(self, what_to_include: list[str]) -> dict:
		results = super().get_dict(what_to_include)
		if "blind_tokens" in what_to_include:
			results["blind_tokens"] = self._blind_tokens
		return results

class ExampleInContext(Example):
	def __init__(self, 
		blind: str,
		gold: str,
		left_context: list[Example],
		right_context: list[Example],
		**kwargs
	):
		super().__init__(blind, gold, **kwargs)
		self.left_context = left_context
		self.right_context = right_context
	
	def blind_text_with_context(self, prefix: str = "", before_text: str = "\n", after_text: str = "\n", suffix: str = "", separator: str = "\n") -> str:
		left_context_text = separator.join([example.blind for example in self.left_context])
		right_context_text = separator.join([example.blind for example in self.right_context])
		return f"{prefix}{left_context_text}{before_text}{self.blind}{after_text}{right_context_text}{suffix}"
	
	def gold_text_with_context(self, prefix: str = "", before_text: str = "\n", after_text: str = "\n", suffix: str = "", separator: str = "\n") -> str:
		left_context_text = separator.join([example.gold for example in self.left_context])
		right_context_text = separator.join([example.gold for example in self.right_context])
		return f"{prefix}{left_context_text}{before_text}{self.gold}{after_text}{right_context_text}{suffix}"

def construct_base_examples(blind_texts: list[str], gold_texts: list[str]) -> list[Example]:
	"""Construct base examples without context."""
	return [Example(blind, gold) for blind, gold in zip(blind_texts, gold_texts)]

def construct_in_context_examples(blind_texts: list[str], gold_texts: list[str], left_context_size: int, right_context_size: int) -> list[ExampleInContext]:
	"""Construct examples with context."""
	# First construct the base examples without context
	base_examples = construct_base_examples(blind_texts, gold_texts)
	# Then construct the in-context examples using the base examples
	in_context_examples = []
	for i in range(len(base_examples)):
		left_context = base_examples[max(0, i - left_context_size):i]
		right_context = base_examples[i + 1:i + 1 + right_context_size]
		in_context_example = ExampleInContext(
			blind=base_examples[i].blind,
			gold=base_examples[i].gold,
			left_context=left_context,
			right_context=right_context
		)
		in_context_examples.append(in_context_example)
	# Finally, we can set the left and right context for each in-context example.
	# We need to exchange the base examples in the left and right context with
	# the in-context examples, so that the context includes the examples with
	# context as well.
	for i in range (len(in_context_examples)):
		left_context = in_context_examples[max(0, i - left_context_size):i]
		right_context = in_context_examples[i + 1:i + 1 + right_context_size]
		in_context_examples[i].left_context = left_context
		in_context_examples[i].right_context = right_context
	return in_context_examples

def choose_examples(examples: list, number: int, strategy: str="first") -> list:
	"""Choose examples according to the given strategy."""
	number = min(number, len(examples))
	if strategy == "random":
		return random.sample(examples, number)
	elif strategy == "first":
		return examples[:number]
	elif strategy == "last":
		return examples[-number:]
	elif strategy == "longest":
		return sorted(examples, key=lambda example: len(example.blind) if hasattr(example, "blind") else len(example), reverse=True)[:number]
	else:
		raise ValueError(f"Unknown strategy: {strategy}")

def construct(
		blind_texts: list[str],
		gold_texts: list[str],
		number: int = 1,
		choose_strategy: str = "first",
		context_strategy: str = "none",
		left_context_size: int = 0,
		right_context_size: int = 0
	) -> list[Example]:
	"""Construct examples according to the given strategies."""
	if context_strategy == "none":
		examples = construct_base_examples(blind_texts, gold_texts)
	elif context_strategy == "in-context":
		examples = construct_in_context_examples(blind_texts, gold_texts, left_context_size, right_context_size)
	else:
		raise ValueError(f"Unknown context strategy: {context_strategy}")
	return choose_examples(examples, number, choose_strategy)

def _test():
	blind_texts = ["Blind text 1", "Blind text 2", "Blind text 3", "Blind text 4", "Blind text 5"]
	gold_texts = ["Gold text 1", "Gold text 2", "Gold text 3", "Gold text 4", "Gold text 5"]
	examples = construct(blind_texts, gold_texts, number=3, choose_strategy="random", context_strategy="none", left_context_size=1, right_context_size=1)
	for example in examples:
		print("Blind with context:")
		print(example.blind_text_with_context(prefix="Left context:\t", before_text="\nExample:\t", after_text="\nRight context:\t"))
		print("Gold with context:")
		print(example.gold_text_with_context(prefix="Left context:\t", before_text="\nExample:\t", after_text="\nRight context:\t"))
		print()

if __name__ == "__main__":
	_test()
