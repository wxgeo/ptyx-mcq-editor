import tomllib
from dataclasses import dataclass, field
from enum import auto, Enum
from pathlib import Path
from typing import Iterator, Any

import platformdirs
from tomli_w import dumps

CONFIG_PATH = Path(platformdirs.user_config_path("mcq-editor") / "config.toml")
MAX_RECENT_FILES = 10


class DocumentHasNoPath(RuntimeError):
    """Error raised when trying to save document without setting a path."""


class SamePath(RuntimeError):
    """Error raised when trying to open an already opened document."""


# class Display(Flag):
#     NONE = 0
#     LEFT = auto()
#     RIGHT = auto()


class Side(Enum):
    """Enum used to indicate the two sides of the editor splitter.

    To get the opposite side, use `~` operator:
        >>> side = Side.LEFT
        >>> ~side
        Side.RIGHT
    """

    LEFT = auto()
    RIGHT = auto()

    def __invert__(self) -> "Side":
        return Side.RIGHT if self == Side.LEFT else Side.LEFT


# TODO: Support opening the same file on left and right sides simultaneously.
#  Currently, we prevent the same file from being edited twice.


class Document:
    all_docs: dict[int, "Document"] = {}
    _id_counter = 0

    def __init__(self, path: Path | None = None):
        self.__class__._id_counter += 1
        self._doc_id = self._id_counter
        self._is_saved = True
        self._path = path
        self.__class__.all_docs[self.doc_id] = self

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def doc_id(self) -> int:
        return self._doc_id

    @property
    def is_saved(self) -> bool:
        return self._is_saved and (self.path is None or self.path.is_file())

    @is_saved.setter
    def is_saved(self, value: bool):
        self._is_saved = value

    @property
    def title(self) -> str:
        name = self.path.name if self.path is not None else f"New document {self.doc_id}"
        return name if self.is_saved else name + " *"

    def write(self, content: str, path: Path = None) -> None:
        """Write provided document content on given path.

        Given path (if any) is stored for next time.
        If successful, set `is_saved` attribute to True, else an error is raised.

        If no path is provided and none has been given before, raise `DocumentHasNoPath` error.
        Any kind of `OSError` might also be raised, notably `FileNotFoundError` if path is invalid.
        """
        if path is None:
            path = self._path
        else:
            # Two opened documents can't have the same path.
            if any(path == doc.path for doc in self.__class__.all_docs.values()):
                raise SamePath("Can't save the document with the same path as an already opened one.")
            self._path = path
        if path is None:
            raise DocumentHasNoPath("Can't save document, no path set.")
        with open(path, "w", encoding="utf8") as f:
            f.write(content)
        self._is_saved = True

    def destroy(self) -> None:
        self.__class__.all_docs.pop(self.doc_id)


@dataclass
class DocumentsCollection:
    """A collection of opened documents.

    This represents the currently opened documents, either on the left side or the right side of the editor.


    """

    _side: Side
    _documents: list[Document] = field(default_factory=list)
    _current_index: int | None = None

    @property
    def current_index(self) -> int | None:
        """Return index of current document, or None if there is no current document."""
        if self._current_index is None or len(self) == 0:
            return None
        elif self._current_index >= len(self):
            len(self) - 1
        return self._current_index

    @current_index.setter
    def current_index(self, index: int):
        """Set the current document."""
        # if not 0 <= index < len(self._documents):
        #     raise IndexError(f"Invalid document index: {index}. (Number of documents: {len(self)}).")
        self._current_index = index

    @property
    def documents(self) -> Iterator[Document]:
        return iter(self._documents)

    def __len__(self) -> int:
        return len(self._documents)

    def __iter__(self) -> Iterator[Document]:
        return iter(self._documents)

    @property
    def paths(self) -> list[Path]:
        return [doc.path for doc in self._documents if doc.path is not None]

    @property
    def current_doc(self) -> Document | None:
        if self.current_index is None:
            return None
        return self._documents[self.current_index]

    def doc(self, index: int = None) -> Document | None:
        """Return current document if `index` is None, else the doc corresponding to the given index.

        Return `None` if `index` is an invalid integer.
        Note that current document may also be `None`.
        """
        if index is None:
            return self.current_doc
        try:
            print(f"Requesting document {index!r} (max={len(self._documents) - 1}) of side {self._side}.")
            return self._documents[index]
        except IndexError:
            return None

    def add_doc(self, *, path: Path = None, doc: Document = None, select=True) -> Document:
        """Open a new document, either an empty one or one corresponding to the given path.

        Set either a path, or a document, not both.

        Return the added document.
        """
        if path is None and doc is None:
            self._documents.append(doc := Document())
        elif doc is not None:
            assert path is None
            self._documents.append(doc)
        elif path is not None:
            if path in self.paths:
                raise SamePath("I can't open the same file twice.")
            self._documents.append(doc := Document(path))
        if select:
            self._current_index = len(self._documents) - 1
        assert doc is not None
        return doc

    def remove_doc(self, index: int) -> None:
        del self._documents[index]

    def index(self, path: Path) -> int:
        for i, doc in enumerate(self._documents):
            if doc.path == path:
                return i
        raise IndexError(f"No document matching path '{path}'.")

    def move_doc(self, old_index: int, new_index: int, select=True) -> None:
        self._documents.insert(new_index, self._documents.pop(old_index))
        if select:
            self.current_index = new_index

    def pop_doc(self, index: int) -> Document:
        return self._documents.pop(index)

    def insert_doc(self, index: int, doc: Document) -> None:
        self._documents.insert(index, doc)

    def close_doc(self, index: int | None) -> Path | None:
        if index is None:
            index = self.current_index
            if index is None:
                return None
        doc = self.pop_doc(index)
        doc.destroy()
        return doc.path

    def as_dict(self) -> dict[str, Any]:
        """Used for saving settings when closing application."""
        return {
            "current_index": self.current_index if self.current_index is not None else -1,
            "files": self.paths,
        }


@dataclass(kw_only=True)
class Settings:
    """The application current state.

    This includes:
    - tabs opened on
    - recent files
    """

    _left_docs: DocumentsCollection
    _right_docs: DocumentsCollection
    _recent_files: list[Path] = field(default_factory=list)
    _current_side: Side = Side.LEFT
    _current_directory: Path | None = None

    # @property
    # def left_docs(self):
    #     return self._left_docs
    #
    # @property
    # def right_docs(self):
    #     return self._right_docs

    @property
    def current_directory(self) -> Path:
        if self.current_doc is None or self.current_doc.path is None:
            return self._current_directory if self._current_directory is not None else Path.cwd()
        return self.current_doc.path.parent

    @current_directory.setter
    def current_directory(self, path: Path) -> None:
        self._current_directory = path

    @property
    def current_side(self) -> Side:
        return self._current_side

    def docs(self, side: Side = None) -> DocumentsCollection:
        """Get the documents of the left side or the right side."""
        if side is None:
            side = self.current_side
        if side == Side.LEFT:
            return self._left_docs
        elif side == Side.RIGHT:
            return self._right_docs
        else:
            raise ValueError(f"`side` value must be either `Side.LEFT` or `Side.RIGHT`, not {side!r}.")

    def new_doc(self, side: Side = None) -> Document:
        if side is None:
            side = self.current_side
        return self.docs(side).add_doc()

    def move_doc(
        self, old_side: Side, old_index: int, new_side: Side = None, new_index: int = None, select=True
    ) -> None:
        if new_side is None or old_side == new_side:
            if new_index is not None:
                self.docs(old_side).move_doc(old_index, new_index, select=select)
        else:
            doc = self.docs(old_side).pop_doc(old_index)
            if new_index is None:
                self.docs(new_side).add_doc(doc=doc, select=select)
            else:
                self.docs(new_side).insert_doc(new_index, doc)
                if select:
                    self.docs(new_side).current_index = new_index

    def invert_sides(self) -> None:
        """Put all the documents of the left side to the right side, and reciprocally."""
        self._left_docs, self._right_docs = self._right_docs, self._left_docs
        self._left_docs._side = Side.LEFT
        self._right_docs._side = Side.RIGHT
        self._current_side = ~self._current_side

    def open_doc(self, path: Path, side: Side) -> None:
        if path in self.docs(side).paths:
            # Don't open twice the same document.
            index = self.docs(side).index(path)
            self.docs(side).current_index = index
        elif path in self.docs(~side).paths:
            index = self.docs(~side).index(path)
            self.move_doc(side, index, ~side)
            self.docs(~side).current_index = len(self.docs(~side)) - 1
        self._current_side = side

    def close_doc(self, side: Side = None, index: int = None) -> Path | None:
        if side is None:
            side = self._current_side
        path = self.docs(side).close_doc(index)
        if path is not None and path.is_file():
            self._remember_file(path)
        return path

    def _remember_file(self, new_path: Path) -> None:
        # The same file must not appear twice in the list.
        self._recent_files = [new_path] + [
            path for path in self._recent_files if path != new_path and path.is_file()
        ]
        if len(self._recent_files) > MAX_RECENT_FILES:
            self._recent_files.pop()

    @property
    def recent_files(self) -> Iterator[Path]:
        """Iterate over the recent files, starting with the more recent one."""
        return iter(path for path in self._recent_files if path.is_file())

    @property
    def current_doc(self) -> Document | None:
        return self.docs(self._current_side).current_doc

    @property
    def current_doc_is_saved(self) -> bool:
        if self.current_doc is None:
            return True
        return self.current_doc.is_saved

    # @property
    # def current_doc_title(self) -> str:
    #     if self.current_doc is None:
    #         return ""
    #     return self.current_doc.title

    def _as_dict(self) -> dict[str, Any]:
        """Used for saving settings when closing application."""
        return {
            "current_side": self._current_side.name,
            "recent_files": list(self.recent_files),
            "docs": {"left": self._left_docs.as_dict(), "right": self._right_docs.as_dict()},
            "current_directory": str(self.current_directory),
        }

    @classmethod
    def _from_dict(cls, d: dict[str, Any]) -> "Settings":
        recent_files = [Path(s) for s in d.get("recent_files", [])]
        current_side = getattr(Side, d.get("current_side", "LEFT"), Side.LEFT)
        current_directory = Path(d.get("current_directory", Path.cwd()))
        docs = {
            side: DocumentsCollection(
                _side=side,
                _documents=[Document(Path(path)) for path in data.get("files", [])],
                _current_index=data.get("current_index", 0),
            )
            for (side, data) in d.get("docs", {}).items()
        }
        return Settings(
            _recent_files=recent_files,
            _current_side=current_side,
            _left_docs=docs.get("left", DocumentsCollection(Side.LEFT)),
            _right_docs=docs.get("right", DocumentsCollection(Side.RIGHT)),
            _current_directory=current_directory,
        )

    def save_settings(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        settings_data = self._as_dict()
        toml = dumps(settings_data)
        assert tomllib.loads(toml) == settings_data
        CONFIG_PATH.write_text(toml, "utf8")
        print(f"Config saved in {CONFIG_PATH}")

    @classmethod
    def load_settings(
        cls,
    ) -> "Settings":
        try:
            settings = tomllib.loads(CONFIG_PATH.read_text("utf8"))
        except FileNotFoundError:
            settings = {}
        except OSError as e:
            settings = {}
            print(f"Enable to load settings: {e!r}")
        return cls._from_dict(settings)
