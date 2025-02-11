import json
import re
import subprocess
import traceback
from typing import Any

from ptyx.errors import ErrorInformation
from ptyx.extensions.extended_python import (
    PYTHON_DELIMITER,
    parse_code_block,
    parse_extended_python_line,
)

from ptyx.shell import red


def ruff_check(code: str, select="E101,F", ignore="F821") -> list[dict[str, Any]]:
    # https://github.com/astral-sh/ruff/issues/8401#issuecomment-1788806462

    # Checker example
    proc = subprocess.run(
        ["ruff", "check", f"--select={select}", f"--ignore={ignore}", "--output-format=json", "-"],
        input=code,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,  # remove this for debugging!
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
                    for d in ruff_check(code)
                )
                lines.clear()
        elif inside_python_block:
            try:
                line = parse_extended_python_line(line)
            except SyntaxError as e:
                errors.append(ErrorInformation(e.msg, row=start + i))
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
