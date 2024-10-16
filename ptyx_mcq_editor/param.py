from pathlib import Path

RESSOURCES_PATH = Path(__file__).resolve().parent.parent / "ressources"
ICON_PATH = RESSOURCES_PATH / "mcq-editor.svg"
WINDOW_TITLE = "MCQ Editor"
DEBUG = True
SHELL_COMMAND = "mcq-editor"
DESKTOP_FILE_NAME = "ptyx-mcq-editor.desktop"
ICON_NAME = "mcq-editor.svg"
ICON_DIR = Path("~/.local/share/icons/hicolor/scalable/apps/").expanduser()

# TODO: use platformdirs instead?
