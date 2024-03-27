.PHONY: ruff mypy black isort test pytest lint

all: lint test
lint: ruff black isort mypy
test: pytest

ruff:
	ruff check .

black:
	black squall setup.py --check --diff

isort:
	isort . --diff --check

mypy:
	mypy squall setup.py

pytest:
	pytest

fmt:
	ruff . --fix
	black squall setup.py
	isort .
