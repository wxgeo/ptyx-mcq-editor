import tempfile
from subprocess import CompletedProcess, run, PIPE, STDOUT
from pathlib import Path

SHELL_COMMAND = "mcq-editor"
DESKTOP_FILE_NAME = "ptyx-mcq-editor.desktop"


def install_desktop_shortcut() -> CompletedProcess[str]:
    desktop_file = Path(__file__).resolve().parent.parent / "ressources" / DESKTOP_FILE_NAME
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
