#!/usr/bin/env python3

import argparse
import logging
import os
import time

import yaml

from config import Config
from run import run

parser = argparse.ArgumentParser(description="Run CRAC annotation experiment")
parser.add_argument("--config", help="Path to config file", default="configs/config_free_whole_recall_prompt_reindexed2_zero_longest_json_debug.yaml")#project/config.yaml
parser.add_argument(
	"--print_config",
	help="Print config and exit. Optionally provide output file path.",
	nargs='?',
	const='-',
	default=None,
)
parser.add_argument("--debug", help="Run in debug mode with a predefined config", action='store_true')

# Adjust config:
parser.add_argument("--annotation_format", help="Override config: experiment.annotation_format")
parser.add_argument("--output_directory", help="Override config: experiment.directory")
parser.add_argument("--language", help="Override config: data.language")
parser.add_argument("--input_format", help="Override config: data.input_format")	
parser.add_argument("--data_chunk_size", help="Override config: data.chunk_size.size", type=int)
parser.add_argument("--data_chunk_size_unit", help="Override config: data.chunk_size.unit")
parser.add_argument("--data_directory", help="Override config: data.directory")
parser.add_argument("--examples_choosing_strategy", help="Override config: examples.choosing_strategy")
parser.add_argument("--examples_number", help="Override config: examples.number", type=int)
parser.add_argument("--examples_chunk_size", help="Override config: examples.chunk_size.size", type=int)
parser.add_argument("--examples_chunk_size_unit", help="Override config: examples.chunk_size.unit")
parser.add_argument("--examples_directory", help="Override config: examples.directory")
parser.add_argument("--prompt_template", help="Override config: prompt.template")
parser.add_argument("--prompt_construction_strategy", help="Override config: prompt.construction_strategy")
parser.add_argument("--prompt_instructions", help="Override config: prompt.instructions_directory (expects directory path)")
parser.add_argument("--attempts", help="Override config: run.attempts", type=int)
parser.add_argument("--save_intermediate", help="Override config: run.save_intermediate", action='store_true')
parser.add_argument("--retries", help="Override config: run.retries", type=int)
parser.add_argument("--skip_existing", help="Override config: run.skip_existing", action='store_true')
parser.add_argument("--show_progress", help="Override config: run.show_progress", action='store_true')
parser.add_argument("--workers", help="Override config: run.workers", type=int)
parser.add_argument("--model", help="Override config: llm.model")
parser.add_argument("--temperature", help="Override config: llm.temperature")
parser.add_argument("--model_parameters", help="Override config: llm.parameters (expects YAML dictionary)", type=str)
parser.add_argument("--api_provider", help="Override config: api.provider")
parser.add_argument("--api_key", help="Override config: api.key")
parser.add_argument("--api_base_url", help="Override config: api.base_url")

def update_config_from_args(config: Config, args: argparse.Namespace):
	"""Update config values based on command-line arguments"""
	if args.annotation_format is not None:
		config.experiment.annotation_format = args.annotation_format
	if args.output_directory is not None:
		config.experiment.directory = args.output_directory
	if args.language is not None:
		config.data.language = args.language
	if args.input_format is not None:
		config.data.input_format = args.input_format
	if args.data_chunk_size is not None:
		config.data.chunk_size.size = args.data_chunk_size
	if args.data_chunk_size_unit is not None:
		config.data.chunk_size.unit = args.data_chunk_size_unit
	if args.data_directory is not None:
		config.data.directory = args.data_directory
	if args.examples_choosing_strategy is not None:
		config.examples.choosing_strategy = args.examples_choosing_strategy
	if args.examples_number is not None:
		config.examples.number = args.examples_number
	if args.examples_chunk_size is not None:
		config.examples.chunk_size.size = args.examples_chunk_size
	if args.examples_chunk_size_unit is not None:
		config.examples.chunk_size.unit = args.examples_chunk_size_unit
	if args.examples_directory is not None:
		config.examples.directory = args.examples_directory
	if args.prompt_template is not None:
		config.prompt.template = args.prompt_template
	if args.prompt_construction_strategy is not None:
		config.prompt.construction_strategy = args.prompt_construction_strategy
	if args.prompt_instructions is not None:
		config.prompt.instructions_directory = args.prompt_instructions
	if args.attempts is not None:
		config.run.attempts = args.attempts
	if args.save_intermediate:
		config.run.save_intermediate = True
	if args.retries is not None:
		config.run.retries = args.retries
	if args.skip_existing:
		config.run.skip_existing = True
	if args.show_progress:
		config.run.show_progress = True
	if args.workers is not None:
		config.run.workers = args.workers
	if args.model is not None:
		config.llm.model = args.model
	if args.model_parameters is not None:
		try:
			parameters_dict = yaml.safe_load(args.model_parameters)
			if not isinstance(parameters_dict, dict):
				raise ValueError("Model parameters should be a YAML dictionary.")
			config.llm.parameters = parameters_dict
		except yaml.YAMLError as e:
			raise ValueError(f"Error parsing model parameters YAML: {e}")
	if args.temperature is not None:
		try:
			temp_value = float(args.temperature)
			config.llm.parameters.temperature = temp_value
		except ValueError:
			# If it's not a float, keep it as a string (e.g., "auto")
			config.llm.parameters.temperature = args.temperature
			if args.temperature == "auto" or args.temperature == "None":
				config.llm.parameters.temperature = None
	if args.api_provider is not None:
		config.api.provider = args.api_provider
	if args.api_key is not None:
		config.api.key = args.api_key
	if args.api_base_url is not None:
		config.api.base_url = args.api_base_url
	config.check(error_prefix="INVALID OPTION")

def print_config(config: Config, args: argparse.Namespace):
	config_text = config.dump()
	if args.print_config == '-':
		print(config_text)
	else:
		with open(args.print_config, 'w', encoding='utf-8') as f:
			f.write(config_text)

def main(args: argparse.Namespace):
	start_time = time.time()
	config = Config(args.config)
	update_config_from_args(config, args)
	if args.print_config is not None:
		print_config(config, args)
		return
	# Run the experiment with the given config
		# Save log to file
	if not os.path.exists(config.experiment.directory):
		os.makedirs(config.experiment.directory)
	logging_level = logging.DEBUG if args.debug else logging.INFO
	logging.basicConfig(filename=os.path.join(config.experiment.directory, 'annotation.log'), level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')
	logging.info(f"Starting annotation run with config: {args.config}")
	run(config)

	end_time = time.time()
	elapsed = end_time - start_time
	minutes, seconds = divmod(elapsed, 60)
	logging.info(f"Annotation run completed in {int(minutes)}:{seconds:.2f}.")
	print(f"Annotation run completed in {int(minutes)}:{int(seconds)}.")

if __name__ == "__main__":
	args = parser.parse_args()
	main(args)
	
