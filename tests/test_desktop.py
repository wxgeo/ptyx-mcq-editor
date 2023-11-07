import tomllib
from pathlib import Path

from ptyx_mcq_editor.tools import SHELL_COMMAND, DESKTOP_FILE_NAME

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_desktop_shortcut():
    desktop_file = PROJECT_ROOT / "ressources" / DESKTOP_FILE_NAME
    content = desktop_file.read_text()
    assert f'\nExec="{SHELL_COMMAND}"' in content

    toml = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    assert SHELL_COMMAND in list(toml["tool"]["poetry"]["scripts"])
