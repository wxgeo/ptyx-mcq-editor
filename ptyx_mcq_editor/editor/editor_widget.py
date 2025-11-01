import ast
import re
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QKeyEvent, QDragEnterEvent, QMouseEvent
from PyQt6.QtWidgets import QDialog, QFileDialog
from ptyx.extensions.extended_python import parse_extended_python_code
from ptyx.errors import PythonBlockError, ErrorInformation, PythonCodeError

from ptyx_mcq_editor.editor.indicator_handlers import Indicators
from ptyx_mcq_editor.editor.lexer import MyLexer, Mode
from ptyx_mcq_editor.enhanced_widget import EnhancedWidget
from ptyx_mcq_editor.generated_ui import dbg_send_scintilla_messages_ui
from ptyx_mcq_editor.tools.python_code_tools import format_each_python_block, check_each_python_block


if TYPE_CHECKING:
    from ptyx_mcq_editor.editor.editor_tab import EditorTab


# Python keywords which introduced a new indented block, like `if`, `for`...
PYTHON_INDENTED_BLOCK_KEYWORDS = [
    "async",
    "class",
    "def",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "if",
    "try",
    "while",
    "with",
    "case",
    "match",
]


# TODO: tool tips for clickable lines.
#  https://riverbankcomputing.com/pipermail/qscintilla/2008-November/000382.html
#  https://doc.qt.io/qt-6/qtooltip.html#showText


# class EventFilter(QObject):
#     # noinspection PyMethodOverriding
#     def eventFilter(self, widget: QObject | None, event: QEvent | None) -> bool:
#         if event is not None and event.type() == QEvent.Type.ShortcutOverride:
#             assert isinstance(event, QKeyEvent)
#             # Ignore only the Ctrl + / shortcut override (char("47") == "/").
#             if (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() == 47:
#                 event.ignore()
#                 return True
#         return super().eventFilter(widget, event)


def analyze_code(code: str) -> SyntaxError | None:
    try:
        ast.parse(parse_extended_python_code(code))
    except SyntaxError as e:
        return e
    return None


# TODO:
#  We should analyze code in real time to detect its structure:
#  - parts of python code
#  - parts of MCQ code
#  - strings inside python code...


class DelimiterKeyCode(IntEnum):
    DOLLAR = 36
    PARENTHESIS = 40
    BRACKET = 91
    BRACE = 123
    SINGLE_QUOTE = 39
    DOUBLE_QUOTE = 34


class Marker(IntEnum):
    ERROR = 0
    NEW = 1


# class Indicator(IntEnum):
#     SEARCH_MARKER_ID = 0
#     INCLUDE_DIRECTIVES_ID = 1
#     COMPILATION_ERROR = 2
#     VALID_STUDENTS_IDS_PATH = 3
#     INVALID_STUDENTS_IDS_PATH = 4


MARGIN_COLOR = QColor("#ff888888")


class EditorWidget(QsciScintilla, EnhancedWidget):
    """Code editor based on QScintilla."""

    charHovered = pyqtSignal(int, int, name="charHovered")

    def __init__(self, parent: "EditorTab"):
        super().__init__(parent)
        self._parent_ = parent
        self.status_message: str = ""
        self._directives_lines: list[int] = []
        self._last_error_message = ""
        self._errors_info: dict[int, ErrorInformation] = {}
        self.student_ids_path: Path | None = None

        self.setUtf8(True)  # Set encoding to UTF-8
        font = QFont()
        font.setPointSize(13)
        self.setFont(font)  # Gets overridden by lexer later on

        # 1. Text wrapping
        # -----------------
        self.setWrapMode(QsciScintilla.WrapMode.WrapWord)
        self.setWrapVisualFlags(QsciScintilla.WrapVisualFlag.WrapFlagByText)
        self.setWrapIndentMode(QsciScintilla.WrapIndentMode.WrapIndentIndented)

        # 2. End-of-line mode
        # --------------------
        self.setEolMode(QsciScintilla.EolMode.EolUnix)
        self.setEolVisibility(False)

        # 3. Indentation
        # ---------------
        self.setIndentationsUseTabs(False)
        self.setTabWidth(4)
        self.setIndentationGuides(True)
        self.setTabIndents(True)
        self.setAutoIndent(True)

        # 4. Caret
        # ---------
        self.setCaretForegroundColor(QColor("#ff0000ff"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#1f0000ff"))
        self.setCaretWidth(2)

        # 5. Margins
        # -----------
        # Margin 0 = Line nr margin
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setMarginsForegroundColor(MARGIN_COLOR)

        # Margin 1 = Text Margin
        self.setMarginType(1, QsciScintilla.MarginType.TextMargin)
        self.setMarginWidth(1, "0")

        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)

        self._lexer = MyLexer(self)
        self.setLexer(self._lexer)

        self.indicators = Indicators(self)

        self.charHovered.connect(self.indicators.on_hover)

        # noinspection PyUnresolvedReferences
        self.textChanged.connect(self.on_text_changed)

        self.markerDefine("|", Marker.ERROR)
        self.setMarkerBackgroundColor(QColor("red"), Marker.ERROR)
        self.setMarkerForegroundColor(QColor("red"), Marker.ERROR)
        self.setMarginSensitivity(0, True)
        self.setMarginSensitivity(1, True)
        # noinspection PyUnresolvedReferences
        self.marginClicked.connect(self.on_margin_clicked)

        self.markerDefine("N", Marker.NEW)
        self.setMarkerBackgroundColor(QColor("red"), Marker.NEW)
        self.setMarkerForegroundColor(QColor("yellow"), Marker.NEW)

        # self.installEventFilter(EventFilter(self))

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        assert event is not None
        key = event.key()
        # DelimiterKeyCode: all wrapping characters, like (), {}, "", '' and so on.
        if self.hasSelectedText() and key in (int(k) for k in DelimiterKeyCode):
            # When text is selected and user presses a parenthesis, for example, all
            # the selected text must be wrapped with a couple of parenthesis.
            from_line, from_col, to_line, to_col = self.getSelection()
            start = chr(key)
            if start == "(":
                end = ")"
            elif start == "[":
                end = "]"
            elif start == "{":
                end = "}"
            else:
                end = start
            self.insertAt(end, to_line, to_col)
            self.insertAt(start, from_line, from_col)
            self.setCursorPosition(to_line, to_col + 2)
        elif key in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            line, index = self.getCursorPosition()
            text = self.text(line).strip()
            if (
                text.endswith(":")
                and text[:-1].split()[0] in PYTHON_INDENTED_BLOCK_KEYWORDS
                and self.is_python_block_code(line, index)
            ):
                # Implement smart indentation inside a python code block.
                # When user press [Enter] after writing for example `if x == 3:`,
                # following line must be automatically indented with 4 additional spaces.
                indent = len(self.text(line)) - len(self.text(line).lstrip()) + 4
                super().keyPressEvent(event)
                self.insert(4 * " ")
                self.setCursorPosition(line + 1, indent)
            else:
                # Default action.
                super().keyPressEvent(event)
        else:
            # Default action.
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        # Close any existing Calltip.
        self.SendScintilla(QsciScintilla.SCI_CALLTIPCANCEL)
        # Step 1: Get mouse coordinates
        point = event.position()
        x = round(point.x())
        y = round(point.y())
        position = self.SendScintilla(QsciScintilla.SCI_POSITIONFROMPOINTCLOSE, x, y)
        # `position` will contain -1 if the mouse's pointer is outside the window or not over the text,
        # else it will be the corresponding position in the text.
        if position != -1:
            self.charHovered.emit(*self.lineIndexFromPosition(position))

    def is_python_block_code(self, line: int, index: int) -> bool:
        """Return `True` iff we are inside a python block code, yet not in a python string."""
        return self._lexer.get_style_and_mode(self.positionFromLineIndex(line, index))[1] == Mode.PYTHON

    def display_error(self, error: BaseException, code: str = None) -> None:
        """Display an error when a document failed to be compiled.

        An error marker will appear in the editor left margin,
        and a message will be displayed in the status bar too.
        """
        self.main_window.statusbar.setStyleSheet("color: red;font-weight: bold")
        current_doc_path = self._parent_.doc.path
        if current_doc_path is not None:
            current_doc_path = current_doc_path.resolve()
        if isinstance(error, PythonCodeError):
            info = error.info
            self._last_error_message = info.message
            file_path = None
            if error.ptyx_traceback:
                if (localisation := error.ptyx_traceback[-1][0]) is not None:
                    file_path = Path(localisation)
            error_message = (f"<{info.type}> " if info.type else "") + info.message
            self.main_window.statusbar.showMessage(
                f"Compilation failed: {error_message}."
                + ("" if file_path is None else f" (File: '{file_path.name}')")
            )
            print(info)
            # To highlight error, we have to be sure that the error row and column are known.
            # We must also verify that the error occurred in the current document, and not in an imported one.

            if (
                isinstance(error, PythonBlockError)
                and error.label.isascii()
                and error.label.isdigit()
                and (
                    file_path is None
                    or self._parent_.doc.path is None
                    or current_doc_path == file_path.resolve()
                )
            ):
                shift = int(error.label) - 2
                row = 0 if info.row is None else info.row
                col = 0 if info.col is None else info.col
                end_row = row if info.end_row is None else info.end_row
                end_col = col if info.end_col is None else info.end_col
                row, end_row = min(row, end_row), max(row, end_row)
                row += shift
                end_row += shift
                col, end_col = min(col, end_col), max(col, end_col)
                line_length = len(self.text(row))
                col = min(line_length - 1, col)
                end_col = max(col + 1, end_col)
                self._highlight_error(row, col, end_row, end_col)
            elif (
                file_path is not None
                and self._parent_.doc.path is not None
                and current_doc_path != file_path.resolve()
                and error.ptyx_traceback is not None
            ):
                # Highlight the import line, if the error is in an imported document.
                pick_next_line_num = False
                position = None
                for path, position in error.ptyx_traceback:
                    if path is not None and Path(path).resolve() == self._parent_.doc.path.resolve():
                        pick_next_line_num = True
                    if pick_next_line_num:
                        break
                if position is not None:
                    # Skip comments.
                    line_num = None
                    i = 0
                    for line_num, line in enumerate(self.text().split("\n")):
                        if not line.startswith("# "):
                            i += 1
                        if i > position:
                            break
                    if line_num is not None:
                        self._highlight_error(line_num)
        else:
            self.main_window.statusbar.showMessage(f"{type(error).__name__}: {error}")

    def _highlight_error(self, row: int, col: int = 0, end_row: int | None = None, end_col: int = -1) -> None:
        if end_row is None:
            end_row = row
        if end_col == -1:
            end_col = len(self.text(row)) - 1
        print("Highlight error:", row, col, end_row, end_col)
        # Now apply the indicator-style on the chosen text
        self.indicators.compilation_error.apply(row, col, end_row, end_col)

    def dragEnterEvent(self, event: QDragEnterEvent):  # type: ignore
        if self.main_window.file_events_handler.any_dragged_file(event):
            event.ignore()
        else:
            QsciScintilla.dragEnterEvent(self, event)

    def autoformat(self) -> None:
        # TODO: display a message in the status bar if autoformat fails.
        #  For that, `format_each_python_block()` should return a status code.
        # Don't use `QScintilla.setText()`, as it would clear undo/redo history.
        self.setText(format_each_python_block(self.text()), preserve_history=True)

    def setText(self, text: str, preserve_history=False):
        """Change editor text content.

        By default, `QsciScintilla.setText()` resets history, but using
        `preserve_history` keeps previous actions history, and
         enables to undo action."""
        if preserve_history:
            if text != self.text():
                self.SendScintilla(QsciScintilla.SCI_SETTEXT, text.encode("utf8"))
        else:
            super().setText(text)

    # def setTextButPreserveHistory(self, new_text: str):
    #     """Change editor text content, but preserve modifications history.
    #
    #     `QsciScintilla.setText()` clears history, which is often unwanted."""
    #     if new_text != self.text():
    #         self.SendScintilla(QsciScintilla.SCI_SETTEXT, new_text.encode("utf8"))

    def on_text_changed(self) -> None:
        self.clear_indicators()
        self.markerDeleteAll(Marker.NEW)
        self.main_window.statusbar.showMessage("")
        self.update_include_indicators()
        self.check_python_code()

    def on_margin_clicked(self, margin: int, line: int, state: Qt.KeyboardModifier) -> None:
        print("ok")
        if line in self._errors_info:
            position = self.positionFromLineIndex(line, 0)
            info = self._errors_info[line]
            msg = (f"{info.type}: " if info.type else "") + info.message
            self.SendScintilla(QsciScintilla.SCI_CALLTIPSHOW, position, msg.encode("utf8"))

    def check_python_code(self):
        self.markerDeleteAll(Marker.ERROR)
        self._errors_info.clear()
        for error_info in check_each_python_block(self.text()):
            self.markerAdd(error_info.row, Marker.ERROR)
            self._errors_info[error_info.row] = error_info

    def on_save(self) -> None:
        self.autoformat()
        # Tell Scintilla that the current editor's state is its new saved state.
        # More information on Scintilla messages: http://www.scintilla.org/ScintillaDoc.html
        self.SendScintilla(QsciScintilla.SCI_SETSAVEPOINT)

    def clear_indicators(self) -> None:
        self.indicators.include_directive.clear()
        self.indicators.compilation_error.clear()

    def dbg_send_scintilla_command(self) -> None:
        dialog = QDialog(self)
        ui = dbg_send_scintilla_messages_ui.Ui_Dialog()
        ui.setupUi(dialog)

        def send_command_and_display_return() -> None:
            editor = self
            message_name = "SCI_" + ui.message_name.text()
            msg = getattr(editor, message_name, None)
            args = [eval(arg) for arg in ui.message_args.text().split(",") if arg.strip()]
            if msg is None:
                ui.return_label.setText(f"Invalid message name: {message_name}.")
            else:
                try:
                    val = editor.SendScintilla(msg, *args)
                    ui.return_label.setText(f"Return: {val!r}")
                except Exception as e:
                    ui.return_label.setText(f"Return: {e!r}")

        ui.sendButton.pressed.connect(send_command_and_display_return)
        dialog.show()

    def get_current_line_text(self) -> str:
        """Get the content of the current line."""
        line = self.getCursorPosition()[0]
        return self.text(line)

    def update_include_indicators(self) -> None:
        """
        Create Scintilla indicators for include directives.

        Those indicators can then be clicked to get the corresponding files.
        """
        n_includes = n_disabled_includes = 0
        self._directives_lines.clear()
        i: int
        line: str
        # TODO: once a real pTyX code parser is implemented for an accurate syntax highlighting,
        #  it should be used to detect accurately include directives as well.
        header_started = header_ended = False
        for i, line in enumerate(self.text().split("\n")):
            if line.startswith("===") and all(c == "=" for c in line):
                if not header_started:
                    header_started = True
                else:
                    header_ended = True
            if (
                header_started
                and not header_ended
                and (m := re.fullmatch(r"(ids\s*=\s*)(.+)", line)) is not None
            ):
                self.student_ids_path = path = Path(m.group(2))
                col = len(m.group(1))
                self.indicators.valid_students_path.clear()
                self.indicators.wrong_students_path.clear()
                if path.is_file():
                    self.indicators.valid_students_path.apply(i, col, i, len(line))
                else:
                    self.indicators.wrong_students_path.apply(i, col, i, len(line))

            elif line.startswith("-- "):
                if not line[3:].lstrip().startswith("DIR:"):
                    self.indicators.include_directive.apply(i, 3, i, len(line))
                    n_includes += 1
                self._directives_lines.append(i)
            elif line.startswith("!-- "):
                if not line[4:].lstrip().startswith("DIR:"):
                    self.indicators.include_directive.apply(i, 4, i, len(line))
                    n_disabled_includes += 1
                self._directives_lines.append(i)
        if n_includes > 0 or n_disabled_includes > 0:
            self.status_message = f"{n_includes} imports ({n_disabled_includes} disabled)"
        else:
            self.status_message = ""
        self.main_window.file_events_handler.update_status_message()

    def replace_line(self, line: int, new_text: str) -> None:
        """Replace a specific range of text in the document."""
        start_pos = self.positionFromLineIndex(line, 0)
        end_pos = self.positionFromLineIndex(line, self.lineLength(line))
        self.SendScintilla(QsciScintilla.SCI_SETSELECTION, start_pos, end_pos)
        self.SendScintilla(QsciScintilla.SCI_REPLACESEL, new_text.encode("utf8"))
        self.update_include_indicators()

    def selectStudentsIdsFile(self) -> None:
        """Select a csv file containing the students IDs."""
        if self.student_ids_path is None:
            current = ""
        elif not self.student_ids_path.is_dir():
            current = str(self.student_ids_path.parent)
        else:
            current = str(self.student_ids_path)
        # noinspection PyTypeChecker
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select a CSV file containing the students names and IDs", current, "CSV File (*.csv)"
        )
        if filename:
            header_started = header_ended = False
            for i, line in enumerate(self.text().split("\n")):
                if line.startswith("===") and all(c == "=" for c in line):
                    if not header_started:
                        header_started = True
                    else:
                        header_ended = True
                if (
                    header_started
                    and not header_ended
                    and (re.fullmatch(r"(ids\s*=\s*)(.+)", line)) is not None
                ):
                    self.replace_line(i, f"ids = {filename}\n")

    def deleteAt(self, line: int, col: int, n: int) -> None:
        """Delete `n` (unicode) chars on the given line, starting from given column.

        Other lines will never be affected, even if `n` is greater than
        the number of remaining chars on the line.

        If `n` is negative, it will remove chars backward starting from given column.
        """
        from_position = self.positionFromLineIndex(line, col)
        # `n` is a number of characters, while Scintilla expect a number of bytes.
        # So, let's use `positionFromLineIndex()` to make the conversion.
        to_position = self.positionFromLineIndex(line, col + n)
        self.SendScintilla(QsciScintilla.SCI_DELETERANGE, from_position, to_position - from_position)

    def toggle_comment(self) -> None:
        """Comment or uncomment current line,
        or lines corresponding to current selection if any.
        """
        from_line, from_col, to_line, to_col = self.getSelection()
        if from_line == -1:
            # No selection: comment/uncomment the current line only.
            self.toggle_comment_at_line(self.getCursorPosition()[0])
        else:
            # Selected text found: comment/uncomment all selected lines.
            # Nota:
            # Method `toggle_comment_at_line()` loose selection when calling `QScintilla.insertAt()`.
            # Since it's nicer to keep the selection (to be able to comment and uncomment several lines
            # successively), we'll have to restore it.
            # However, we have to take care of inserted or deleted characters,
            # since they induce a shift in the selection start and end positions.
            from_shift = to_shift = 0
            for line_num in range(from_line, to_line + 1):
                to_shift = self.toggle_comment_at_line(line_num)
            if from_shift == 0:
                from_shift = to_shift
            # Restore selection
            self.setSelection(from_line, from_col + from_shift, to_line, to_col + to_shift)

    def toggle_comment_at_line(self, line_num: int) -> int:
        """Comment or uncomment given line.

        Return the number of characters inserted or deleted at the start of the line.
        (Result will be positive for inserted characters, negative else).
        """
        line = self.text(line_num)
        if line_num in self._directives_lines:
            # Special case: to disable a directive, prefix it with `!`.
            if line.startswith("!"):
                # Enable directive.
                self.deleteAt(line_num, 0, 1)
                return -1
            else:
                # Disable directive.
                self.insertAt("!", line_num, 0)
                return 1
        else:
            # General case: prefix a line with `# ` to comment it.
            if line.startswith("# "):
                # Uncomment line.
                self.deleteAt(line_num, 0, 2)
                return -2
            else:
                # Comment line.
                self.insertAt("# ", line_num, 0)
                return 2

    def unselect(self):
        line, col = self.getCursorPosition()
        self.setSelection(line, col, line, col)
