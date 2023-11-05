help:
	cat Makefile

ui:
	pyuic6 -o ptyx_mcq_editor/main.py -x interfaces/main.ui
