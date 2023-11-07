ui:
	pyuic6 -o ptyx_mcq_editor/ui/main.py -x ui/main.ui

help:
	@cat Makefile

.PHONY: ui help

