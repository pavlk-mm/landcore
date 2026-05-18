from udapi.core.block import Block

class Chunker(Block):
	def __init__(self, words=1024, make_new_docs=True, write_chunk_ids=True, **kwargs):
		super().__init__(**kwargs)
		self.words = words
		self.newdoc = None
		self.make_new_docs = make_new_docs
		self.write_chunk_ids = write_chunk_ids

	def chunk_name(self, chunk_number, include_doc_id=True):
		if include_doc_id:
			return f"{self.newdoc}_{chunk_number:03d}"
		else:
			return f"{chunk_number:03d}"

	def add_new_chunk(self, tree, chunk_number):
		if self.make_new_docs:
			tree.newdoc = self.chunk_name(chunk_number)
		if self.write_chunk_ids:
			tree.add_comment(f"chunk_id = {self.chunk_name(chunk_number, include_doc_id=False)}")

	def process_document(self, document):
		for bundle in document.bundles:
			tree = bundle.get_tree()
			if tree.newdoc:
				self.newdoc = tree.newdoc
				chunk_number = 0
				word_count = 0
				self.add_new_chunk(tree, chunk_number)

			words_in_sentence = len(tree.descendants)

			if word_count + words_in_sentence > self.words:
				chunk_number += 1
				word_count = 0
				self.add_new_chunk(tree, chunk_number)

			word_count += words_in_sentence
