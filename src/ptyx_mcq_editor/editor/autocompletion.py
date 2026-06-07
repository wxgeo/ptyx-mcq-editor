"""
Implement autocompletion in the editor.
"""

import builtins
import textwrap
from typing import TYPE_CHECKING

import jedi  # type: ignore[import-untyped]
from jedi.api.classes import Name  # type: ignore[import-untyped]
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, QPoint, QObject, QEvent
from PyQt6.Qsci import QsciScintilla, QsciAPIs
import traceback

from ptyx_mcq.make.extend_latex_generator import MCQLatexGenerator

from ptyx.latex_generator import LatexGenerator

from ptyx_mcq import PTYX_MCQ_TAGS

from ptyx_mcq_editor.param import RESSOURCES_PATH
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

from ptyx.pretty_print import print_warning
from ptyx_mcq_editor.widgets.permanent_tooltip import Tooltip

if TYPE_CHECKING:
    from ptyx_mcq_editor.editor.editor_widget import EditorWidget

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent

from ptyx.context import GLOBAL_CONTEXT
from ptyx.syntax_tree import SyntaxTreeGenerator, TagDict

_LATEX_COMMANDS_FILE = RESSOURCES_PATH / "latex_commands.txt"
LATEX_COMMANDS = sorted(
    line for _line in _LATEX_COMMANDS_FILE.read_text("utf8").split("\n") if (line := _line.strip())
)
NAME_SPACES = [GLOBAL_CONTEXT, vars(builtins)]


def _generate_commands_from_ptyx_tags(ptyx_tags: TagDict) -> list[str]:
    """
    Use pTyX tags syntax definition to generate a list of commands for autocompletion.

    :param ptyx_tags: a dictionary specifying each tag syntax, see `ptyx` package for an example.
    :return: a list of commands for autocompletion.
    """
    commands: set[str] = set()
    for tag in sorted(ptyx_tags):
        command_parts = ["#", tag]
        _python_args, _other_args, closing_tags = ptyx_tags[tag]
        n_args = _python_args + _other_args
        if closing_tags is None:
            closing_tags = []
        else:
            closing_tags = [tag for _tag in closing_tags if (tag := _tag.lstrip("@")) != "END"]
            commands.update("#" + tag for tag in closing_tags if tag not in ptyx_tags)
        if n_args >= 1:
            command_parts.append("{%M}")
            command_parts.append((n_args - 1) * "{}")
        if len(closing_tags) == 1:
            command_parts.append("%M" if n_args == 0 else "")
            command_parts.append("#" + closing_tags[0])
        commands.add("".join(command_parts))
    # print(commands)
    return sorted(commands)


PTYX_COMMANDS = _generate_commands_from_ptyx_tags(SyntaxTreeGenerator.tags)
PTYX_MCQ_COMMANDS = _generate_commands_from_ptyx_tags(PTYX_MCQ_TAGS)


def generate_python_help_message(results: list[Name], definitions: list[Name]) -> str:
    formatter = HtmlFormatter(nowrap=True, style="default")
    css = formatter.get_style_defs()
    lexer = PythonLexer()
    if not definitions:
        return ""
    result = results[0] if results else None
    definition = definitions[0]
    try:
        raw_signature = result.get_signatures()[0].to_string() if result else ""
    except IndexError:
        raw_signature = ""

    category: tuple[str, str] = (result.type if result else "", definition.type)
    if category[0] == "function":
        parent = definition.parent()
        if parent and parent.type == "class":
            category = ("function", "method")
    print(category)

    title = ""
    module = ""
    signature = ""
    docstring = result.docstring(raw=True) if result else ""
    print("DOCSTRING:", docstring)
    match category:
        case "function", "function":
            title = f"Function <b>{definition.name}</b>"
            module = definition.parent().full_name
            print(definitions)
            signature = "def " + raw_signature
        case "function", "method":
            title = f"Method <b>{definition.name}</b> of class <b>{definition.parent().name}</b>"
            module = definition.parent().parent().full_name
            signature = "def " + raw_signature
        case "class", "class":
            title = f"Class <b>{definition.name}</b>"
            signature = "class " + raw_signature
            module = definition.parent().full_name
        case "instance", "property":
            title = f"Property <b>{definition.name}</b> of class <b>{definition.parent().name}</b>"
            module = definition.parent().parent().full_name
            signature = "@property\ndef " + raw_signature
            docstring = definition.docstring(raw=True) if result else ""
        case "instance", _:
            _possible_types = "|".join(f"<i>{result.name}</i>" for result in results)
            title = f"Instance <b>{definition.name}</b>: {_possible_types}"
        case _, "param":
            title = f"param <b>{definition.name}</b>"
            signature = definition.description[6:]
        case "module", "module":
            title = f"module <b>{definition.full_name}</b>"
        case _:
            print_warning(f"Unknown category: {category}")

    horizontal_separator = '<hr style="border:none;border-top:1px solid #ccc;margin:4px 0;">'

    docstring = docstring.strip().replace("\n", "<br>") if docstring else "<i>no documentation</i>"

    html = [f"<style>{css}</style>"]
    if title:
        html.append(f"<div style='margin-bottom: 5px'>{title}</div>")
    if module:
        html.append(f"<div style='margin-bottom: 5px'><i>Module: {module}</i></div>")
    if signature:
        signature = highlight(signature, lexer, formatter).strip().replace("\n", "<br>")
        html.append(f"<div style='background-color: #ffeac2'><code>{signature}</code></div>")
    html.append(horizontal_separator)
    html.append(docstring)

    return "\n".join(html)


def generate_ptyx_help_message(tag: str) -> str:
    name = f"_parse_{tag}_tag"
    try:
        doc = getattr(LatexGenerator, name).__docstring__
    except AttributeError:
        try:
            doc = getattr(MCQLatexGenerator, name).__docstring__
        except AttributeError:
            doc = "<i>no documentation</i>"
    title = f"<div><b>#{tag}</b></div>"
    return title + '<hr style="border:none;border-top:1px solid #ccc;margin:4px 0;">' + f"<div>{doc}</div>"


def _get_potential_command_stem(line_prefix: str) -> str:
    """
    Search for what looks like the stem of a potential LaTeX or pTyX command at the end of the given string.

    If there is nothing like that, return an empty string else.

    The test is very simple: any # or \\ character is detected as the start of a potential command, whatever follows.

    :param line_prefix: the part of the line of text that precede the cursor.
    :return: the start of the current LaTeX or pTyX command, including \\ or #.
    """
    i = max(line_prefix.rfind(char) for char in ("\\", "#"))

    return line_prefix[i:] if i != -1 else ""


class Worker(QThread):
    """
    Runs jedi in a background thread to avoid blocking the UI.

    Abstract class.
    """

    ready = pyqtSignal(list)  # list[str]
    error = pyqtSignal(str)  # carries the traceback

    def __init__(self, source: str, line: int, column: int):
        super().__init__()
        self.source = source
        self.line = line
        self.column = column

    def run(self):
        raise NotImplementedError


class CompletionWorker(Worker):
    """
    Helper class to analyze Python code and suggest autocompletion.

    Runs jedi in a background thread to avoid blocking the UI.
    """

    def run(self):
        # noinspection PyBroadException
        try:
            script = jedi.Interpreter(self.source, NAME_SPACES)
            completions = script.complete(self.line, self.column)
            names = [c.name for c in completions]
            if names:
                self.ready.emit(names)
        except Exception:
            self.error.emit(traceback.format_exc())


class SignatureWorker(Worker):
    """
    Helper class to analyze Python code and suggest signature's autocompletion.

    Runs jedi in a background thread to avoid blocking the UI.
    """

    def run(self):
        # noinspection PyBroadException
        try:
            script = jedi.Interpreter(self.source, NAME_SPACES)
            signatures = script.get_signatures(self.line, self.column)
            if not signatures:
                return
            self.ready.emit([signatures[0].to_string()])
        except Exception:
            self.error.emit(traceback.format_exc())


class AutoCompleter(QObject):
    """
    Attach to a QsciScintilla editor.
    Provides dynamic, jedi-powered Python completion inside Python blocks
    of current pTyX file.
    Some basic completion is also provided for LaTeX and pTyX code.

    Usage:
        self.completer = AutoCompleter(self.editor)
    """

    def __init__(self, editor: "EditorWidget", minimal_char_count=1):
        super().__init__(editor)
        self.editor = editor
        self.minimal_char_count = minimal_char_count
        self._worker: Worker | None = None
        self._apis: QsciAPIs | None = None
        # Last char and last word before the cursor.
        self._last_char = ""
        self._current_word = ""
        self._current_pos = 0
        self._command_stem = ""
        # Use a timer to avoid calling autocompletion when the user is still writing.
        # Every time the user modifies the text, the timer will be reset.
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)  # ms after typing stops
        self._debounce.timeout.connect(self._trigger_completion)

        self._setup_scintilla()
        # Use char-added event, and not text-changed one: text-changed event is also fired
        # without user intervention, for example when a file is loaded in the editor.
        # This triggered Segmentation Faults sometimes.
        editor.SCN_CHARADDED.connect(self._on_char_added)
        editor.SCN_AUTOCSELECTION.connect(self._on_completion_selected)
        editor.SCN_DOUBLECLICK.connect(self._on_double_click)
        self.tooltip = Tooltip(editor)

    def _setup_scintilla(self) -> None:
        ed = self.editor

        # Use Python lexer for syntax highlighting (you may already have this)
        # If your editor uses a custom lexer, skip or adapt this block.

        # Autocompletion settings
        ed.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAPIs)
        ed.setAutoCompletionThreshold(self.minimal_char_count)  # show after 1 char
        ed.setAutoCompletionCaseSensitivity(True)
        ed.setAutoCompletionReplaceWord(False)
        ed.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)

        view_port = ed.viewport()
        if view_port is not None:
            view_port.installEventFilter(self)

        # If you already have a lexer attached:
        lexer = ed.lexer()
        if lexer:
            self._apis = QsciAPIs(lexer)
            self._apis.prepare()

    def _get_current_word_range(self) -> tuple[int, int]:
        pos = self.editor.SendScintilla(QsciScintilla.SCI_GETCURRENTPOS)
        start = self.editor.SendScintilla(QsciScintilla.SCI_WORDSTARTPOSITION, pos, True)
        end = self.editor.SendScintilla(QsciScintilla.SCI_WORDENDPOSITION, pos, True)
        return start, end

    def _get_current_word(self) -> str:
        start, end = self._get_current_word_range()
        return self.editor.text().encode("utf8")[start:end].decode("utf8")

    def _on_char_added(self):
        self._debounce.start()
        self.tooltip.hide()

    def eventFilter(self, watched, event) -> bool:
        if isinstance(event, QMouseEvent):
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.tooltip.hide()
                    line, col = self.editor.getCursorPosition()
                    if not self.editor.is_python_block_code(line, col):
                        self.editor.cancelList()
        return False  # always let the event through

    def _on_double_click(self, position: int, line: int, modifiers: int) -> None:
        # The word is already selected by Scintilla's default handler.
        # We just reuse the same logic as F1, no need to duplicate it.
        self.trigger_help()
        print("Double-click!")

    def _on_completion_selected(self, selection_in_bytes: bytes, position: int) -> None:
        """Customize autocompletion, when a suggestion is selected."""
        # IMPORTANT: Newlines must be replaced before `selection_in_bytes.find(b"%M")` is called.
        # Else, it would return an incorrect value, since we are replacing two bytes (%N) with only one (\n).
        selection_in_bytes = selection_in_bytes.replace(b"%N", b"\n")
        selection = selection_in_bytes.decode("utf8")
        shift = len(self._command_stem)
        if "%M" in selection or "%N" in selection:
            self.editor.SendScintilla(QsciScintilla.SCI_AUTOCCANCEL)
            selection = selection[shift:]
            position_shift = selection_in_bytes.find(b"%M")
            selection = selection.replace("%M", "")
            if position_shift == -1:
                position_shift = len(selection_in_bytes)
            line, col = self.editor.lineIndexFromPosition(position)
            self.editor.insertAndEdit(selection, line, col + shift)
            self.editor.SendScintilla(QsciScintilla.SCI_GOTOPOS, position + position_shift)

    def _trigger_completion(self) -> None:
        """Open a pop-up with autocompletion suggestions, if relevant, based on the cursor position."""
        line, col = self.editor.getCursorPosition()
        self._last_char = self.editor.text(line)[col - 1 : col]

        if self.editor.python_content.is_inside_python_block():
            # We are inside a Python code block.
            if self.editor.python_content.is_extended_python(line):
                # The current line does not follow the Python syntax (it is "extended python",
                # see the pTyX plugin of the same name).
                return
            self._python_completion(line, col)
        else:
            self._latex_completion(line, col)

    def _latex_completion(self, line: int, col: int) -> None:
        """Open a pop-up with autocompletion suggestions for LaTeX code or pTyX code."""
        potential_command_stem = _get_potential_command_stem(self.editor.text(line)[:col])
        if len(potential_command_stem) <= self.minimal_char_count:
            return
        if potential_command_stem.startswith("\\"):
            commands_list = LATEX_COMMANDS
        else:
            if self.editor.doc.title.endswith(".ex") or "#LOAD{MCQ}" in self.editor.text():
                commands_list = PTYX_COMMANDS + PTYX_MCQ_COMMANDS
            else:
                commands_list = PTYX_COMMANDS

        sep = "\t"  # use a tab as separator, since a space may be present in an autocompletion snippet.
        item_list = sep.join(
            command for command in commands_list if command.startswith(potential_command_stem)
        )  # tab-separated, must be sorted

        if item_list:
            self.editor.SendScintilla(QsciScintilla.SCI_AUTOCSETSEPARATOR, ord(sep))
            self._command_stem = potential_command_stem
            self.editor.SendScintilla(
                QsciScintilla.SCI_AUTOCSHOW,
                len(potential_command_stem),  # lenEntered
                item_list.encode("utf-8"),
            )

    def _python_completion(self, line: int, col: int) -> None:
        """Open a pop-up with autocompletion suggestions for Python code snippets."""
        python_code = self.editor.python_content.context_python_code(line, col)

        # jedi line numbers are 1-based
        virtual_position = self.editor.python_content.virtual_position(line, col, first_line=1)

        if python_code is None or virtual_position is None:
            # Should not occur, except perhaps in case of race condition?
            return
        # Kill previous worker if still running
        if self._worker and self._worker.isRunning():
            self._worker.terminate()

        jedi_line, jedi_col = virtual_position
        print(f"{jedi_line=}, {jedi_col=}")

        # current_line = python_code.split("\n")[jedi_line - 1]
        # self._last_char = current_line[jedi_col - 1 : jedi_col]
        # print(f"{self._last_char=}")

        self._current_word = self._get_current_word()
        self._current_pos = self.editor.positionFromLineIndex(line, col)

        # Either ask for autocompletion, or for the signature of the function/method, depending on the last char.
        display_signature = self._last_char in ("(", ",")
        worker_class = SignatureWorker if display_signature else CompletionWorker
        self._worker = worker_class(python_code, jedi_line, jedi_col)
        self._worker.ready.connect(
            self._on_signature_ready if display_signature else self._on_completion_ready
        )
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_signature_ready(self, hint: list[str]) -> None:
        wrapped = textwrap.fill(hint[0], width=72)
        self.editor.SendScintilla(QsciScintilla.SCI_CALLTIPSHOW, self._current_pos, wrapped.encode("utf-8"))

    def _on_completion_ready(self, names: list[str]) -> None:
        if not self._apis or not names:
            return
        print(names, self._current_word)
        if len(names) == 1 and names[0] == self._current_word:
            # No need to show the suggestion, since it matches the current text!
            self.editor.cancelList()
            return
        if self._last_char == ".":
            # Force autocompletion popup to appear, bypassing QScintilla internal logic.
            # This is used to trigger autocompletion suggestions after a dot.
            # Bypass QsciAPIs entirely — show the raw list directly
            # SCI_AUTOCSHOW(int lenEntered, const char *itemList)
            # lenEntered = characters of the stem already typed (0 after a dot)
            item_list = " ".join(
                sorted(name for name in names if name[0] != "_")
            )  # space-separated, must be sorted
            self.editor.SendScintilla(QsciScintilla.SCI_AUTOCSETSEPARATOR, ord(" "))
            self.editor.SendScintilla(
                QsciScintilla.SCI_AUTOCSHOW,
                0,  # lenEntered
                item_list.encode("utf-8"),
            )
        else:
            self._apis.clear()
            for name in names:
                self._apis.add(name)
            self._apis.prepare()

            # Trigger the popup (only if user is still typing)
            self.editor.autoCompleteFromAPIs()

    def _on_error(self, message: str) -> None:
        print(message)
        print_warning("Autocompletion or signature failed.")

    def trigger_help(self) -> None:
        line, col = self.editor.getCursorPosition()
        pos = self.editor.positionFromLineIndex(line, col)
        x = self.editor.SendScintilla(QsciScintilla.SCI_POINTXFROMPOSITION, 0, pos)
        y = self.editor.SendScintilla(QsciScintilla.SCI_POINTYFROMPOSITION, 0, pos)
        global_pos = self.editor.mapToGlobal(QPoint(x, y + 20))
        if self.editor.python_content.is_inside_python_block(pos):
            self._trigger_python_help(line, col, global_pos)
        else:
            self._trigger_ptyx_help(line, col, global_pos)

    def _trigger_python_help(self, line: int, col: int, global_pos: QPoint) -> None:
        python_code = self.editor.python_content.context_python_code(line, col)
        virtual_position = self.editor.python_content.virtual_position(line, col, first_line=1)
        print("hello!")
        if python_code is None or virtual_position is None:
            return
        jedi_line, jedi_col = virtual_position
        script = jedi.Interpreter(python_code, NAME_SPACES)
        results: list[Name] = script.infer(jedi_line, jedi_col)
        definitions: list[Name] = script.goto(jedi_line, jedi_col)
        if not definitions:
            current_line = python_code.split("\n")[jedi_line - 1]
            print("No info for:")
            print(current_line)
            start, end = self._get_current_word_range()
            _, col1 = self.editor.lineIndexFromPosition(start)
            _, col2 = self.editor.lineIndexFromPosition(end)
            print(col1 * "-" + (col2 - col1) * "^")
            return

        message = generate_python_help_message(results, definitions)
        self.tooltip.show_at(global_pos, message, as_html=True)

    def _trigger_ptyx_help(self, line: int, col: int, global_pos: QPoint):
        start, end = self._get_current_word_range()
        content = self.editor.text().encode("utf8")
        print("previous:", content[start - 1 : start], b"#")
        if start == 0 or content[start - 1 : start] != b"#":
            # This is not a pTyX command
            return
        tag = content[start:end].decode("utf8")
        if tag not in PTYX_COMMANDS + PTYX_MCQ_COMMANDS:
            return
        message = generate_ptyx_help_message(tag)
        print("ptyx help:", message)
        self.tooltip.show_at(global_pos, message, as_html=True)
