MAKEFLAGS += --no-print-directory

# Do not remove this block. It is used by the 'help' rule when
# constructing the help output.
# help:
# help: Ray/Redis/Feast Demo Makefile help
# help:

SHELL:=/bin/bash

# help: help                      - display this makefile's help information
.PHONY: help
help:
	@grep "^# help\:" Makefile | grep -v grep | sed 's/\# help\: //' | sed 's/\# help\://'

# help:
# help: Feature Store
# help: -------------

# help: init-fs                   - intialize the Feast feature store with Redis
.PHONY: init-fs
init-fs:
	@rm -rf ./data/registry.db
	@cd feature_store/actions && python create_feature_store.py

# help: test-fs                   - Test feature retrieval
.PHONY: test-fs
test-fs:
	@cd feature_store/utils && python data_fetcher.py


# help:
# help: Train
# help: ----

# help: train                     - Train on a single node w/o Ray
.PHONY: train
train:
	@cd feature_store/actions && python train.py


# help: train-ray                 - Train distributed with Ray
.PHONY: train-ray
train-ray:
	@cd feature_store/actions && python train_w_ray_distributed.py


# help:
# help: Infer
# help: -----

# help: serve                     - Serve trained XGBoost model with Ray Serve
.PHONY: serve
serve:
	@cd feature_store/actions && python serve.py


# help: test-infer                - Test the inference pipeline for a sample loan request
.PHONY: test-infer
test-infer:
	@cd feature_store/utils && python test.py



# help:
# help: