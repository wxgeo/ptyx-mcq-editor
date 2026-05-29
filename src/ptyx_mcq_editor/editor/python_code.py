"""
In an opened pTyX file, the Python code blocks are stored as a list of lists of PythonCodeBlock instances.

The structure is the following:
- Each item of the main list represent a new context.
  Currently, a new context is generated each time the keyword `OR` is found alone in a new line.
  It is used to declare an alternative version of the same exercise.
- Each inner list (the new context) contains PythonCodeBlock instances.
- Each PythonCodeBlock instance stores the position of a Python code block.

This list is synchronized each time the editor lexer is called, so at every text changed event.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, NewType

from ptyx.extensions.extended_python import parse_extended_python_code

if TYPE_CHECKING:
    from ptyx_mcq_editor.editor.editor_widget import EditorWidget

ContextNum = NewType("ContextNum", int)


class BlockType(Enum):
    BLOCK = auto()
    EXPRESSION = auto()


class AllPythonContent:
    def __init__(self, editor: "EditorWidget"):
        self.editor = editor
        # Store the position of the Python code blocks.
        self._content: list[list[PythonCodeBlock]] = [[]]
        # Memorize the start of each context (unused for now).
        self._context_start: list[int] = []
        # Create a cache for the gathered Python code.
        self._cache: dict[int, str] = {}

    def new_context(self, position: int) -> None:
        self._content.append([])
        self._context_start.append(position)

    def add_code_block(self, block_type: BlockType, start: int, end: int) -> None:
        """
        Add a new code block.

        Beware of adding code blocks in the right order, since they are supposed ordered in all algorithms!
        """
        context = self._content[-1]

        assert start <= end, (start, end)
        # Blocks must be ordered !
        assert not context or context[-1].end < start, (context, start, end)

        context.append(PythonCodeBlock(block_type, start, end))

    def is_inside_python_block(self, position: int) -> bool:
        """Test whether the given position is inside a python block code."""
        return self._context_num(position) is not None

    def _context_num(self, position: int) -> ContextNum | None:
        """Return the current context number, if the position is inside a python block, else `None`."""
        match self._find_block(position):
            case context_num, _:
                assert isinstance(context_num, int), context_num
                return context_num
        return None

    def _find_block(self, position: int) -> tuple[ContextNum, "PythonCodeBlock"] | None:
        """
        Return the current context number and the current block, if the position is in a Python block, else `None`.
        """
        for i, context in enumerate(self._content):
            # Blocks are supposed ordered.
            for block in context:
                if block.start <= position <= block.end:
                    return ContextNum(i), block
        return None

    def _current_raw_python_code(self, context_num: ContextNum) -> str:
        """
        Return the raw Python code of the given context.

        Note that this code may contain unparsed "extended python" directives, which are not valid Python code.
        If you need valid Python code, you should use `AllPythonContent.current_python_code()` instead.

        :param line: line of the file (starting from 0)
        :param col: column in the file (idem)
        :return: raw Python code or `None`
        """
        text = self.editor.text().encode("utf8")
        return b"".join(text[block.start : block.end] for block in self._content[context_num]).decode("utf8")

    def python_code(self, context_num: ContextNum) -> str:
        try:
            python_code = self._cache[context_num]
        except KeyError:
            python_code = parse_extended_python_code(self._current_raw_python_code(context_num))
            self._cache[context_num] = python_code
        return python_code

    def current_python_code(self, line: int, col: int) -> str | None:
        """
        Return the parsed Python code of the current context.

        Return the Python code as a string, if the given position is inside a Python block, or `None` else.

        Note that they may be several Python context in the same document,
        notably when alternative versions of the same MCQ document are declared through the keyword `OR`.
        Only the code of the context of the given position will be returned.

        The result is cached. The method `.invalidate_cache()` must be called each time the code is parsed again
        by the lexer to clear the cache.

        Extended python directives are parsed and converted to valid Python code.

        :param line: line number (starting from 0)
        :param col: column number (idem)
        :return: parsed Python code or `None`
        """
        position = self.editor.positionFromLineIndex(line, col)
        context_num = self._context_num(position)
        return None if context_num is None else self.python_code(context_num)

    def is_extended_python(self, line: int) -> bool:
        """
        Test whether it is a line of 'extended python' code.

        Python syntax is extended with the keyword `let` (cf. the extended_python ptyx extension).
        A line starting with "let " must not be autocompleted, since it does not follow Python syntax.
        """
        return self.editor.text(line).startswith("let ")

    def invalidate_cache(self) -> None:
        self._cache.clear()

    def _string_length(self, start: int, end: int) -> int:
        """Return the string length (number of characters), given the start and end positions in bytes."""
        return len(self.editor.text().encode("utf8")[start:end].decode("utf8"))

    def virtual_position(self, line: int, col: int) -> tuple[int, int] | None:
        """
        Convert the real position in the editor to a virtual one inside the gathered Python code.

        :param line: line number (starting from 0)
        :param col: column number (idem)
        :return: virtual position (line, column),  or `None`
        """
        # Qscintilla position (in bytes)
        position = self.editor.positionFromLineIndex(line, col)
        context_num = self._context_num(position)
        if context_num is None:
            return None

        context = self._content[context_num]
        virtual_position = 0
        # Blocks are supposed ordered.
        for block in context:
            if block.end < position:
                # Add the number of characters (and not the number of bytes!)
                virtual_position += block.end - block.start
            elif block.start <= position <= block.end:
                return self.position_to_line_col(
                    self.python_code(context_num), virtual_position + position - block.start
                )
        return None

    @staticmethod
    def position_to_line_col(text: str, pos: int) -> tuple[int, int]:
        """
        Convert the position in bytes to a (line, col) tuple indicating the position in the string.

        QScintilla uses the combination of a line number and a character index from the start of that line to specify
        the position of a character within the text. The underlying Scintilla instead uses a byte index from the start
        of the text. This will convert the position byte index to the line number and character index.

        :param text: text
        :param pos: position in bytes
        :return: (line, column)
        """
        prefix = text.encode("utf8")[:pos].decode("utf8")
        line = prefix.count("\n")
        col = len(prefix) - prefix.rfind("\n") - 1
        return line, col


@dataclass
class PythonCodeBlock:
    """
    Represent a block of Python code, stored as chunks of code, as detected by the lexer.

    The position of this block of code in the editor is remembered using `start` and `end`.

    This refers to the position as used internally by Scintilla, so a number of bytes, and not of characters.
    The code itself can be get using:

        ```
        editor.text().encode("utf8")[start:end].decode("utf8")
        ```

    """

    type: BlockType
    start: int
    end: int

    # def __len__(self) -> int:
    #     return self.end - self.start
