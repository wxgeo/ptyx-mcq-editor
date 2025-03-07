ui:
	@./.build_ui

tox:
	poetry run black .
	poetry run tox

fix:
	poetry run black .
	poetry run ruff check --fix ptyx_mcq_editor tests

help:
	@cat Makefile

lock:
	git commit poetry.lock -m "dev: update poetry.lock"

.PHONY: ui help

