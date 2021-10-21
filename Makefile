.PHONY: test doc
test:
	pipenv run python setup.py pytest
doc:
	pdoc deriv_api --force --html -o docs/html --template-dir docs/templates
