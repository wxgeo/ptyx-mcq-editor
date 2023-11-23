from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    from ptyx_mcq_editor.main_window import McqEditorMainWindow


class EnhancedWidget(QWidget):
    def get_main_window(self) -> "McqEditorMainWindow":
        from ptyx_mcq_editor.main_window import McqEditorMainWindow

        widget = self
        while widget.parent() is not None:
            widget = widget.parent()
        assert isinstance(widget, McqEditorMainWindow), widget
        return widget
