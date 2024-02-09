import ast
import re
import traceback
from enum import IntEnum
from typing import TYPE_CHECKING

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QKeyEvent
from PyQt6.QtWidgets import QDialog

from ptyx_mcq_editor.editor.lexer import MyLexer
from ptyx_mcq_editor.enhanced_widget import EnhancedWidget
from ptyx_mcq_editor.generated_ui import dbg_send_scintilla_messages_ui

if TYPE_CHECKING:
    from ptyx_mcq_editor.editor.editor_tab import EditorTab

SEARCH_MARKER_ID = 0
INCLUDE_DIRECTIVES_ID = 1

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
    # `let` is a pseudo-keyword added to python to declare variables very quickly.
    # Since it is not valid python syntax, we'll have to convert it
    # before testing python syntax.
    def sub(m: re.Match):
        vars_str = m.groupdict()["vars1"]
        if vars_str is None:
            vars_str = m.groupdict()["vars2"]
        return f"{vars_str}=..."

    code = re.sub("^( *)let ((?P<vars1>.+?) +(with|in) +|(?P<vars2>.+))", sub, flags=re.MULTILINE)
    try:
        ast.parse(code)
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


class EditorWidget(QsciScintilla, EnhancedWidget):
    def __init__(self, parent: "EditorTab"):
        super().__init__(parent)
        self.status_message: str = ""
        self._directives_lines: list[int] = []
        self._modifiers = Qt.KeyboardModifier.NoModifier

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
        self.setMarginsForegroundColor(QColor("#ff888888"))

        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)

        self.setLexer(MyLexer(self))

        # Marker use to highlight all search results
        self.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, SEARCH_MARKER_ID, QsciScintilla.INDIC_FULLBOX)
        self.SendScintilla(QsciScintilla.SCI_INDICSETALPHA, SEARCH_MARKER_ID, 100)
        self.SendScintilla(QsciScintilla.SCI_INDICSETOUTLINEALPHA, SEARCH_MARKER_ID, 200)
        self.SendScintilla(QsciScintilla.SCI_INDICSETFORE, SEARCH_MARKER_ID, QColor("#67d0eb"))

        self.indicatorDefine(QsciScintilla.IndicatorStyle.DotBoxIndicator, INCLUDE_DIRECTIVES_ID)
        self.setIndicatorHoverForegroundColor(QColor("#67d0eb"), INCLUDE_DIRECTIVES_ID)
        self.setIndicatorHoverStyle(QsciScintilla.IndicatorStyle.FullBoxIndicator, INCLUDE_DIRECTIVES_ID)
        self.textChanged.connect(self.update_include_indicators)

        # Don't use QScintilla.indicatorClicked signal, since it lead to an occasional severe bug with a selection
        # anchor impossible to remove.
        self.indicatorClicked.connect(self.save_modifiers)
        self.indicatorReleased.connect(self.on_click)

        # self.installEventFilter(EventFilter(self))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # key code == 40 -> "("
        key = event.key()
        if self.hasSelectedText() and key in (int(k) for k in DelimiterKeyCode):
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
        else:
            super().keyPressEvent(event)

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
        last = self.lines() - 1
        self.clearIndicatorRange(0, 0, last, len(self.text(last)), INCLUDE_DIRECTIVES_ID)
        n_includes = n_disabled_includes = 0
        self._directives_lines.clear()
        i: int
        line: str
        for i, line in enumerate(self.text().split("\n")):
            if line.startswith("-- "):
                if not line[3:].lstrip().startswith("DIR:"):
                    self.fillIndicatorRange(i, 3, i, len(line), INCLUDE_DIRECTIVES_ID)
                    n_includes += 1
                self._directives_lines.append(i)
            elif line.startswith("!-- "):
                if not line[4:].lstrip().startswith("DIR:"):
                    self.fillIndicatorRange(i, 4, i, len(line), INCLUDE_DIRECTIVES_ID)
                    n_disabled_includes += 1
                self._directives_lines.append(i)
        if n_includes > 0 or n_disabled_includes > 0:
            self.status_message = f"{n_includes} imports ({n_disabled_includes} disabled)"
        else:
            self.status_message = ""
        self.main_window.file_events_handler.update_status_message()

    def save_modifiers(self, line, _, keys):
        self._modifiers = keys

    def on_click(self, line, _, keys):
        ctrl_pressed = self._modifiers & Qt.KeyboardModifier.ControlModifier
        shift_pressed = self._modifiers & Qt.KeyboardModifier.ShiftModifier
        try:
            self.main_window.file_events_handler.open_file_from_current_ptyx_import_directive(
                current_line=line,
                background=not shift_pressed,
                preview_only=not ctrl_pressed and not shift_pressed,
            )
        except IOError:
            traceback.print_exc()
        if shift_pressed:
            # Scintilla select text as a side effect when clicking with shift key pressed.
            self.unselect()

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
