import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import platformdirs

CONFIG_PATH = Path(platformdirs.user_config_path("mcq-editor") / "config.toml")
MAX_RECENT_FILES = 10


@dataclass
class Settings:
    _current_file: str = ""
    _recent_files: list[str] = field(default_factory=list)

    @property
    def recent_files(self) -> list[Path]:
        """Get the list of the recent files, starting from the more recent."""
        return [Path(file) for file in self._recent_files]

    @property
    def current_file(self) -> Path:
        return Path(self._current_file).resolve()

    @current_file.setter
    def current_file(self, value: Path | str) -> None:
        if self.current_file.is_file():
            try:
                # The same file must not appear twice in the list.
                # So, if it is already in the list, remove it,
                # and then insert it at the **first** position.
                self._recent_files.remove(self._current_file)
            except ValueError:
                pass
            # Store last current file in `recent_files`.
            self._recent_files.insert(0, self._current_file)
        if len(self._recent_files) > MAX_RECENT_FILES:
            # Remove the oldest.
            self._recent_files.pop()
        self._current_file = str(value)

    @property
    def current_dir(self) -> Path:
        if self.current_file.is_file():
            return self.current_file.parent
        else:
            for path in self.recent_files:
                if (directory := path.parent).is_dir():
                    return directory
        return Path().resolve()

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            "\n".join(f"{key}={val!r}" for (key, val) in vars(self).items()) + "\n", "utf8"
        )
        print(f"Config saved in {CONFIG_PATH}")

    @classmethod
    def load(cls) -> "Settings":
        try:
            settings = tomllib.loads(CONFIG_PATH.read_text("utf8"))
        except FileNotFoundError:
            settings = {}
        except OSError as e:
            settings = {}
            print(f"Enable to load settings: {e!r}")
        return cls(**settings)
