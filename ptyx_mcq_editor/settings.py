import tomllib
from dataclasses import dataclass, field
from enum import auto, Enum
from pathlib import Path
from typing import Iterator, Any

import platformdirs
from tomli_w import dumps

CONFIG_PATH = Path(platformdirs.user_config_path("mcq-editor") / "config.toml")
MAX_RECENT_FILES = 12


class DocumentHasNoPath(RuntimeError):
    """Error raised when trying to save document without setting a path."""


class SamePath(RuntimeError):
    """Error raised when trying to open an already opened document."""


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
        self._path = path.resolve() if path is not None else path
        self.__class__.all_docs[self.doc_id] = self

    def __str__(self):
        return f"<Document {self.doc_id}: {self.path} (saved: {self.is_saved})>"

    def __repr__(self):
        return str(self)

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
        return name if self.is_saved else "* " + name

    def rename(self, path: Path) -> None:
        """Rename the document.

        If the document is saved on disk, then the file will be effectively renamed.
        Else, only the path of the unsaved document will change.

        Raise `SamePath` error if the path matches any already opened document.
        """
        self._assert_unicity(path)
        if self.path is not None:
            # Rename the corresponding file.
            self.path.rename(path)
        # Update the document's path.
        self._path = path

    def _assert_unicity(self, path: Path) -> None:
        """Raise a `SamePath` error if the path matches an already opened document."""
        if any(path == doc.path for doc in self.__class__.all_docs.values() if doc is not self):
            raise SamePath("Can't save the document with the same path as an already opened one.")

    def write(self, content: str, path: Path = None, is_copy: bool = False) -> None:
        """Write provided document content on given path.

        Given path (if any) is stored for next time.
        If successful, set `is_saved` attribute to True, else an error is raised.

        If no path is provided and none has been given before, raise `DocumentHasNoPath` error.
        Any kind of `OSError` might also be raised, notably `FileNotFoundError` if path is invalid.

        If `is_copy` is `True`, the document path will not change.
        """
        if path is None:
            path = self._path
        else:
            # Two opened documents can't have the same path.
            self._assert_unicity(path)
            if not is_copy:
                self._path = path
        if path is None:
            raise DocumentHasNoPath("Can't save document, no path set.")
        with open(path, "w", encoding="utf8") as f:
            f.write(content)
        self._is_saved = True

    def on_close(self) -> None:
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
            return len(self) - 1
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

    def __getitem__(self, index: int) -> Document | None:
        return self.doc(index)

    @property
    def paths(self) -> list[Path]:
        return [doc.path for doc in self._documents if doc.path is not None]

    @property
    def resolved_paths(self) -> list[Path]:
        return [doc.path.resolve() for doc in self._documents if doc.path is not None]

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

    def add_doc(
        self, *, path: Path = None, doc: Document = None, select=True, position: int = None
    ) -> Document:
        """Open a new document, either an empty one or one corresponding to the given path.

        Set either a path, or a document, not both.

        Return the added document.
        """
        if path is None and doc is None:
            doc = Document()
        elif doc is not None:
            assert path is None
        elif path is not None:
            # Attention, paths must be resolved to don't miss duplicates (symlinks...)!
            if path.resolve() in self.resolved_paths:
                if select:
                    self._current_index = self.index(path)
                raise SamePath("I can't open the same file twice.")
            doc = Document(path)
        assert doc is not None
        if position is None:
            self._documents.append(doc)
        else:
            self._documents.insert(position, doc)
        if select:
            self._current_index = len(self._documents) - 1
        return doc

    def remove_doc(self, index: int) -> None:
        del self._documents[index]

    def index(self, path: Path) -> int:
        for i, doc in enumerate(self._documents):
            if doc.path is not None and doc.path.resolve() == path.resolve():
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
        doc.on_close()
        return doc.path

    def as_dict(self) -> dict[str, Any]:
        """Used for saving settings when closing application."""
        return {
            "current_index": self.current_index if self.current_index is not None else -1,
            "files": [str(path) for path in self.paths],
        }


@dataclass(kw_only=True)
class Settings:
    """The application current state.

    This includes:
    - tabs opened on
    - recent files
    """

    _left_docs: DocumentsCollection = field(default_factory=lambda: DocumentsCollection(_side=Side.LEFT))
    _right_docs: DocumentsCollection = field(default_factory=lambda: DocumentsCollection(_side=Side.RIGHT))
    _recent_files: list[Path] = field(default_factory=list)
    _current_side: Side = Side.LEFT
    _current_directory: Path | None = None

    @property
    def current_directory(self) -> Path:
        """Current directory, used for example when opening or saving a file.

        This is the folder containing the current file, if saved on disk.
        Else, it is last used directory.
        """
        if self.current_doc_path is None:
            return self._current_directory if self._current_directory is not None else Path.cwd()
        return self.current_doc_path.parent

    @current_directory.setter
    def current_directory(self, path: Path) -> None:
        self._current_directory = path

    @property
    def current_doc(self) -> Document | None:
        return self.docs(self._current_side).current_doc

    @property
    def current_doc_path(self) -> Path | None:
        return None if self.current_doc is None else self.current_doc.path

    # @property
    # def current_doc_directory(self) -> Path | None:
    #     return None if self.current_doc_path is None else self.current_doc_path.parent

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

    def open_doc(self, path: Path, side: Side):
        # Attention, paths must be resolved to don't miss duplicates (symlinks...)!
        if path.resolve() in self.docs(side).resolved_paths:
            # Don't open twice the same document.
            index = self.docs(side).index(path)
            self.docs(side).current_index = index
        elif path.resolve() in self.docs(~side).resolved_paths:
            index = self.docs(~side).index(path)
            self.move_doc(side, index, ~side)
            self.docs(~side).current_index = len(self.docs(~side)) - 1
        else:
            self.docs(side).add_doc(path=path)
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
            path for path in self._recent_files if path.resolve() != new_path.resolve() and path.is_file()
        ]
        if len(self._recent_files) > MAX_RECENT_FILES:
            self._recent_files.pop()

    def new_session(self):
        for side in Side:
            while len(self.docs(side)) > 0:
                self.close_doc(side, 0)

    @property
    def opened_files(self) -> frozenset[Path]:
        """Return the (frozen) set of the opened files.

        Result is recomputed each time, so it should be cached before being used in a loop.
        """
        return frozenset(path for side in Side for path in self.docs(side).paths)

    @property
    def recent_files(self) -> Iterator[Path]:
        """Return an iterator over the recent files, starting with the more recent one.

        The recent files list is updated first, removing invalid entries (deleted files).
        """
        # Update recent files list.
        opened_files = self.opened_files
        self._recent_files = [
            path for path in self._recent_files if path.is_file() and path not in opened_files
        ]

        return iter(self._recent_files)

    # @property
    # def current_doc_is_saved(self) -> bool:
    #     if self.current_doc is None:
    #         return True
    #     return self.current_doc.is_saved

    # @property
    # def current_doc_title(self) -> str:
    #     if self.current_doc is None:
    #         return ""
    #     return self.current_doc.title

    def _as_dict(self) -> dict[str, Any]:
        """Used for saving settings when closing application."""
        return {
            "current_side": self._current_side.name,
            "recent_files": [str(path) for path in self.recent_files],
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
                _documents=[Document(Path(path)) for path in data.get("files", []) if Path(path).is_file()],
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
    def load_settings(cls) -> "Settings":
        try:
            settings_dict = tomllib.loads(CONFIG_PATH.read_text("utf8"))
        except FileNotFoundError:
            settings_dict = {}
        except OSError as e:
            settings_dict = {}
            print(f"Enable to load settings: {e!r}")
        return cls._from_dict(settings_dict)
