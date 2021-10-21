.PHONY: test
test:
	PYTHONPATH=.  pipenv run pytest -vvv -s tests
