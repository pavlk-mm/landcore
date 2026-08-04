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

# GOLD
## DEV
### ENTIRE
#### CoNLL-U
data/gold/dev/entire/conllu: data/downloaded/llm-gold-minidev
	mkdir -p data/gold/dev/entire/conllu
	cp -r data/downloaded/llm-gold-minidev/*.conllu data/gold/dev/entire/conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "$(OLD_SUFFIX).conllu" \
		--new-suffix "$(NEW_SUFFIX).conllu" \
		data/gold/dev/entire/conllu/*.conllu
data/gold/dev/entire/conllu-clean:
	rm -rf data/gold/dev/entire/conllu

#### TXT
data/gold/dev/entire/txt: data/downloaded/llm-gold-minidev
	mkdir -p data/gold/dev/entire/txt
	cp -r data/downloaded/llm-gold-minidev/*.txt data/gold/dev/entire/txt
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "$(OLD_SUFFIX).txt" \
		--new-suffix "$(NEW_SUFFIX).txt" \
		data/gold/dev/entire/txt/*.txt
data/gold/dev/entire/txt-clean:
	rm -rf data/gold/dev/entire/txt

#### EML
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

#### JSON
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

#### MML
data/gold/dev/entire/mml: data/gold/dev/entire/eml
	mkdir -p data/gold/dev/entire/mml
	bash ./preprocessing/eml2mml_all.sh \
		--output-dir data/gold/dev/entire/mml \
		--human_readable_json \
		--store_mentions \
		data/gold/dev/entire/eml/*.eml

data/gold/dev/entire/mml-clean:
	rm -rf data/gold/dev/entire/mml

### CHUNKED1500
#### CoNLL-U
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

#### TXT
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

#### EML
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

#### JSON
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

#### MML
data/gold/dev/chunked1500/mml: data/gold/dev/chunked1500/eml
	mkdir -p data/gold/dev/chunked1500/mml
	bash ./preprocessing/eml2mml_all.sh \
		--output-dir data/gold/dev/chunked1500/mml \
		--human_readable_json \
		--store_mentions \
		data/gold/dev/chunked1500/eml/*.eml
data/gold/dev/chunked1500/mml-clean:
	rm -rf data/gold/dev/chunked1500/mml


# GOLD
## TRAIN
### EXAMPLE
#### ENTIRE
##### CoNLL-U
data/gold/train/example/entire/conllu: data/downloaded/llm-gold-train
	mkdir -p data/gold/train/example/entire/conllu
	bash ./preprocessing/split_all.sh \
		data/downloaded/llm-gold-train \
		--split-ratio 0.125,0.125 \
		--upper-bounds 25000,10000 \
		--seed 42 \
		--shuffle \
		--format conllu \
		--output-dirs data/gold/train/tuning/entire/conllu,data/gold/train/small/entire/conllu,data/gold/train/example/entire/conllu
data/gold/train/example/entire/conllu-clean:
	rm -rf data/gold/train/example/entire/conllu

##### TXT
data/gold/train/example/entire/txt: data/gold/train/example/entire/conllu
	mkdir -p data/gold/train/example/entire/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/example/entire/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "-corefud.txt" \
		data/gold/train/example/entire/txt/*.txt
data/gold/train/example/entire/txt-clean:
	rm -rf data/gold/train/example/entire/txt

##### EML
data/gold/train/example/entire/eml: data/gold/train/example/entire/conllu
	mkdir -p data/gold/train/example/entire/eml
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/example/entire/eml \
		--skipchunk \
		--skipreindex \
		--format eml \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.eml" \
		--new-suffix "-corefud.eml" \
		data/gold/train/example/entire/eml/*.eml
data/gold/train/example/entire/eml-clean:
	rm -rf data/gold/train/example/entire/eml

##### JSON
data/gold/train/example/entire/json: data/gold/train/example/entire/conllu
	mkdir -p data/gold/train/example/entire/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/example/entire/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "-corefud.json" \
		data/gold/train/example/entire/json/*.json
data/gold/train/example/entire/json-clean:
	rm -rf data/gold/train/example/entire/json

##### MML
data/gold/train/example/entire/mml: data/gold/train/example/entire/eml
	mkdir -p data/gold/train/example/entire/mml
	bash ./preprocessing/eml2mml_all.sh \
		--output-dir data/gold/train/example/entire/mml \
		--human_readable_json \
		--store_mentions \
		data/gold/train/example/entire/eml/*.eml
data/gold/train/example/entire/mml-clean:
	rm -rf data/gold/train/example/entire/mml

#### CHUNKED500
##### CoNLL-U
data/gold/train/example/chunked500/conllu: data/gold/train/example/entire/conllu
	mkdir -p data/gold/train/example/chunked500/conllu
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/example/chunked500/conllu \
		--words 500 \
		--skipreindex \
		--skiptext \
		data/gold/train/example/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked.conllu" \
		--new-suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/chunked500/conllu/*.conllu
data/gold/train/example/chunked500/conllu-clean:
	rm -rf data/gold/train/example/chunked500/conllu

##### TXT
data/gold/train/example/chunked500/txt: data/gold/train/example/chunked500/conllu
	mkdir -p data/gold/train/example/chunked500/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/example/chunked500/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "-corefud.txt" \
		data/gold/train/example/chunked500/txt/*.txt
data/gold/train/example/chunked500/txt-clean:
	rm -rf data/gold/train/example/chunked500/txt

##### EML
data/gold/train/example/chunked500/eml: data/gold/train/example/chunked500/conllu
	mkdir -p data/gold/train/example/chunked500/eml
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/example/chunked500/eml \
		--skipchunk \
		--skipreindex \
		--format eml \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.eml" \
		--new-suffix "-corefud.eml" \
		data/gold/train/example/chunked500/eml/*.eml
data/gold/train/example/chunked500/eml-clean:
	rm -rf data/gold/train/example/chunked500/eml

##### JSON
data/gold/train/example/chunked500/json: data/gold/train/example/chunked500/conllu
	mkdir -p data/gold/train/example/chunked500/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/example/chunked500/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "-corefud.json" \
		data/gold/train/example/chunked500/json/*.json
data/gold/train/example/chunked500/json-clean:
	rm -rf data/gold/train/example/chunked500/json

##### MML
data/gold/train/example/chunked500/mml: data/gold/train/example/chunked500/eml
	mkdir -p data/gold/train/example/chunked500/mml
	bash ./preprocessing/eml2mml_all.sh \
		--output-dir data/gold/train/example/chunked500/mml \
		--human_readable_json \
		--store_mentions \
		data/gold/train/example/chunked500/eml/*.eml
data/gold/train/example/chunked500/mml-clean:
	rm -rf data/gold/train/example/chunked500/mml

### TUNING
#### ENTIRE
##### CoNLL-U
data/gold/train/tuning/entire/conllu: data/gold/train/example/entire/conllu
data/gold/train/tuning/entire/conllu-clean:
	rm -rf data/gold/train/tuning/entire/conllu

##### TXT
data/gold/train/tuning/entire/txt: data/gold/train/tuning/entire/conllu
	mkdir -p data/gold/train/tuning/entire/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/tuning/entire/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/tuning/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "-corefud.txt" \
		data/gold/train/tuning/entire/txt/*.txt
data/gold/train/tuning/entire/txt-clean:
	rm -rf data/gold/train/tuning/entire/txt

##### EML
data/gold/train/tuning/entire/eml: data/gold/train/tuning/entire/conllu
	mkdir -p data/gold/train/tuning/entire/eml
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/tuning/entire/eml \
		--skipchunk \
		--skipreindex \
		--format eml \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/tuning/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.eml" \
		--new-suffix "-corefud.eml" \
		data/gold/train/tuning/entire/eml/*.eml
data/gold/train/tuning/entire/eml-clean:
	rm -rf data/gold/train/tuning/entire/eml

##### JSON
data/gold/train/tuning/entire/json: data/gold/train/tuning/entire/conllu
	mkdir -p data/gold/train/tuning/entire/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/tuning/entire/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/tuning/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "-corefud.json" \
		data/gold/train/tuning/entire/json/*.json
data/gold/train/tuning/entire/json-clean:
	rm -rf data/gold/train/tuning/entire/json

##### MML
data/gold/train/tuning/entire/mml: data/gold/train/tuning/entire/eml
	mkdir -p data/gold/train/tuning/entire/mml
	bash ./preprocessing/eml2mml_all.sh \
		--output-dir data/gold/train/tuning/entire/mml \
		--human_readable_json \
		--store_mentions \
		data/gold/train/tuning/entire/eml/*.eml
data/gold/train/tuning/entire/mml-clean:
	rm -rf data/gold/train/tuning/entire/mml

#### CHUNKED500
##### CoNLL-U
data/gold/train/tuning/chunked500/conllu: data/gold/train/tuning/entire/conllu
	mkdir -p data/gold/train/tuning/chunked500/conllu
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/tuning/chunked500/conllu \
		--words 500 \
		--skipreindex \
		--skiptext \
		data/gold/train/tuning/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked.conllu" \
		--new-suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/tuning/chunked500/conllu/*.conllu
data/gold/train/tuning/chunked500/conllu-clean:
	rm -rf data/gold/train/tuning/chunked500/conllu

##### TXT
data/gold/train/tuning/chunked500/txt: data/gold/train/tuning/chunked500/conllu
	mkdir -p data/gold/train/tuning/chunked500/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/tuning/chunked500/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/tuning/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "-corefud.txt" \
		data/gold/train/tuning/chunked500/txt/*.txt
data/gold/train/tuning/chunked500/txt-clean:
	rm -rf data/gold/train/tuning/chunked500/txt

##### EML
data/gold/train/tuning/chunked500/eml: data/gold/train/tuning/chunked500/conllu
	mkdir -p data/gold/train/tuning/chunked500/eml
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/tuning/chunked500/eml \
		--skipchunk \
		--skipreindex \
		--format eml \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/tuning/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.eml" \
		--new-suffix "-corefud.eml" \
		data/gold/train/tuning/chunked500/eml/*.eml
data/gold/train/tuning/chunked500/eml-clean:
	rm -rf data/gold/train/tuning/chunked500/eml

##### JSON
data/gold/train/tuning/chunked500/json: data/gold/train/tuning/chunked500/conllu
	mkdir -p data/gold/train/tuning/chunked500/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/tuning/chunked500/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/tuning/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "-corefud.json" \
		data/gold/train/tuning/chunked500/json/*.json
data/gold/train/tuning/chunked500/json-clean:
	rm -rf data/gold/train/tuning/chunked500/json

##### MML
data/gold/train/tuning/chunked500/mml: data/gold/train/tuning/chunked500/eml
	mkdir -p data/gold/train/tuning/chunked500/mml
	bash ./preprocessing/eml2mml_all.sh \
		--output-dir data/gold/train/tuning/chunked500/mml \
		--human_readable_json \
		--store_mentions \
		data/gold/train/tuning/chunked500/eml/*.eml
data/gold/train/tuning/chunked500/mml-clean:
	rm -rf data/gold/train/tuning/chunked500/mml

### SMALL
#### ENTIRE
##### CoNLL-U
data/gold/train/small/entire/conllu: data/gold/train/example/entire/conllu
data/gold/train/small/entire/conllu-clean:
	rm -rf data/gold/train/small/entire/conllu

##### TXT
data/gold/train/small/entire/txt: data/gold/train/small/entire/conllu
	mkdir -p data/gold/train/small/entire/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/small/entire/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/small/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "-corefud.txt" \
		data/gold/train/small/entire/txt/*.txt
data/gold/train/small/entire/txt-clean:
	rm -rf data/gold/train/small/entire/txt

##### EML
data/gold/train/small/entire/eml: data/gold/train/small/entire/conllu
	mkdir -p data/gold/train/small/entire/eml
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/small/entire/eml \
		--skipchunk \
		--skipreindex \
		--format eml \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/small/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.eml" \
		--new-suffix "-corefud.eml" \
		data/gold/train/small/entire/eml/*.eml
data/gold/train/small/entire/eml-clean:
	rm -rf data/gold/train/small/entire/eml

##### JSON
data/gold/train/small/entire/json: data/gold/train/small/entire/conllu
	mkdir -p data/gold/train/small/entire/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/small/entire/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/small/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "-corefud.json" \
		data/gold/train/small/entire/json/*.json
data/gold/train/small/entire/json-clean:
	rm -rf data/gold/train/small/entire/json

##### MML
data/gold/train/small/entire/mml: data/gold/train/small/entire/eml
	mkdir -p data/gold/train/small/entire/mml
	bash ./preprocessing/eml2mml_all.sh \
		--output-dir data/gold/train/small/entire/mml \
		--human_readable_json \
		--store_mentions \
		data/gold/train/small/entire/eml/*.eml
data/gold/train/small/entire/mml-clean:
	rm -rf data/gold/train/small/entire/mml

#### CHUNKED500
##### CoNLL-U
data/gold/train/small/chunked500/conllu: data/gold/train/small/entire/conllu
	mkdir -p data/gold/train/small/chunked500/conllu
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/small/chunked500/conllu \
		--words 500 \
		--skipreindex \
		--skiptext \
		data/gold/train/small/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked.conllu" \
		--new-suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/small/chunked500/conllu/*.conllu
data/gold/train/small/chunked500/conllu-clean:
	rm -rf data/gold/train/small/chunked500/conllu

##### TXT
data/gold/train/small/chunked500/txt: data/gold/train/small/chunked500/conllu
	mkdir -p data/gold/train/small/chunked500/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/small/chunked500/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/small/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "-corefud.txt" \
		data/gold/train/small/chunked500/txt/*.txt
data/gold/train/small/chunked500/txt-clean:
	rm -rf data/gold/train/small/chunked500/txt

##### EML
data/gold/train/small/chunked500/eml: data/gold/train/small/chunked500/conllu
	mkdir -p data/gold/train/small/chunked500/eml
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/small/chunked500/eml \
		--skipchunk \
		--skipreindex \
		--format eml \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/small/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.eml" \
		--new-suffix "-corefud.eml" \
		data/gold/train/small/chunked500/eml/*.eml
data/gold/train/small/chunked500/eml-clean:
	rm -rf data/gold/train/small/chunked500/eml

##### JSON
data/gold/train/small/chunked500/json: data/gold/train/small/chunked500/conllu
	mkdir -p data/gold/train/small/chunked500/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/gold/train/small/chunked500/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/small/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "-corefud.json" \
		data/gold/train/small/chunked500/json/*.json
data/gold/train/small/chunked500/json-clean:
	rm -rf data/gold/train/small/chunked500/json

##### MML
data/gold/train/small/chunked500/mml: data/gold/train/small/chunked500/eml
	mkdir -p data/gold/train/small/chunked500/mml
	bash ./preprocessing/eml2mml_all.sh \
		--output-dir data/gold/train/small/chunked500/mml \
		--human_readable_json \
		--store_mentions \
		data/gold/train/small/chunked500/eml/*.eml
data/gold/train/small/chunked500/mml-clean:
	rm -rf data/gold/train/small/chunked500/mml

## TRAIN AGGREGATES
data/gold/train/example/all: \
	data/gold/train/example/entire/conllu \
	data/gold/train/example/entire/txt \
	data/gold/train/example/entire/eml \
	data/gold/train/example/entire/json \
	data/gold/train/example/entire/mml \
	data/gold/train/example/chunked500/conllu \
	data/gold/train/example/chunked500/txt \
	data/gold/train/example/chunked500/eml \
	data/gold/train/example/chunked500/json \
	data/gold/train/example/chunked500/mml

data/gold/train/tuning/all: \
	data/gold/train/tuning/entire/conllu \
	data/gold/train/tuning/entire/txt \
	data/gold/train/tuning/entire/eml \
	data/gold/train/tuning/entire/json \
	data/gold/train/tuning/entire/mml \
	data/gold/train/tuning/chunked500/conllu \
	data/gold/train/tuning/chunked500/txt \
	data/gold/train/tuning/chunked500/eml \
	data/gold/train/tuning/chunked500/json \
	data/gold/train/tuning/chunked500/mml

data/gold/train/small/all: \
	data/gold/train/small/entire/conllu \
	data/gold/train/small/entire/txt \
	data/gold/train/small/entire/eml \
	data/gold/train/small/entire/json \
	data/gold/train/small/entire/mml \
	data/gold/train/small/chunked500/conllu \
	data/gold/train/small/chunked500/txt \
	data/gold/train/small/chunked500/eml \
	data/gold/train/small/chunked500/json \
	data/gold/train/small/chunked500/mml

data/gold/train/all: \
	data/gold/train/example/all \
	data/gold/train/tuning/all \
	data/gold/train/small/all

# BLIND
## DEV
### ENTIRE
#### CoNLL-U
data/blind/dev/entire/conllu: data/downloaded/llm-input_blind-minidev
	mkdir -p data/blind/dev/entire/conllu
	cp -r data/downloaded/llm-input_blind-minidev/*.conllu data/blind/dev/entire/conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "$(OLD_SUFFIX).conllu" \
		--new-suffix "$(NEW_SUFFIX).conllu" \
		data/blind/dev/entire/conllu/*.conllu
data/blind/dev/entire/conllu-clean:
	rm -rf data/blind/dev/entire/conllu

#### TXT
data/blind/dev/entire/txt: data/downloaded/llm-input_blind-minidev
	mkdir -p data/blind/dev/entire/txt
	cp -r data/downloaded/llm-input_blind-minidev/*.txt data/blind/dev/entire/txt
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "$(OLD_SUFFIX).txt" \
		--new-suffix "$(NEW_SUFFIX).txt" \
		data/blind/dev/entire/txt/*.txt
data/blind/dev/entire/txt-clean:
	rm -rf data/blind/dev/entire/txt

#### JSON
data/blind/dev/entire/json: data/blind/dev/entire/conllu
	mkdir -p data/blind/dev/entire/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/dev/entire/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--blind \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/blind/dev/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "-corefud.json" \
		data/blind/dev/entire/json/*.json
data/blind/dev/entire/json-clean:
	rm -rf data/blind/dev/entire/json

### CHUNKED1500
#### CoNLL-U
data/blind/dev/chunked1500/conllu: data/blind/dev/entire/conllu
	mkdir -p data/blind/dev/chunked1500/conllu
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/dev/chunked1500/conllu \
		--words 1500 \
		--skipreindex \
		--skiptext \
		data/blind/dev/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked.conllu" \
		--new-suffix "$(NEW_SUFFIX).conllu" \
		data/blind/dev/chunked1500/conllu/*.conllu
data/blind/dev/chunked1500/conllu-clean:
	rm -rf data/blind/dev/chunked1500/conllu

#### TXT
data/blind/dev/chunked1500/txt: data/blind/dev/chunked1500/conllu
	mkdir -p data/blind/dev/chunked1500/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/dev/chunked1500/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--blind \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/blind/dev/chunked1500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "$(NEW_SUFFIX).txt" \
		data/blind/dev/chunked1500/txt/*.txt
data/blind/dev/chunked1500/txt-clean:
	rm -rf data/blind/dev/chunked1500/txt

#### JSON
data/blind/dev/chunked1500/json: data/blind/dev/chunked1500/conllu
	mkdir -p data/blind/dev/chunked1500/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/dev/chunked1500/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--blind \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/blind/dev/chunked1500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "$(NEW_SUFFIX).json" \
		data/blind/dev/chunked1500/json/*.json
data/blind/dev/chunked1500/json-clean:
	rm -rf data/blind/dev/chunked1500/json

## TRAIN
### EXAMPLE
#### ENTIRE
##### TXT
data/blind/train/example/entire/txt: data/gold/train/example/entire/conllu
	mkdir -p data/blind/train/example/entire/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/train/example/entire/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--blind \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "$(NEW_SUFFIX).txt" \
		data/blind/train/example/entire/txt/*.txt
data/blind/train/example/entire/txt-clean:
	rm -rf data/blind/train/example/entire/txt

##### JSON
data/blind/train/example/entire/json: data/gold/train/example/entire/conllu
	mkdir -p data/blind/train/example/entire/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/train/example/entire/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--blind \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "$(NEW_SUFFIX).json" \
		data/blind/train/example/entire/json/*.json
data/blind/train/example/entire/json-clean:
	rm -rf data/blind/train/example/entire/json

#### CHUNKED500
##### TXT
data/blind/train/example/chunked500/txt: data/gold/train/example/chunked500/conllu
	mkdir -p data/blind/train/example/chunked500/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/train/example/chunked500/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--blind \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "$(NEW_SUFFIX).txt" \
		data/blind/train/example/chunked500/txt/*.txt
data/blind/train/example/chunked500/txt-clean:
	rm -rf data/blind/train/example/chunked500/txt

##### JSON
data/blind/train/example/chunked500/json: data/gold/train/example/chunked500/conllu
	mkdir -p data/blind/train/example/chunked500/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/train/example/chunked500/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--blind \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/gold/train/example/chunked500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "$(NEW_SUFFIX).json" \
		data/blind/train/example/chunked500/json/*.json
data/blind/train/example/chunked500/json-clean:
	rm -rf data/blind/train/example/chunked500/json

## TEST
### ENTIRE
#### CoNLL-U
data/blind/test/entire/conllu: data/downloaded/llm-input_blind-minitest
	mkdir -p data/blind/test/entire/conllu
	cp -r data/downloaded/llm-input_blind-minitest/*.conllu data/blind/test/entire/conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-corefud-minitest.conllu" \
		--new-suffix "$(NEW_SUFFIX).conllu" \
		data/blind/test/entire/conllu/*.conllu
data/blind/test/entire/conllu-clean:
	rm -rf data/blind/test/entire/conllu

#### TXT
data/blind/test/entire/txt: data/downloaded/llm-input_blind-minitest
	mkdir -p data/blind/test/entire/txt
	cp -r data/downloaded/llm-input_blind-minitest/*.txt data/blind/test/entire/txt
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-corefud-minitest.txt" \
		--new-suffix "$(NEW_SUFFIX).txt" \
		data/blind/test/entire/txt/*.txt
data/blind/test/entire/txt-clean:
	rm -rf data/blind/test/entire/txt

#### JSON
data/blind/test/entire/json: data/blind/test/entire/conllu
	mkdir -p data/blind/test/entire/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/test/entire/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--blind \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/blind/test/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "$(NEW_SUFFIX).json" \
		data/blind/test/entire/json/*.json
data/blind/test/entire/json-clean:
	rm -rf data/blind/test/entire/json

### CHUNKED1500
#### CoNLL-U
data/blind/test/chunked1500/conllu: data/blind/test/entire/conllu
	mkdir -p data/blind/test/chunked1500/conllu
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/test/chunked1500/conllu \
		--words 1500 \
		--skipreindex \
		--skiptext \
		data/blind/test/entire/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked.conllu" \
		--new-suffix "$(NEW_SUFFIX).conllu" \
		data/blind/test/chunked1500/conllu/*.conllu
data/blind/test/chunked1500/conllu-clean:
	rm -rf data/blind/test/chunked1500/conllu

#### TXT
data/blind/test/chunked1500/txt: data/blind/test/chunked1500/conllu
	mkdir -p data/blind/test/chunked1500/txt
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/test/chunked1500/txt \
		--skipchunk \
		--skipreindex \
		--format txt \
		--blind \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/blind/test/chunked1500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.txt" \
		--new-suffix "$(NEW_SUFFIX).txt" \
		data/blind/test/chunked1500/txt/*.txt
data/blind/test/chunked1500/txt-clean:
	rm -rf data/blind/test/chunked1500/txt

#### JSON
data/blind/test/chunked1500/json: data/blind/test/chunked1500/conllu
	mkdir -p data/blind/test/chunked1500/json
	bash ./preprocessing/preprocess_all.sh \
		--output-dir data/blind/test/chunked1500/json \
		--skipchunk \
		--skipreindex \
		--format json \
		--blind \
		--suffix "$(NEW_SUFFIX).conllu" \
		data/blind/test/chunked1500/conllu/*.conllu
	bash ./preprocessing/copy_rename_suffix.sh \
		--old-suffix "-chunked_reindexed.json" \
		--new-suffix "$(NEW_SUFFIX).json" \
		data/blind/test/chunked1500/json/*.json
data/blind/test/chunked1500/json-clean:
	rm -rf data/blind/test/chunked1500/json

## BLIND AGGREGATES
data/blind/dev/all: \
	data/blind/dev/entire/conllu \
	data/blind/dev/entire/txt \
	data/blind/dev/entire/json \
	data/blind/dev/chunked1500/conllu \
	data/blind/dev/chunked1500/txt \
	data/blind/dev/chunked1500/json

data/blind/train/all: \
	data/blind/train/example/entire/txt \
	data/blind/train/example/entire/json \
	data/blind/train/example/chunked500/txt \
	data/blind/train/example/chunked500/json

data/blind/test/all: \
	data/blind/test/entire/conllu \
	data/blind/test/entire/txt \
	data/blind/test/entire/json \
	data/blind/test/chunked1500/conllu \
	data/blind/test/chunked1500/txt \
	data/blind/test/chunked1500/json

data/blind/all: \
	data/blind/dev/all \
	data/blind/train/all \
	data/blind/test/all


# CLEANING UP
clean: downloaded-clean