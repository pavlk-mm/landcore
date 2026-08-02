# Makefile for downloading and extracting the CRAC 2026 shared task data.
.PHONY: all clean

OLD_SUFFIX ?= -corefud-minidev
NEW_SUFFIX ?= -corefud

all: data/downloaded/llm-gold-train data/downloaded/llm-gold-minidev data/downloaded/llm-input_blind-minidev data/downloaded/llm-input_blind-minitest

# DOWNLOADING DATA
## Make sure the downloaded directory exists
data/downloaded:
	mkdir -p data/downloaded

## Download the zip files into the `downloaded` directory
data/downloaded/llm-gold-train.zip: | data/downloaded
	wget -P data/downloaded https://ufal.mff.cuni.cz/~mnovak/files/crac26/llm-gold-train.zip
data/downloaded/llm-gold-minidev.zip: | data/downloaded
	wget -P data/downloaded https://ufal.mff.cuni.cz/~mnovak/files/crac26/llm-gold-minidev.zip
data/downloaded/llm-input_blind-minidev.zip: | data/downloaded
	wget -P data/downloaded https://ufal.mff.cuni.cz/~mnovak/files/crac26/llm-input_blind-minidev.zip
data/downloaded/llm-input_blind-minitest.zip: | data/downloaded
	wget -P data/downloaded https://ufal.mff.cuni.cz/~mnovak/files/crac26/llm-input_blind-minitest.zip

## Extract the zip files into their respective directories
data/downloaded/llm-gold-train: data/downloaded/llm-gold-train.zip
	mkdir -p data/downloaded/llm-gold-train
	unzip data/downloaded/llm-gold-train.zip -d data/downloaded/llm-gold-train
data/downloaded/llm-gold-minidev: data/downloaded/llm-gold-minidev.zip
	mkdir -p data/downloaded/llm-gold-minidev
	unzip data/downloaded/llm-gold-minidev.zip -d data/downloaded/llm-gold-minidev
data/downloaded/llm-input_blind-minidev: data/downloaded/llm-input_blind-minidev.zip
	mkdir -p data/downloaded/llm-input_blind-minidev
	unzip data/downloaded/llm-input_blind-minidev.zip -d data/downloaded/llm-input_blind-minidev
data/downloaded/llm-input_blind-minitest: data/downloaded/llm-input_blind-minitest.zip
	mkdir -p data/downloaded/llm-input_blind-minitest
	unzip data/downloaded/llm-input_blind-minitest.zip -d data/downloaded/llm-input_blind-minitest

data/downloaded-all: data/downloaded/llm-gold-train data/downloaded/llm-gold-minidev data/downloaded/llm-input_blind-minidev data/downloaded/llm-input_blind-minitest

## Clean up downloaded zip files and extracted directories
data/downloaded-zip-clean:
	rm -f data/downloaded/llm-gold-train.zip data/downloaded/llm-gold-minidev.zip data/downloaded/llm-input_blind-minidev.zip data/downloaded/llm-input_blind-minitest.zip
data/downloaded-dirs-clean:
	rm -rf data/downloaded/llm-gold-train data/downloaded/llm-gold-minidev data/downloaded/llm-input_blind-minidev data/downloaded/llm-input_blind-minitest
data/downloaded-clean: data/downloaded-zip-clean data/downloaded-dirs-clean


# DEV
## ENTIRE
### CoNLL-U
data/gold/dev/entire/conllu: data/downloaded/llm-gold-minidev
	mkdir -p data/gold/dev/entire/conllu
	cp -r data/downloaded/llm-gold-minidev/*.conllu data/gold/dev/entire/conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "$(OLD_SUFFIX).conllu" \
		--new-suffix "$(NEW_SUFFIX).conllu" \
		data/gold/dev/entire/conllu/*.conllu
data/gold/dev/entire/conllu-clean:
	rm -rf data/gold/dev/entire/conllu

### TXT
data/gold/dev/entire/txt: data/downloaded/llm-gold-minidev
	mkdir -p data/gold/dev/entire/txt
	cp -r data/downloaded/llm-gold-minidev/*.txt data/gold/dev/entire/txt
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "$(OLD_SUFFIX).txt" \
		--new-suffix "$(NEW_SUFFIX).txt" \
		data/gold/dev/entire/txt/*.txt
data/gold/dev/entire/txt-clean:
	rm -rf data/gold/dev/entire/txt

### EML
data/gold/dev/entire/eml: data/gold/dev/entire/conllu
	mkdir -p data/gold/dev/entire/eml
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/dev/entire/eml \
		--skipchunk \
		--skipreindex \
		--format eml \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/dev/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.eml" \
		--new-suffix "-corefud.eml" \
		data/gold/dev/entire/eml/*.eml
data/gold/dev/entire/eml-clean:
	rm -rf data/gold/dev/entire/eml

### JSON
data/gold/dev/entire/json: data/gold/dev/entire/conllu
	mkdir -p data/gold/dev/entire/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/dev/entire/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/dev/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "-corefud.json" \
		data/gold/dev/entire/json/*.json
data/gold/dev/entire/json-clean:
	rm -rf data/gold/dev/entire/json

### MML
data/gold/dev/entire/mml: data/gold/dev/entire/eml
	mkdir -p data/gold/dev/entire/mml
	bash ./preprocessing/eml2mml_all.sh \
		--output-dir data/gold/dev/entire/mml \
		--human_readable_json \
		--store_mentions \
		data/gold/dev/entire/eml/*.eml

data/gold/dev/entire/mml-clean:
	rm -rf data/gold/dev/entire/mml

## CHUNKED1500
### CoNLL-U
data/gold/dev/chunked1500/conllu: data/gold/dev/entire/conllu
	mkdir -p data/gold/dev/chunked1500/conllu
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/dev/chunked1500/conllu \
		--words 1500 \
		--skipreindex \
		--skiptext \
		data/gold/dev/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked.conllu" \
		--new-suffix "$(NEW_SUFFIX).conllu" \
		data/gold/dev/chunked1500/conllu/*.conllu
data/gold/dev/chunked1500/conllu-clean:
	rm -rf data/gold/dev/chunked1500/conllu

### TXT
data/gold/dev/chunked1500/txt: data/gold/dev/chunked1500/conllu
	mkdir -p data/gold/dev/chunked1500/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/dev/chunked1500/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/dev/chunked1500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "-corefud.txt" \
		data/gold/dev/chunked1500/txt/*.txt
data/gold/dev/chunked1500/txt-clean:
	rm -rf data/gold/dev/chunked1500/txt

### EML
data/gold/dev/chunked1500/eml: data/gold/dev/chunked1500/conllu
	mkdir -p data/gold/dev/chunked1500/eml
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/dev/chunked1500/eml \
		--skipchunk \
		--skipreindex \
		--format eml \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/dev/chunked1500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.eml" \
		--new-suffix "-corefud.eml" \
		data/gold/dev/chunked1500/eml/*.eml
data/gold/dev/chunked1500/eml-clean:
	rm -rf data/gold/dev/chunked1500/eml

### JSON
data/gold/dev/chunked1500/json: data/gold/dev/chunked1500/conllu
	mkdir -p data/gold/dev/chunked1500/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/dev/chunked1500/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/dev/chunked1500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "-corefud.json" \
		data/gold/dev/chunked1500/json/*.json
data/gold/dev/chunked1500/json-clean:
	rm -rf data/gold/dev/chunked1500/json

### MML
data/gold/dev/chunked1500/mml: data/gold/dev/chunked1500/eml
	mkdir -p data/gold/dev/chunked1500/mml
	bash ./preprocessing/eml2mml_all.sh \
		--output-dir data/gold/dev/chunked1500/mml \
		--human_readable_json \
		--store_mentions \
		data/gold/dev/chunked1500/eml/*.eml
data/gold/dev/chunked1500/mml-clean:
	rm -rf data/gold/dev/chunked1500/mml


# TRAIN
## EXAMPLE
### ENTIRE
#### CoNLL-U
data/gold/train/example/entire/conllu: data/downloaded/llm-gold-train
	mkdir -p data/gold/train/example/entire/conllu
	bash ./preprocessing/split_all.sh \
		data/downloaded/llm-gold-train \
		--split-ratio 0.125,0.125 \
		--upper-bounds 25000,10000 \
		--seed 42 \
		--format conllu \
		--output-dirs data/gold/train/tuning/entire/conllu,data/gold/train/small/entire/conllu,data/gold/train/example/entire/conllu



# CLEANING UP
clean: downloaded-clean