# Landcore
CRAC 2026 submission and master thesis by Jan Pavelka.

## Installation
This project depends on a local checkout of the CorefUD scorer. The upstream project is not a standard Python package and does not provide a `setup.py` or `pyproject.toml`, so it must be cloned into the repository root and its dependencies installed from that local repo.

From the project root, run:

```bash
git clone --depth 1 https://github.com/ufal/corefud-scorer.git corefud-scorer
python -m pip install -r corefud-scorer/requirements.txt
```

The project expects the scorer script at `corefud-scorer/corefud-scorer.py`.

Then, the other dependencies must be installed:
```bash
python -m pip install -r requirements.txt
```

## Usage
The demo usage:
```bash
bash landcore_demo.sh --or-api-key <YOUR_OPEN_ROUTER_API_KEY>
```
Note that a single annotation by the default DeepSeek model costs about 4-6 dollars. You can change the model like this:
```bash
bash landcore_demo.sh --or-api-key <YOUR_OPEN_ROUTER_API_KEY> --or-model <OPENROUTER_ID_OF_YOUR_MODEL>
```
Further modifications can be done in the config file. The config file can be specified:
```bash
bash landcore_demo.sh --or-api-key <YOUR_OPEN_ROUTER_API_KEY> --or-model <OPENROUTER_ID_OF_YOUR_MODEL> --config <PATH_TO_YOUR_CONFIG_FILE>
```