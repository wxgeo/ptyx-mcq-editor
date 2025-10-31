"""
This module defines static classes providing specific indicators data and methods.
"""

import traceback
from abc import ABC
from dataclasses import dataclass, asdict

from typing import ClassVar, TYPE_CHECKING, Iterator

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


if TYPE_CHECKING:
    from ptyx_mcq_editor.editor.editor_widget import EditorWidget


@dataclass
class IndicatorStyling:
    style: int
    fore: QColor | None = None
    stroke_width: int | None = None
    alpha: int | None = None  # The alpha value ranges from 0 (completely transparent) to 255 (fully opaque).
    outline_alpha: int | None = None  # idem
    under: bool | None = None
    hover_style: int | None = None
    hover_fore: QColor | None = None
    flags: int | None = None


class Indicator(ABC):
    """
    Base (abstract) class for each QScintilla indicator.
    """

    # List of all indicators (this list will be automatically populated with all subclasses).
    indicators_list: ClassVar[list[type["Indicator"]]] = []
    # Unique identifier for each indicator, required by QScintilla.
    # It will be automatically set at subclass creation.
    num: ClassVar[int]

    # Must be redefined in subclasses.
    styling: ClassVar[IndicatorStyling]

    def __init_subclass__(cls: type["Indicator"], **kwargs):
        cls.num = len(Indicator.indicators_list)
        Indicator.indicators_list.append(cls)
        setattr(Indicator, cls.__name__, cls)

    def __init__(self, editor: "EditorWidget"):
        self.editor = editor
        for property_name, property_value in asdict(self.styling).items():
            if property_value is not None:
                sci_code = getattr(QsciScintilla, "SCI_INDICSET" + property_name.upper().replace("_", ""))
                # Apply indicator style.
                self.editor.SendScintilla(sci_code, self.num, property_value)

    def on_left_click(self, line: int, index: int, ctrl_pressed=False, shift_pressed=False) -> None:
        pass

    def on_right_click(self, line: int, index: int, ctrl_pressed=False, shift_pressed=False) -> None:
        pass

    def is_present_at(self, position: int) -> bool:
        """Test if indicator is at the given position."""
        return self.editor.SendScintilla(QsciScintilla.SCI_INDICATORVALUEAT, self.num, position) > 0

    def apply(self, start_line: int, start_col: int, end_line: int, end_col: int) -> None:
        """Apply this indicator from position `start` to position `end`."""
        self.editor.fillIndicatorRange(start_line, start_col, end_line, end_col, self.num)

    # def apply(self, start: int, end: int) -> None:
    #     """Apply this indicator from position `start` to position `end`."""
    #     send = self.editor.SendScintilla
    #     send(QsciScintilla.SCI_SETINDICATORCURRENT, self.num)
    #     send(QsciScintilla.SCI_SETINDICATORVALUE, self.num)
    #     send(QsciScintilla.SCI_INDICATORFILLRANGE, start, end - start)

    # def apply_to_line(self, line: int, start: int = 0, end: int | None = None) -> None:
    #     """Apply this indicator from index `start` to index `end` to line `line`."""
    #     if end is None:
    #         end = len(self.editor.text(line))
    #     self.editor.fillIndicatorRange(line, start, line, end, self.num)

    def clear(self) -> None:
        last_line = self.editor.lines() - 1
        self.editor.clearIndicatorRange(0, 0, last_line, len(self.editor.text(last_line)), self.num)


class SearchMarker(Indicator):
    """Marker use to highlight all search results."""

    styling = IndicatorStyling(
        style=QsciScintilla.INDIC_FULLBOX,
        fore=QColor("#67d0eb"),
        alpha=100,
        outline_alpha=200,
    )


class IncludeDirective(Indicator):
    """Highlight all include directives in a .ptyx file."""

    styling = IndicatorStyling(
        style=QsciScintilla.INDIC_DOTBOX,
        hover_fore=QColor("#67d0eb"),
        hover_style=QsciScintilla.INDIC_FULLBOX,
    )

    def on_left_click(self, line: int, index: int, ctrl_pressed=False, shift_pressed=False) -> None:
        try:
            self.editor.main_window.file_events_handler.open_file_from_current_ptyx_import_directive(
                current_line=line,
                background=not shift_pressed,
                preview_only=not ctrl_pressed and not shift_pressed,
            )
        except IOError:
            traceback.print_exc()


class CompilationError(Indicator):
    """Underline python code resulting in compilation errors."""

    styling = IndicatorStyling(
        style=QsciScintilla.INDIC_SQUIGGLE,
        hover_fore=QColor("#cc0000"),
    )

    def on_left_click(self, line: int, index: int, ctrl_pressed=False, shift_pressed=False) -> None:
        position = self.editor.positionFromLineIndex(line, index)
        self.editor.SendScintilla(
            QsciScintilla.SCI_CALLTIPSHOW, position, self.editor._last_error_message.encode("utf8")
        )


class ValidStudentsPath(Indicator):
    """Indicator for the path of CSV file containing all students IDs."""

    styling = IndicatorStyling(
        style=QsciScintilla.INDIC_DOTBOX,
        hover_fore=QColor("#67d0eb"),
        hover_style=QsciScintilla.INDIC_FULLBOX,
    )

    def on_left_click(self, line: int, index: int, ctrl_pressed=False, shift_pressed=False) -> None:
        if shift_pressed:
            if self.editor.student_ids_path is not None and self.editor.student_ids_path.is_file():
                self.editor.main_window.file_events_handler.open_doc(paths=[self.editor.student_ids_path])
        else:
            self.editor.selectStudentsIdsFile()


class WrongStudentsPath(Indicator):
    styling = IndicatorStyling(
        style=QsciScintilla.INDIC_TEXTFORE,
        fore=QColor("#dc143c"),
        hover_style=QsciScintilla.INDIC_BOX,
    )

    def on_left_click(self, line: int, index: int, ctrl_pressed=False, shift_pressed=False) -> None:
        if shift_pressed:
            if self.editor.student_ids_path is not None and self.editor.student_ids_path.is_file():
                self.editor.main_window.file_events_handler.open_doc(paths=[self.editor.student_ids_path])
        else:
            self.editor.selectStudentsIdsFile()


# class Indicator(Enum):
#     SearchMarker = SearchMarker
#     INCLUDE_DIRECTIVES_ID = 1
#     COMPILATION_ERROR = 2
#     VALID_STUDENTS_IDS_PATH = 3
#     INVALID_STUDENTS_IDS_PATH = 4


class Indicators:
    """A container for all indicators."""

    def __init__(self, editor: "EditorWidget"):
        self.editor = editor
        # Generate all indicators instances.
        # It would be nice to generate them dynamically, but we would lose autocompletion in the editor. :(
        self.search_marker = SearchMarker(editor)
        self.include_directive = IncludeDirective(editor)
        self.compilation_error = CompilationError(editor)
        self.valid_students_path = ValidStudentsPath(editor)
        self.wrong_students_path = WrongStudentsPath(editor)
        # Generate revert search, to be able to find the corresponding Indicator for
        # each
        self.indicators_by_num: dict[int, Indicator] = {}
        for value in self.__dict__.values():
            if isinstance(value, Indicator):
                self.indicators_by_num[value.num] = value

        # Don't use directly QScintilla.indicatorClicked signal to handle indicators,
        # since it leads to an occasional severe bug with a selection
        # anchor impossible to remove (I couldn't figure out why...).
        # However, we have to use it to get key modifiers, since QScintilla.indicatorReleased
        # won't get them.
        self.editor.indicatorClicked.connect(self._save_modifiers)
        self.editor.indicatorReleased.connect(self.on_left_click)

    def __iter__(self) -> Iterator[Indicator]:
        return iter(self.indicators_by_num.values())

    # def find(self, num: int) -> Indicator:
    #     return self._reverse_search[num]

    def _save_modifiers(self, line, _, keys):
        self._modifiers = keys

    # def is_indicator_applied(self, line: int, index: int, *indicators: Indicator) -> bool:
    #     """Test if any of the given indicators is applied at specified line and index."""
    #     position = self.editor.positionFromLineIndex(line, index)
    #     print(position, indicators)
    #     for indicator in indicators:
    #         value = self.editor.SendScintilla(QsciScintilla.SCI_INDICATORVALUEAT, indicator, position)
    #         if value > 0:
    #             return True
    #     return False

    # def is_indicator_at(self, indicator: Indicator, position: int) -> bool:
    #     return self.editor.SendScintilla(QsciScintilla.SCI_INDICATORVALUEAT, indicator.num, position) > 0

    def on_left_click(self, line: int, index: int, keys: Qt.KeyboardModifier) -> None:
        """Action executed when user clicks on a Qscintilla indicator."""
        print("Indicator left-clicked.")
        position = self.editor.positionFromLineIndex(line, index)
        ctrl_pressed = self._modifiers & Qt.KeyboardModifier.ControlModifier
        shift_pressed = self._modifiers & Qt.KeyboardModifier.ShiftModifier
        for indicator in self:
            if indicator.is_present_at(position):
                print(indicator.__class__.__name__, "detected.")
                indicator.on_left_click(
                    line=line, index=index, ctrl_pressed=ctrl_pressed, shift_pressed=shift_pressed
                )

        if shift_pressed:
            # Scintilla select text as a side effect when clicking with shift key pressed.
            self.editor.unselect()
