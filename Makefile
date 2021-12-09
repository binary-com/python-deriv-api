.PHONY: all setup test doc gh-pages build
all: setup test
setup:
	pip3 install pipenv && pipenv install --dev
test:
	pipenv run python setup.py pytest
doc:
	pipenv run pdoc deriv_api --force --html -o docs/html --template-dir docs/templates
build:
	pip3 install build && python3 -m build
coverage:
	pipenv run coverage run --source deriv_api -m pytest && pipenv run coverage report -m
