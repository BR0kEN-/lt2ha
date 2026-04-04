.PHONY: venv

venv:
	python3 -m venv venv

i:
	pip install .[dev]

test:
	pytest ./tests --cov ./src/lt2ha -vvv --cov-report term

ci: test
