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

.PHONY: ui help

