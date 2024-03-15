import json
import re
import shutil
import subprocess
import tempfile
import traceback
from subprocess import CompletedProcess, run, PIPE, STDOUT
from pathlib import Path
from typing import Any

from ptyx.errors import ErrorInformation
from ptyx.extensions.extended_python import (
    parse_code_block,
    PYTHON_DELIMITER,
    parse_extended_python_code,
)
from ptyx.shell import red

SHELL_COMMAND = "mcq-editor"


RESSOURCES_PATH = Path(__file__).resolve().parent.parent / "ressources"
DESKTOP_FILE_NAME = "ptyx-mcq-editor.desktop"
ICON_NAME = "mcq-editor.svg"
ICON_DIR = Path("~/.local/share/icons/hicolor/scalable/apps/").expanduser()

# TODO: use platformdirs instead?


def install_desktop_shortcut() -> CompletedProcess[str]:
    icon_file = RESSOURCES_PATH / ICON_NAME
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(icon_file, ICON_DIR)

    desktop_file = RESSOURCES_PATH / DESKTOP_FILE_NAME
    # Using "mcq-editor" in Exec field does not work (probably because `mcq-editor` is in the $PATH
    # only for bash).
    # So, we have to replace it with its absolute path.
    # Another possibility would be to launch python3 with the appropriate python file,
    # but anyway, we would have to locate the correct version of python3 first, because it is
    # probably sandboxed inside a virtual environment.
    exec_command = run(["which", SHELL_COMMAND], capture_output=True, encoding="utf8").stdout.strip()
    content = desktop_file.read_text()
    assert f'\nExec="{SHELL_COMMAND}"' in content, f'Exec="{SHELL_COMMAND}" not found.'
    content = content.replace(f'\nExec="{SHELL_COMMAND}"', f'\nExec="{exec_command}"')
    assert f"\nIcon={ICON_NAME}" in content
    content = content.replace(f"\nIcon={ICON_NAME}", f"\nIcon={icon_file}")
    with tempfile.TemporaryDirectory() as tmp_dir:
        amended_desktop_file = Path(tmp_dir) / DESKTOP_FILE_NAME
        amended_desktop_file.write_text(content)
        completed_process = run(
            ["xdg-desktop-menu", "install", str(amended_desktop_file)],
            stdout=PIPE,
            stderr=STDOUT,
            encoding="utf8",
            errors="replace",
        )
    return completed_process


def ruff_check(code: str, select="E999,E101,F", ignore="F821") -> list[dict[str, Any]]:
    # https://github.com/astral-sh/ruff/issues/8401#issuecomment-1788806462

    # Checker example
    proc = subprocess.run(
        ["ruff", "check", f"--select={select}", f"--ignore={ignore}", "--output-format=json", "-"],
        input=code,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding="utf-8",
    )
    # proc.returncode  # <- 1 if bad
    output = proc.stdout
    try:
        js = json.loads(output)
    except json.JSONDecodeError as e:
        print(red("Error: invalid ruff output."))
        print("--------------")
        print(" Ruff output: ")
        print("==============")
        print(proc.stdout)
        print("--------------")
        traceback.print_exception(e)
        js = {}
    return js


def check_each_python_block(code: str) -> list[ErrorInformation]:
    lines: list[str] = []
    inside_python_block = False
    errors: list[ErrorInformation] = []
    start = 0
    for i, line in enumerate(code.split("\n")):
        if re.match(PYTHON_DELIMITER, line):
            inside_python_block = not inside_python_block
            if inside_python_block:
                start = i
            else:
                # Leaving a python block
                code = "\n".join(lines)
                errors.extend(
                    ErrorInformation(
                        f"<{d['code']}> {d['message']}",
                        start + d["location"]["row"],
                        start + d["end_location"]["row"],
                        d["location"]["column"],
                        d["end_location"]["column"],
                    )
                    for d in ruff_check(parse_extended_python_code(code))
                )
                lines.clear()
        elif inside_python_block:
            lines.append(line)
    return errors


def ruff_formater(code: str) -> str:
    """Format code using ruff."""
    return subprocess.check_output(["ruff", "format", "-"], input=code, encoding="utf-8")


def extended_python_ruff_formater(code: str) -> str:
    """Format code using ruff.

    Support `let` directives, as defined in ptyx.extended_python plugin.
    """
    RAND_VARNAME = "rNTucrSob8Yqlb68syg066XeWxYZ8H"
    store: list[str] = []

    def extract_let_directives(m: re.Match) -> str:
        let_dir = m.group(2)
        let_dir = re.sub(" +", " ", let_dir)
        let_dir = re.sub(" ?, ?", ", ", let_dir)
        store.append(let_dir)
        return m.group(1) + RAND_VARNAME

    code = re.sub("^( *)(let .+)$", extract_let_directives, code, flags=re.MULTILINE)

    try:
        code = ruff_formater(code)
    except Exception as e:
        print(e)

    def restore_let_directives(m: re.Match) -> str:
        return m.group(1) + store.pop(0)

    code = re.sub(f"^( *){RAND_VARNAME}$", restore_let_directives, code, flags=re.MULTILINE)
    return code


def format_each_python_block(code: str) -> str:
    """For each python code block in the document, apply ruff formatting."""
    delimiter = 12 * "."

    def parser(start: str, end: str, content: str) -> str:
        content = extended_python_ruff_formater(content)
        return "".join([delimiter, "" if content.startswith("\n") else "\n", content, delimiter])

    return parse_code_block(code, parser)
