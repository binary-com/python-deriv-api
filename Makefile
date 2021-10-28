.PHONY: all setup test doc gh-pages build
all: setup test
setup:
	pip3 install pipenv && pipenv install --dev
test:
	pipenv run python setup.py pytest
doc:
	pdoc deriv_api --force --html -o docs/html --template-dir docs/templates
gh-pages:
	pdoc deriv_api --force --html -o /tmp/python-deriv-api-docs --template-dir docs/templates && git add . && git stash && git checkout gh-pages && cp -r /tmp/python-deriv-api-docs/deriv_api/* . && git add . && git commit -m 'Update docs' && git push && git checkout -
build:
	pip3 install build && python3 -m build
coverage:
	pipenv run coverage run --source deriv_api -m pytest && pipenv run coverage report -m 
