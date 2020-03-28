SRC_PATH 		= supremepancake
OUT_PATH 		= out
SPHINX_PATH 	= docs
UNITTEST_PATH 	= tests
RUN_ARGS	   ?= --help

.ONESHELL:

all: format typecheck lint

.PHONY: docs
docs:
	sphinx-build -b html $(SPHINX_PATH)/ $(OUT_PATH)/docs/html/
	-@xdg-open $(OUT_PATH)/docs/html/index.html

.PHONY: format
format:
	yapf --in-place --recursive --style pep8 --verbose $(SRC_PATH)

.PHONY: lint
lint:
	pylint $(SRC_PATH)

.PHONY: run
run:
	@set -a
	-@. ./venv/bin/activate
	@python3 $(SRC_PATH)/supremepancake.py $(RUN_ARGS)

.PHONY: typecheck
typecheck:
	mypy $(SRC_PATH)/*.py
