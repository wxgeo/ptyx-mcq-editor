import sys
import traceback
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
    QStyle,
)
from PyQt6.QtCore import Qt


class ErrorDialog(QDialog):
    def __init__(
        self,
        title: str = "An error occurred",
        message: str = "Something went wrong.",
        detail: str = "",
        parent=None,
        default_width=600,
    ):
        super().__init__(parent)
        self.detail_text = detail
        self.details_visible = False

        self._build_ui(message)
        self.setWindowTitle(title)
        self.default_width = default_width
        # self.setMinimumWidth(480)
        # self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._resize()

    def _resize(self) -> None:
        # print(self.sizeHint().height())
        # self.resize(self.default_width, self.sizeHint().height())

        # Let Qt recalculate the layout and resize the window
        self.body.resize(self.default_width, self.body.sizeHint().height())
        self.resize(self.default_width, self.body.sizeHint().height())

    # ------------------------------------------------------------------ #
    #  UI construction                                                     #
    # ------------------------------------------------------------------ #
    def _build_ui(self, message: str) -> None:
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical))
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Body ────────────────────────────────────────────────────────
        self.body = body = QFrame()
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(20, 18, 20, 18)
        b_layout.setSpacing(14)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        b_layout.addWidget(msg_label)

        # ── Details toggle ──────────────────────────────────────────────
        self.details_btn = QPushButton("▶  Details")
        self.details_btn.setCheckable(True)
        self.details_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.details_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                text-align: left;
                padding: 0px;
                font-weight: bold;
            }
            QPushButton:hover { color: #ff8a80; }
        """)
        self.details_btn.clicked.connect(self._toggle_details)
        b_layout.addWidget(self.details_btn)

        # ── Traceback box (hidden by default) ───────────────────────────
        self.traceback_box = QTextEdit()
        self.traceback_box.setReadOnly(True)
        self.traceback_box.setPlainText(self.detail_text)
        self.traceback_box.setMaximumHeight(220)
        self.traceback_box.setStyleSheet("""
            QTextEdit {
                border: 1px solid #444;
                border-radius: 4px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.traceback_box.hide()
        b_layout.addWidget(self.traceback_box)

        b_layout.addStretch()  # ← push everything up, absorbs leftover space

        # ── Close button ────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        b_layout.addLayout(btn_row)

        root.addWidget(body)

    # ------------------------------------------------------------------ #
    #  Toggle details                                                      #
    # ------------------------------------------------------------------ #
    def _toggle_details(self) -> None:
        self.details_visible = not self.details_visible

        if self.details_visible:
            self.details_btn.setText("▼  Details")
            # self.traceback_box.setFixedHeight(220)
            self.traceback_box.show()
        else:
            self.details_btn.setText("▶  Details")
            # self.traceback_box.setFixedHeight(0)
            self.traceback_box.hide()
        self._resize()


# ------------------------------------------------------------------ #
#  Demo                                                               #
# ------------------------------------------------------------------ #
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Generate a realistic traceback string
    try:
        _ = 1 / 0
    except ZeroDivisionError:
        tb = traceback.format_exc()

    dlg = ErrorDialog(
        title="Unhandled Exception",
        message="ZeroDivisionError: division by zero\n\nThe application encountered an unexpected error and could not continue.",
        detail=tb,
    )
    dlg.exec()


if __name__ == "__main__":
    main()
