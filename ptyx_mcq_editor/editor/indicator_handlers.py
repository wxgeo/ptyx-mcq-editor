"""
This module defines static classes providing specific indicators data and methods.
"""

from abc import ABC
from dataclasses import dataclass, asdict
from enum import Enum
from typing import ClassVar, TYPE_CHECKING, TypedDict

from PyQt6.Qsci import QsciScintilla
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


class Indicators:
    """All indicators' handlers.

    This namespace will be automatically populated when creating a new indicator handler,
    i.e. a subclass of `IndicatorHandler`.
    """


class IndicatorHandler(ABC):
    """
    Base (abstract) class for each QScintilla indicator.

    Each subclass must be instantiated only once.
    """

    # This counter will be automatically incremented at each subclass creation.
    _subclass_counter: ClassVar[int] = 0
    # Unique identifier for each indicator, required by QScintilla.
    # It will be automatically set at subclass creation.
    indicator_num: ClassVar[int] = -1

    # Each class must be instantiated only once.
    _already_instantiated = False

    # Must be redefined in subclasses.
    styling: ClassVar[IndicatorStyling]

    def __init_subclass__(cls, **kwargs):
        cls.id = IndicatorHandler._subclass_counter
        IndicatorHandler._subclass_counter += 1
        setattr(Indicators, cls.__name__, cls)

    def __new__(cls, *args, **kwargs):
        if cls._already_instantiated:
            raise RuntimeError("Classes inheriting from `IndicatorHandler` must be instantiated only once!")
        cls._already_instantiated = True
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, editor: "EditorWidget"):
        self.editor = editor
        for property_name, property_value in asdict(self.styling).items():
            if property_value is not None:
                sci_code = getattr(QsciScintilla, "SCI_INDICSET" + property_name.upper().replace("_", ""))
                # Apply indicator style.
                self.editor.SendScintilla(sci_code, self.indicator_num, property_value)

    def on_left_click(self) -> None:
        pass

    def on_right_click(self) -> None:
        pass


class SearchMarker(IndicatorHandler):
    styling = IndicatorStyling(
        style=QsciScintilla.INDIC_FULLBOX,
        fore=QColor("#67d0eb"),
        alpha=100,
        outline_alpha=200,
    )


class IncludeDirective(IndicatorHandler):
    styling = IndicatorStyling(
        style=QsciScintilla.INDIC_DOTBOX,
        hover_fore=QColor("#67d0eb"),
        hover_style=QsciScintilla.IndicatorStyle.FullBoxIndicator,
    )


class CompilationError(IndicatorHandler):
    styling = IndicatorStyling(
        style=QsciScintilla.INDIC_SQUIGGLE,
        hover_fore=QColor("#cc0000"),
    )


class ValidStudentsPath(IndicatorHandler):
    styling = IndicatorStyling(
        style=QsciScintilla.INDIC_DOTBOX,
        hover_fore=QColor("#67d0eb"),
        hover_style=QsciScintilla.INDIC_FULLBOX,
    )


class WrongStudentsPath(IndicatorHandler):
    styling = IndicatorStyling(
        style=QsciScintilla.INDIC_TEXTFORE,
        fore=QColor("#dc143c"),
        hover_style=QsciScintilla.INDIC_BOX,
    )


class Indicator(Enum):
    SearchMarker = SearchMarker
    INCLUDE_DIRECTIVES_ID = 1
    COMPILATION_ERROR = 2
    VALID_STUDENTS_IDS_PATH = 3
    INVALID_STUDENTS_IDS_PATH = 4
