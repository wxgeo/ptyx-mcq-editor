from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QTextOption, QKeyEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit


class Tooltip(QWidget):
    """A persistent tooltip-like popup for displaying contextual help in the editor.
    Closes on Escape or click outside.
    """

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setFrameStyle(0)
        self._text.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        layout.addWidget(self._text)

        # Match QToolTip appearance
        self.setStyleSheet("""
            QWidget { background: #ffffdc; border: 1px solid #aaaaaa; }
            QTextEdit { background: #ffffdc; }
        """)

    def show_at(self, global_pos: QPoint, content: str, as_html: bool = False) -> None:
        if as_html:
            self._text.setHtml(content)
        else:
            self._text.setText(content)
        # Size to content
        doc = self._text.document()
        assert doc is not None
        doc.setTextWidth(500)
        self.resize(int(doc.size().width()) + 16, int(doc.size().height()) + 16)
        self.move(global_pos)
        self.show()

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event and event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    # def mousePressEvent(self, event) -> None:
    #     self.hide()
