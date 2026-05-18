import json

from chunks import Chunk
from examples import Example

class Template:
	def __init__ (self, template: str, variables: list[str] = []):
		self.template = template
		self.variables = variables

	def render(self, variables: dict[str, str]) -> str:
		rendered = self.template
		for var in variables:
			# TODO: Consider whether to raise an error or just leave the variable as is in the template
			# raise ValueError(f"Variable '{var}' is missing from the provided variables.")
			rendered = rendered.replace(f"{{{var}}}", variables[var])
		return rendered

class Prompt:
	def __init__(self, template: Template, data: Chunk, variables: dict[str, str]):
		self.template = template
		self.data = data
		self.variables = variables
		self._update_variables()

	def _update_variables(self):
		self.variables["$DATA"] = self.data.text

	def render(self) -> str:
		return self.template.render(self.variables)

class ExamplePrompt(Prompt):
	def __init__(self,
		template: Template,
		data: Chunk,
		examples: list[Example],
		variables: dict[str, str],
		input_format: str = "plaintext",
		what_in_input: set[str] = {"blind_tokens"},
		output_format: str = "plaintext",
		what_in_output: set[str] = {"clusters_token_offsets", "clusters_text_mentions"}
	):
		self.examples = examples
		self.input_format = input_format
		self.output_format = output_format
		self.what_in_input = what_in_input
		self.what_in_output = what_in_output
		super().__init__(template, data, variables)

	def _dump_input(self, example: Example) -> str:
		if self.input_format == "json":
			input_dict = example.get_dict(self.what_in_input)
			input_list = [(key, json.dumps(input_dict[key], ensure_ascii=False)) for key in self.what_in_input if key in input_dict]
			return f"{{{', '.join([f'\"{key}\": {value}' for key, value in input_list])}}}"
		else:
			return example.blind
	
	def _dump_output(self, example: Example) -> str:
		if self.output_format == "json":
			output_dict = example.get_dict(self.what_in_output)
			output_list = [(key, json.dumps(output_dict[key], ensure_ascii=False)) for key in self.what_in_output if key in output_dict]
			return f"{{{', '.join([f'\"{key}\": {value}' for key, value in output_list])}}}"
		else:
			return example.gold

	def _update_variables(self):
		super()._update_variables()
		for i, example in enumerate(self.examples):
			self.variables[f"$EXAMPLE_{i+1}_INPUT"] = self._dump_input(example)
			self.variables[f"$EXAMPLE_{i+1}_OUTPUT"] = self._dump_output(example)

def _test_template():
	template = Template("This is a template {k} with variables: {var1}, {var2}.", ["var1", "var2"])
	variables = {"var1": "value1", "var2": "value2"}
	rendered = template.render(variables)
	print(rendered)
	assert rendered == "This is a template {k} with variables: value1, value2."

def _test_prompt():
	template = Template("Data: {$DATA}.")
	data = Chunk("This is some data.")
	variables = {}
	prompt = Prompt(template, data, variables)
	rendered = prompt.render()
	print(rendered)
	assert rendered == "Data: This is some data.."

if __name__ == "__main__":
	_test_template()
	_test_prompt()
	var = "test"
	pokus = f"{{{var}}}"
	print(pokus)
