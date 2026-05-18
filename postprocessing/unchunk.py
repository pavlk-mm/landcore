from udapi.core.block import Block

class Unchunk(Block):
	def __init__(self, rewrite_new_docs=True, delete_chunk_ids=False, **kwargs):
		super().__init__(**kwargs)
		self.rewrite_new_docs = rewrite_new_docs
		self.delete_chunk_ids = delete_chunk_ids

	def remove_chunk_id_from_newdoc(self, newdoc):
		return "_".join(newdoc.split("_")[:-1])

	# def remove_chunk_id_from_comment(self, comment):
	# 	# TODO
	# 	comment = comment.split("\n")
	# 	comment = [line for line in comment if not line.startswith("# chunk_id")]
	# 	return "\n".join(comment)
	
	def remove_newdoc(self, tree):
		tree.newdoc = None

	def process_document(self, document):
		for bundle in document.bundles:
			tree = bundle.get_tree()
			if tree.newdoc:
				chunk_number = int(tree.newdoc.split("_")[-1])
				if chunk_number == 0:
					if self.rewrite_new_docs:
						tree.newdoc = self.remove_chunk_id_from_newdoc(tree.newdoc)
				else:
					tree.newdoc = None
				# if self.delete_chunk_ids:
				# 	tree.comment = self.remove_chunk_id_from_comment(tree.comment)
