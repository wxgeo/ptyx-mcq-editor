import shutil
import subprocess
from pathlib import Path

terminal_emulators: list[str] = [
    "x-terminal-emulator",
    "gnome-terminal",
    "konsole",
    "xfce4-terminal",
    "lxterminal",
    "alacritty",
    "terminator",
    "tilix",
    "xterm",
    "urxvt",
    "eterm",
    "kitty",
    "hyper",
    "guake",
    "yakuake",
    "io.elementary.terminal",
    "deepin-terminal",
]


def _parse_path(current_working_directory: Path) -> Path:
    if current_working_directory.is_file():
        current_working_directory = current_working_directory.parent
    if not current_working_directory.is_dir():
        raise ValueError(f"The path `{current_working_directory}` is not a directory.")
    return current_working_directory


def detect_terminal() -> str | None:
    """Return a terminal emulator command for this Linux distribution."""
    for emulator in terminal_emulators:
        if shutil.which(emulator):  # Checks if the command exists in the system PATH
            return emulator
    return None


def launch_terminal(current_working_directory: Path) -> None:
    """
    Launches a terminal in the specified directory.

    Args:
        current_working_directory (Path): The working directory of the terminal.
    """
    terminal = detect_terminal()
    if terminal is None:
        print("No terminal emulator found.")
    else:
        print(f"Launching `{terminal}`...")
        try:
            subprocess.Popen([terminal], cwd=_parse_path(current_working_directory))
        except Exception as e:
            print(f"Failed to launch terminal emulator `{terminal}`: {e}")


def detect_navigator() -> str | None:
    try:
        result = subprocess.run(
            ["xdg-mime", "query", "default", "inode/directory"], capture_output=True, text=True, check=True
        )
        desktop_file = Path(result.stdout.strip())
        if desktop_file.suffix == ".desktop":
            return desktop_file.stem
    except Exception as e:
        print(f"Error detecting default navigator: {e}")
    return None


def launch_navigator(current_working_directory: Path) -> None:
    """
    Launches the default file navigator using xdg-open in the specified directory.

    Args:
        current_working_directory (Path): The directory to open in the file navigator.
    """
    try:
        navigator = detect_navigator()
        if navigator is None:
            print("No default navigator found.")
        else:
            current_working_directory = _parse_path(current_working_directory)
            # Use xdg-open to launch the navigator
            subprocess.Popen(["xdg-open", str(current_working_directory)])
            print(f"Navigator {navigator} launched for `{current_working_directory}`")
    except Exception as e:
        print(f"Failed to launch navigator: {e}")
