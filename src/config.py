import yaml
import os
from urllib.parse import urlparse

LANGUAGES = {
    "ca" : "Catalan",
    "cs" : "Czech",
    "cu" : "Old Church Slavonic",
    "de" : "German",
    "en" : "English",
    "es" : "Spanish",
    "fr" : "French",
    "grc" : "Ancient Greek",
    "hbo" : "Biblical Hebrew",
    "hi" : "Hindi",
    "hu" : "Hungarian",
    "ko" : "Korean",
    "la" : "Latin",
    "lt" : "Lithuanian",
    "nl" : "Dutch",
    "no" : "Norwegian",
    "pl" : "Polish",
    "ru" : "Russian",
    "tr" : "Turkish"
}

def _is_url(url):
    try:
        result = urlparse(url)
        # Check if both scheme and netloc (domain) are present
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

class DataObject:
    def __init__(self, data):
        for key, value in data.items():
            # If the value is a dict, convert it to a DataObject recursively
            if isinstance(value, dict):
                setattr(self, key, DataObject(value))
            # If it's a list, check for dicts inside the list
            elif isinstance(value, list):
                setattr(self, key, [DataObject(i) if isinstance(i, dict) else i for i in value])
            else:
                setattr(self, key, value)

    def __repr__(self):
        return f"{self.__dict__}"
    
    def to_dict(self):
        result = {}
        # Iterate over the instance's __dict__
        for key, value in self.__dict__.items():
            if isinstance(value, DataObject):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [i.to_dict() if isinstance(i, DataObject) else i for i in value]
            else:
                result[key] = value
        return result

class Config(DataObject):
    REQUIRED_SECTIONS = ["experiment", "data", "examples", "prompt", "run", "llm", "api"]
    ANNOTATION_FORMATS = ["plaintext", "json", "eml"]
    LANGUAGES = ["auto"] + list(LANGUAGES.keys())
    INPUT_FORMATS = ["plaintext", "json", "eml"]
    CHUNK_UNITS = ["words", "sentences", "characters", "tokens"]
    CHOOSE_STRATEGIES = ["first", "random", "last", "longest"]
    CONSTRUCTION_STRATEGIES = ["few-shots", "zero-shot", "simple"]
    API_PROVIDERS = ["OpenRouter"]
    DEFAULT_PROMPT_TEMPLATE = "project/prompt_templates/improved_high_recall_empty_tokens_by_corpus_eml_3examples.txt"

    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        super().__init__(data)
        self.check()
        self.prompt.template = self.expand_prompt_template_path(self.prompt.template)
        self.check_prompt_template_paths()

    def dump(self):
        return yaml.dump(self.to_dict(), sort_keys=True)
    
    def check_sections(self, error_prefix="INVALID CONFIG"):
        for section in self.REQUIRED_SECTIONS:
            if not hasattr(self, section):
                raise ValueError(f"{error_prefix} Missing required section: {section}")

    def expand_macro_by_corpora(self, macro: str, values: list[str], default_text: str = "") -> dict[str, str]:
        expanded_values = {"default": default_text}
        if "$CORPUS" in macro:
            for value in values:
                expanded_values[value] = macro.replace("$CORPUS", value)
        elif "$LANGUAGE" in macro:
            for value in values:
                expanded_values[value] = macro.replace("$LANGUAGE", value.split("_")[0])
        return expanded_values
    
    def expand_prompt_template_path(self, template_path: str) -> dict[str, str]:
        if "$CORPUS" not in template_path and "$LANGUAGE" not in template_path:
            return {"default": template_path}
        values = set()
        for dirpath, _, filenames in os.walk(self.data.directory):
            for filename in filenames:
                if filename.endswith(".conllu") or filename.endswith(".eml") or filename.endswith(".txt"):
                    corpus = os.path.basename(dirpath).split("-")[0]
                    if "$CORPUS" in template_path:
                        values.add(corpus)
                    elif "$LANGUAGE" in template_path:
                        language = corpus.split("_")[0]
                        values.add(language)
        return self.expand_macro_by_corpora(template_path, sorted(values), default_text=self.DEFAULT_PROMPT_TEMPLATE)

    def check_prompt_template_paths(self, error_prefix="INVALID CONFIG"):
        for corpus, path in self.prompt.template.items():
            if not os.path.exists(path):
                raise ValueError(f"{error_prefix} prompt: template for corpus '{corpus}': {path} does not exist")

    def check_values(self, error_prefix="INVALID CONFIG"):
        # Check experiment section
        if self.experiment.annotation_format not in self.ANNOTATION_FORMATS:
            raise ValueError(f"{error_prefix} experiment: annotation_format: {self.experiment.annotation_format}. Expected one of {self.ANNOTATION_FORMATS}")
        # if not os.path.exists(self.experiment.directory):
        #     raise ValueError(f"{error_prefix} experiment: directory: {self.experiment.directory} does not exist")
        # Check data section
        if self.data.language not in self.LANGUAGES:
            raise ValueError(f"{error_prefix} data: language: {self.data.language}. Expected one of {self.LANGUAGES}")
        if self.data.input_format not in self.INPUT_FORMATS:
            raise ValueError(f"{error_prefix} data: input_format: {self.data.input_format}. Expected one of {self.INPUT_FORMATS}")
        if not isinstance(self.data.chunk_size.size, int):
            raise ValueError(f"{error_prefix} data: chunk_size: size: Expected int, got {type(self.data.chunk_size.size).__name__}")
        if self.data.chunk_size.size <= 0:
            raise ValueError(f"{error_prefix} data: chunk_size: size: {self.data.chunk_size.size}. Expected positive int.")
        if self.data.chunk_size.unit not in self.CHUNK_UNITS:
            raise ValueError(f"{error_prefix} data: chunk_size: unit: {self.data.chunk_size.unit}. Expected one of {self.CHUNK_UNITS}")
        if not os.path.exists(self.data.directory):
            raise ValueError(f"{error_prefix} data: directory: {self.data.directory} does not exist")
        if self.data.only_indices_file is not None and not os.path.exists(self.data.only_indices_file):
            raise ValueError(f"{error_prefix} data: only_indices_file: {self.data.only_indices_file} does not exist")
        # Check examples section
        if self.examples.choose_strategy not in self.CHOOSE_STRATEGIES:
            raise ValueError(f"{error_prefix} examples: choose_strategy: {self.examples.choose_strategy}. Expected one of {self.CHOOSE_STRATEGIES}")
        if not isinstance(self.examples.number, int):
            raise ValueError(f"{error_prefix} examples: number: Expected int, got {type(self.examples.number).__name__}")
        if self.examples.number < 0:
            raise ValueError(f"{error_prefix} examples: number: {self.examples.number}. Expected non-negative int.")
        if not isinstance(self.examples.chunk_size.size, int):
            raise ValueError(f"{error_prefix} examples: chunk_size: size: Expected int, got {type(self.examples.chunk_size.size).__name__}")
        if self.examples.chunk_size.size <= 0:
            raise ValueError(f"{error_prefix} examples: chunk_size: size: {self.examples.chunk_size.size}. Expected positive int.")
        if self.examples.chunk_size.unit not in self.CHUNK_UNITS:
            raise ValueError(f"{error_prefix} examples: chunk_size: unit: {self.examples.chunk_size.unit}. Expected one of {self.CHUNK_UNITS}")
        if not os.path.exists(self.examples.directory_gold):
            raise ValueError(f"{error_prefix} examples: directory_gold: {self.examples.directory_gold} does not exist")
        if not os.path.exists(self.examples.directory_blind):
            raise ValueError(f"{error_prefix} examples: directory_blind: {self.examples.directory_blind} does not exist")
        # Check prompt section
        if not isinstance(self.prompt.template, dict) and not "$LANGUAGE" in self.prompt.template and not "$CORPUS" in self.prompt.template and not os.path.exists(self.prompt.template):
            raise ValueError(f"{error_prefix} prompt: template: {self.prompt.template} does not exist")
        if self.prompt.construction_strategy not in self.CONSTRUCTION_STRATEGIES:
            raise ValueError(f"{error_prefix} prompt: construction_strategy: {self.prompt.construction_strategy}. Expected one of {self.CONSTRUCTION_STRATEGIES}")
        # Check run section
        if not isinstance(self.run.attempts, int):
            raise ValueError(f"{error_prefix} run: attempts: Expected int, got {type(self.run.attempts).__name__}")
        if self.run.attempts < 0:
            raise ValueError(f"{error_prefix} run: attempts: {self.run.attempts}. Expected non-negative int.")
        if not isinstance(self.run.save_intermediate, bool):
            raise ValueError(f"{error_prefix} run: save_intermediate: Expected bool, got {type(self.run.save_intermediate).__name__}")
        if not isinstance(self.run.retries, int):
            raise ValueError(f"{error_prefix} run: retries: Expected int, got {type(self.run.retries).__name__}")
        if self.run.retries < 0:
            raise ValueError(f"{error_prefix} run: retries: {self.run.retries}. Expected non-negative int.")
        if not isinstance(self.run.skip_existing, bool):
            raise ValueError(f"{error_prefix} run: skip_existing: Expected bool, got {type(self.run.skip_existing).__name__}")
        if not isinstance(self.run.show_progress, bool):
            raise ValueError(f"{error_prefix} run: show_progress: Expected bool, got {type(self.run.show_progress).__name__}")
        if not isinstance(self.run.show_separate_progress_bars, bool):
            raise ValueError(f"{error_prefix} run: show_separate_progress_bars: Expected bool, got {type(self.run.show_separate_progress_bars).__name__}")
        if not isinstance(self.run.concurrency, int):
            raise ValueError(f"{error_prefix} run: concurrency: Expected int, got {type(self.run.concurrency).__name__}")
        if self.run.concurrency < 1:
            raise ValueError(f"{error_prefix} run: concurrency: {self.run.concurrency}. Expected int greater than 0.")
        # Check llm section
        # if not isinstance(self.llm.temperature, float) and self.llm.temperature != "auto":
        #     raise ValueError(f"{error_prefix} llm: temperature: Expected float, got {type(self.llm.temperature).__name__}")
       # Check api section
        if self.api.provider not in self.API_PROVIDERS:
            raise ValueError(f"{error_prefix} api: provider: {self.api.provider}. Expected one of {self.API_PROVIDERS}")
        if self.api.key.startswith("$"):
            env_var = self.api.key[1:]
            if env_var not in os.environ:
                raise ValueError(f"{error_prefix} api: key: Environment variable {env_var} not found")
        if not _is_url(self.api.base_url):
            raise ValueError(f"{error_prefix} api: base_url: {self.api.base_url}. Expected valid URL.")

    def check(self, error_prefix="INVALID CONFIG"):
        self.check_sections(error_prefix=error_prefix)
        self.check_values(error_prefix=error_prefix)
    
    def get_api_key(self):
        if self.api.key.startswith("$"):
            env_var = self.api.key[1:]
            return os.getenv(env_var)
        return self.api.key

def _test():
    config = Config(os.path.join(os.path.dirname(__file__), 'config.yaml'))
    print(config.dump())

if __name__ == "__main__":
    _test()
