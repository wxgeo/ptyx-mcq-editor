import re
from enum import Enum, auto
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets
from PyQt6.Qsci import QsciScintilla

from ptyx_mcq_editor.editor_widget import SEARCH_MARKER_ID

if TYPE_CHECKING:
    from ptyx_mcq_editor.main_window import McqEditorMainWindow


class SearchAction(Enum):
    FIND_NEXT = auto()
    FIND_PREVIOUS = auto()
    REPLACE = auto()


class FindAndReplaceWidget(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.new_search = True
        self.last_search_action: SearchAction | None = None
        # Set later by main_window:
        self.main_window: McqEditorMainWindow = None  # type: ignore

    @property
    def mcq_editor(self):
        return self.main_window.current_mcq_editor

    @property
    def find_field(self):
        return self.main_window.find_field

    @property
    def replace_field(self):
        return self.main_window.replace_field

    @property
    def replace_label(self):
        return self.main_window.replace_label

    @property
    def replace_button(self):
        return self.main_window.replace_button

    @property
    def replace_all_button(self):
        return self.main_window.replace_all_button

    @property
    def regexCheckBox(self):
        return self.main_window.regexCheckBox

    @property
    def caseCheckBox(self):
        return self.main_window.caseCheckBox

    @property
    def selectionOnlyCheckBox(self):
        return self.main_window.selectionOnlyCheckBox

    @property
    def wholeCheckBox(self):
        return self.main_window.wholeCheckBox

    def toggle_find_and_replace_dialog(self, replace=True):
        if (replace and self.replace_field.isVisible()) or (
            not replace and self.find_field.isVisible() and not self.replace_field.isVisible()
        ):
            # Typing Ctrl+F once open the dock, typing Ctrl+F again close it.
            # Same thing for Ctrl+H.
            self.setVisible(False)
        else:
            self.display_replace_widgets(replace)
            self.setVisible(True)
            selected_text = self.mcq_editor.selectedText()
            if selected_text:
                if "\n" in selected_text:
                    # The user probably wants to search only in the selection
                    self.selectionOnlyCheckBox.setChecked(True)
                else:
                    # The selection is probably used to highlight the word to search.
                    self.find_field.setText(selected_text)
            else:
                self.selectionOnlyCheckBox.setChecked(False)
            self.find_field.setFocus()
            if self.find_field.text():
                self.highlight_all_find_results()

    def clear_indicators(self):
        last_line = self.mcq_editor.lines() - 1
        self.mcq_editor.clearIndicatorRange(
            0, 0, last_line, len(self.mcq_editor.text(last_line)) - 1, SEARCH_MARKER_ID
        )

    def reset_search(self):
        # During a search, when `findNext()` is called, the cursor is automatically
        # moved to the next occurrence, so the signal `cursorPositionChanged`
        # is emitted. However, the search must not be reset, since the cursor was not
        # manually moved (if the search is reset, replacement will not occur).
        # If the mcq_editor has not the focus, it means
        # cursor hasn't been moved manually.
        # This is not perfect though, since if mcq_editor has focus,
        # the cursor may have been moved programmatically yet (e.g. using F3 or SHIFT+F3).
        # One (dirty) solution is to force `mcq_editor` to lose
        # its focus (see `find_and_replace()` comment).
        # Maybe there is a cleaner and more reliable way to do this ?
        # I tried to disconnect signal when entering `find_and_replace()`,
        # and restoring it after, but it doesn't work. The `cursorPositionChanged` signal is maybe
        # emitted only after leaving `find_and_replace()` ?
        if self.mcq_editor.hasFocus():
            self.new_search = True
            print("New search")
        else:
            print("New search blocked")

    def search_changed(self):
        print("New search and highlight")
        self.new_search = True
        self.highlight_all_find_results()

    def selection_range(self) -> tuple[int, int]:
        """Return start and end position of the selection.

        Those positions correspond to the number of bytes, and not the number of unicode characters.
        """
        line_from, index_from, line_to, index_to = self.mcq_editor.getSelection()
        return (
            self.mcq_editor.positionFromLineIndex(line_from, index_from),
            self.mcq_editor.positionFromLineIndex(line_to, index_to),
        )

    def highlight_all_find_results(self):
        """Highlight all search results."""
        self.find_field.setStyleSheet("")
        self.clear_indicators()
        if self.isHidden():
            return
        to_find = self.find_field.text()
        if not to_find:
            return
        text = self.mcq_editor.text()
        # if not self.caseCheckBox.isChecked():
        #     to_find = to_find.lower()
        #     text = text.lower()
        # Scintilla positions correspond to a number of bytes, not a number of characters.
        to_find_as_bytes = to_find.encode("utf8")
        text_as_bytes = text.encode("utf8")
        flags = 0
        if not self.caseCheckBox.isChecked():
            flags |= re.IGNORECASE
        if not self.regexCheckBox.isChecked():
            to_find_as_bytes = re.escape(to_find_as_bytes)
        if self.wholeCheckBox.isChecked():
            to_find_as_bytes = rb"\b" + to_find_as_bytes + rb"\b"

        start = 0
        end = len(text_as_bytes)
        if self.selectionOnlyCheckBox.isChecked():
            start, end = self.selection_range()
        try:
            for match in re.finditer(to_find_as_bytes, text_as_bytes[start:end], flags=flags):
                self.mcq_editor.SendScintilla(
                    QsciScintilla.SCI_INDICATORFILLRANGE, start + match.start(), match.end() - match.start()
                )
        except re.error:
            self.find_field.setStyleSheet("background-color: #ffe2db")

        # https://stackoverflow.com/questions/54305745/how-to-unselect-unhighlight-selected-and-highlighted-text-in-qscintilla-editor

    def display_replace_widgets(self, display: bool):
        self.replace_label.setVisible(display)
        self.replace_field.setVisible(display)
        self.replace_button.setVisible(display)
        self.replace_all_button.setVisible(display)

    def replace_all(self):
        self.mcq_editor.setCursorPosition(0, 0)
        self.mcq_editor.SendScintilla(QsciScintilla.SCI_BEGINUNDOACTION)
        while self.find_and_replace(action=SearchAction.REPLACE):
            pass
        self.mcq_editor.SendScintilla(QsciScintilla.SCI_ENDUNDOACTION)
        self.mcq_editor.setFocus()

    def find_and_replace(self, action: SearchAction) -> bool:
        # Because of `reset_search()` method hack (see comment there),
        # it is important for `mcq_editor` to lose its focus.
        self.find_field.setFocus()
        if action in (action.FIND_NEXT, action.FIND_PREVIOUS) and action != self.last_search_action:
            self.new_search = True
            self.last_search_action = action
        if not self.new_search:
            if action == SearchAction.REPLACE:
                self.mcq_editor.replace(self.replace_field.text())

            if not (next_find := self.mcq_editor.findNext()):
                # Restart search from the beginning of the text.
                self.new_search = True
            return next_find
        else:
            self.new_search = False
            to_find: str = self.find_field.text()
            is_regex = self.regexCheckBox.isChecked()
            case_sensitive = self.caseCheckBox.isChecked()
            selection_only = self.selectionOnlyCheckBox.isChecked()
            whole_words = self.wholeCheckBox.isChecked()
            # current_text = self.mcq_editor.text()
            forward = action != SearchAction.FIND_PREVIOUS
            print(f"{forward=}")

            # https://brdocumentation.github.io/qscintilla/classQsciScintilla.html#a04780d47f799c56b6af0a10b91875045
            if selection_only:
                return self.mcq_editor.findFirstInSelection(
                    to_find, is_regex, case_sensitive, whole_words, forward=forward
                )
            else:
                return self.mcq_editor.findFirst(
                    to_find, is_regex, case_sensitive, whole_words, True, forward=forward
                )
