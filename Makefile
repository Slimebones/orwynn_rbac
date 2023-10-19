export PYTEST_SHOW=all
export args
export t=.

test:
	poetry run coverage run -m pytest -x --ignore=tests/app -p no:warnings --show-capture=$(PYTEST_SHOW) --failed-first $(args) $(t)

lint:
	poetry run ruff $(args) $(t)

check: lint test

coverage:
	poetry run coverage report -m

coverage.html:
	poetry run coverage html --show-contexts && python -m http.server -d htmlcov 8000
