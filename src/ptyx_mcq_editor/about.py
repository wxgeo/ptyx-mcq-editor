import sys
from importlib.metadata import metadata, PackageNotFoundError
from pathlib import Path

from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, Qt
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDialogButtonBox,
)

from ptyx_mcq_editor.param import ICON_PATH, APP_NAME, PACKAGE_NAME

try:
    meta = metadata(PACKAGE_NAME)
    APP_VERSION = meta["Version"]
    PTYX_VERSION = metadata("ptyx")["Version"]
    PTYX_MCQ_VERSION = metadata("ptyx-mcq")["Version"]
except PackageNotFoundError:
    APP_VERSION = "development"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumWidth(450)

        main_layout = QVBoxLayout(self)

        # Content row: info on the left, icon on the right
        content_layout = QHBoxLayout()

        # --- Left: SVG icon, centered vertically and horizontally ---
        icon_layout = QVBoxLayout()
        icon_layout.addStretch()
        if Path(ICON_PATH).exists():
            svg = QSvgWidget(str(ICON_PATH))
            svg.setFixedSize(64, 64)  # adjust to taste
            icon_layout.addWidget(svg, alignment=Qt.AlignmentFlag.AlignHCenter)
        icon_layout.addStretch()

        content_layout.addLayout(icon_layout, stretch=1)

        # --- Right: text info ---
        info_layout = QVBoxLayout()

        title = QLabel(f"<h2>{APP_NAME}</h2>")
        version = QLabel(f"<b>Application version:</b> {APP_VERSION}")
        ptyx_version = QLabel(f"<b>pTyX version:</b> {PTYX_VERSION}")
        ptyx_mcq_version = QLabel(f"<b>pTyX-MCQ version:</b> {PTYX_MCQ_VERSION}")
        pyqt = QLabel(f"<b>PyQt version:</b> {PYQT_VERSION_STR}")
        qt = QLabel(f"<b>Qt version:</b> {QT_VERSION_STR}")
        python = QLabel(
            f"<b>Python version:</b> "
            f"{sys.version_info.major}."
            f"{sys.version_info.minor}."
            f"{sys.version_info.micro}"
        )

        info_layout.addWidget(title)
        info_layout.addWidget(version)
        info_layout.addSpacing(10)
        info_layout.addWidget(ptyx_mcq_version)
        info_layout.addWidget(ptyx_version)
        info_layout.addWidget(pyqt)
        info_layout.addWidget(qt)
        info_layout.addWidget(python)
        info_layout.addStretch()

        content_layout.addLayout(info_layout, stretch=2)

        main_layout.addLayout(content_layout)

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        main_layout.addSpacing(15)
        main_layout.addWidget(buttons)
