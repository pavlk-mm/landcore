import json_repair
import logging
import json

class Chunk:
	def __init__(self, text_or_dict: str|dict, metadata: dict = None, parse_json: bool = False):
		self.metadata = metadata or {}
		self._tokens = []
		self._clusters_token_offsets = []
		self._clusters_text_mentions = []
		if isinstance(text_or_dict, dict):
			self.json_dict = text_or_dict
		elif isinstance(text_or_dict, str):
			if parse_json:
				self.json_str = text_or_dict
			else:
				self._tokens = text_or_dict.split(" ")
				self._clusters_token_offsets = []
				self._clusters_text_mentions = []
		else:
			raise ValueError(f"Invalid type for text_or_dict: {type(text_or_dict)}. Expected str or dict.")
		if (self.tokens is None or len(self.tokens) == 0) and "input_chunk" in self.metadata:
			self.tokens = self.metadata["input_chunk"].tokens
		if parse_json:
			self._fix_clusters_token_offsets()

	@property
	def text(self) -> str:
		return " ".join(self._tokens) if self._tokens is not None else ""
	
	@text.setter
	def text(self, value: str):
		self._tokens = value.split(" ") if value is not None else []

	def blind_text_with_context(self, prefix: str = "", before_text: str = "", after_text: str = "", suffix: str = "", separator: str = "\n") -> str:
		return f"{prefix}{before_text}{self.text}{after_text}{suffix}"

	def __str__(self):
		return self.text

	@property
	def json_dict(self) -> dict:
		return {
			"doc_id" : self.metadata.get("doc_id", None),
			"tokens" : self._tokens,
			"clusters_token_offsets": self._clusters_token_offsets,
			"clusters_text_mentions": self._clusters_text_mentions
		}

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

	@property
	def json_str(self):
		return json.dumps(self.json_dict, ensure_ascii=False)
	
	@json_str.setter
	def json_str(self, json_str: str):
		self.json_dict = json_repair.loads(json_str)
	
	@property
	def tokens(self) -> list[str]:
		return self._tokens
	
	@tokens.setter
	def tokens(self, tokens: list[str]):
		self._tokens = tokens

	def get_dict(self, what_to_include: list[str]) -> dict:
		result = {}
		if "doc_id" in what_to_include:
			result["doc_id"] = self.metadata.get("doc_id", None)
		if "tokens" in what_to_include:
			result["tokens"] = self._tokens
		if "clusters_token_offsets" in what_to_include:
			result["clusters_token_offsets"] = self._clusters_token_offsets
		if "clusters_text_mentions" in what_to_include:
			result["clusters_text_mentions"] = self._clusters_text_mentions
		return result
	
	def _fix_mention(self, mention: list, max_offset: int) -> list[int]:
		if not isinstance(mention, list):
			if isinstance(mention, int):
				return [mention, mention]
			else:
				logging.warning(f"Invalid mention format in clusters_token_offsets: {mention}. Expected list of two integers. Skipping this mention.")
				return None
		
		mention_int = [m for m in mention if isinstance(m, int)]
		if len(mention_int) == 0:
			logging.warning(f"Invalid mention format in clusters_token_offsets: {mention}. Expected list of two integers. Skipping this mention.")
			return None
		mention_int = sorted(mention_int)
		if mention_int[0] < 0:
			mention_int[0] = 0
		if mention_int[-1] > max_offset:
			mention_int[-1] = max_offset

		if mention_int[0] > mention_int[-1]:
			return None
		return [mention_int[0], mention_int[-1]]
	
	def _mentions_equal(self, mention1: list[int], mention2: list[int]) -> bool:
		return mention1[0] == mention2[0] and mention1[1] == mention2[1]
	
	def _mention_in_cluster(self, mention: list[int], cluster: list[list[int]]) -> bool:
		for existing_mention in cluster:
			if self._mentions_equal(mention, existing_mention):
				return True
		return False
	
	def _fix_cluster(self, cluster: list[list], max_offset: int) -> list[list[int]]:
		fixed_cluster = []
		if not isinstance(cluster, list):
			logging.warning(f"Invalid cluster format in clusters_token_offsets: {cluster}. Expected list of mentions. Skipping this cluster.")
			return None
		if len(cluster) == 0:
			logging.warning(f"Empty cluster in clusters_token_offsets. Skipping this cluster.")
			return None
		for mention in cluster:
			fixed_mention = self._fix_mention(mention, max_offset)
			if fixed_mention is not None and not self._mention_in_cluster(fixed_mention, fixed_cluster):
				fixed_cluster.append(fixed_mention)
		return fixed_cluster

	def _fix_clusters(self, clusters: list[list[list]], max_offset: int) -> list[list[list[int]]]:
		fixed_clusters = []
		if not isinstance(clusters, list):
			logging.warning(f"Invalid clusters format in clusters_token_offsets: {clusters}. Expected list of clusters. Skipping clusters.")
			return []
		for cluster in clusters:
			fixed_cluster = self._fix_cluster(cluster, max_offset)
			if fixed_cluster is not None and len(fixed_cluster) > 0:
				fixed_clusters.append(fixed_cluster)
		return fixed_clusters
	
	def _fix_clusters_token_offsets(self):
		if self.tokens is not None and len(self.tokens) > 0:
			max_offset = len(self.tokens) - 1
			self._clusters_token_offsets = self._fix_clusters(self._clusters_token_offsets, max_offset)

class ChunkInContext(Chunk):
	def __init__(self, text: str, left_context: list[Chunk], right_context: list[Chunk], **kwargs):
		super().__init__(text, **kwargs)
		self.left_context = left_context
		self.right_context = right_context
	
	def blind_text_with_context(self, prefix: str = "", before_text: str = "\n", after_text: str = "\n", suffix: str = "", separator: str = "\n") -> str:
		left_context_text = separator.join([chunk.text for chunk in self.left_context])
		right_context_text = separator.join([chunk.text for chunk in self.right_context])
		return f"{prefix}{left_context_text}{before_text}{self.text}{after_text}{right_context_text}{suffix}"

def construct_base_chunks(texts: list[str], metadata: dict = {}, doc_ids: list[str] = None) -> list[Chunk]:
	"""Construct chunks from the given texts."""
	chunks = []
	for i, (text, doc_id) in enumerate(zip(texts, doc_ids or [None] * len(texts))):
		metadata_with_index = {"index" : i}
		if metadata:
			metadata_with_index.update(metadata)
		if doc_id is None:
			doc_id = metadata["corpus"] + f"_{i}" if "corpus" in metadata else str(i)
		metadata_with_index["doc_id"] = doc_id
		chunks.append(Chunk(text, metadata_with_index))
	return chunks

def construct_chunks_in_context(texts: list[str], left_context_size: int, right_context_size: int, metadata: dict = None, doc_ids: list[str] = None) -> list[ChunkInContext]:
	"""Construct chunks with context from the given texts."""
	chunks = construct_base_chunks(texts, metadata, doc_ids)
	chunks_in_context = []
	for i in range(len(chunks)):
		left_context = chunks[max(0, i - left_context_size):i]
		right_context = chunks[i + 1:i + 1 + right_context_size]
		chunk_in_context = ChunkInContext(
			text=chunks[i].text,
			left_context=left_context,
			right_context=right_context,
			metadata=chunks[i].metadata
		)
		chunks_in_context.append(chunk_in_context)
	for i in range(len(chunks_in_context)):
		left_context = chunks_in_context[max(0, i - left_context_size):i]
		right_context = chunks_in_context[i + 1:i + 1 + right_context_size]
		chunks_in_context[i].left_context = left_context
		chunks_in_context[i].right_context = right_context
	return chunks_in_context

def construct(
		texts: list[str],
		context_strategy: str = "none",
		left_context_size: int = 0,
		right_context_size: int = 0,
		metadata: dict = None,
		doc_ids: list[str] = None
	) -> list[Chunk | ChunkInContext]:
	if context_strategy == "none":
		return construct_base_chunks(texts, metadata, doc_ids)
	elif context_strategy == "in-context":
		return construct_chunks_in_context(texts, left_context_size, right_context_size, metadata, doc_ids)
	else:
		raise ValueError(f"Invalid context strategy: {context_strategy}")

def _test():
	texts = [f"Text {i}" for i in range(10)]
	chunks_in_context = construct(texts, context_strategy="in-context", left_context_size=2, right_context_size=2)
	for chunk in chunks_in_context:
		print(chunk.blind_text_with_context(prefix="< ", before_text=" $ ", after_text=" & ", suffix=" >", separator=" , "))

if __name__ == "__main__":
	_test()
