ui:
	pyuic6 -o ptyx_mcq_editor/ui/main.py -x ui/main.ui
	pyuic6 -o ptyx_mcq_editor/ui/find_and_replace.py -x ui/find_and_replace.ui
	pyuic6 -o ptyx_mcq_editor/ui/find.py -x ui/find.ui

help:
	@cat Makefile

.PHONY: ui help

