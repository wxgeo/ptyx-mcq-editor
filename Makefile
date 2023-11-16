ui:
	pyuic6 -o ptyx_mcq_editor/ui/main_ui.py -x ui/main.ui
	pyuic6 -o ptyx_mcq_editor/ui/find_and_replace_ui.py -x ui/find_and_replace.ui

help:
	@cat Makefile

.PHONY: ui help

