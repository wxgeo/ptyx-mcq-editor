from typing import TYPE_CHECKING

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QDialog

from ptyx_mcq_editor.editor.lexer import MyLexer
from ptyx_mcq_editor.enhanced_widget import EnhancedWidget
from ptyx_mcq_editor.generated_ui import dbg_send_scintilla_messages_ui

if TYPE_CHECKING:
    from ptyx_mcq_editor.editor.editor_tab import EditorTab

SEARCH_MARKER_ID = 0


class EditorWidget(QsciScintilla, EnhancedWidget):
    def __init__(self, parent: "EditorTab"):
        super().__init__(parent)

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

        self.setLexer(MyLexer(self))

        # Marker use to highlight all search results
        self.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, SEARCH_MARKER_ID, QsciScintilla.INDIC_FULLBOX)
        self.SendScintilla(QsciScintilla.SCI_INDICSETALPHA, SEARCH_MARKER_ID, 100)
        self.SendScintilla(QsciScintilla.SCI_INDICSETOUTLINEALPHA, SEARCH_MARKER_ID, 200)
        self.SendScintilla(QsciScintilla.SCI_INDICSETFORE, SEARCH_MARKER_ID, QColor("#67d0eb"))

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
        line = self.getCursorPosition()[0]
        return self.text(line)
