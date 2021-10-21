.PHONY: all setup test doc
all: setup test
setup:
	pip3 install pipenv && pipenv install --dev && pipenv shell
test:
	pipenv run python setup.py pytest
doc:
	pdoc deriv_api --force --html -o docs/html --template-dir docs/templates
