from udapi.core.block import Block

class PrintMentionClusters(Block):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

	def process_document(self, document):
		pass
