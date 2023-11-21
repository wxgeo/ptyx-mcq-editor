#!/usr/bin/python3
import signal
import sys
from functools import partial
from types import TracebackType
from typing import Type

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from ptyx_mcq_editor.main_window import ICON_PATH, McqEditorMainWindow

from ptyx_mcq_editor.signal_wake_up import SignalWakeupHandler


def my_excepthook(
    type_: Type[BaseException],
    value: BaseException,
    traceback: TracebackType | None,
    window: QMainWindow = None,
) -> None:
    # log the exception here
    QMessageBox.critical(window, "Something went wrong!", f"{type(value).__name__}: {value}")
    # then call the default handler
    sys.__excepthook__(type_, value, traceback)


def main() -> None:
    try:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(str(ICON_PATH)))
        # Used to handle Ctrl+C
        # https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
        SignalWakeupHandler(app)
        main_window = McqEditorMainWindow()
        # Don't close pyQt application on failure.
        sys.excepthook = partial(my_excepthook, window=main_window)
        # Used to handle Ctrl+C
        signal.signal(signal.SIGINT, lambda sig, _: app.quit())
        main_window.show()
        return_code = app.exec()
    except BaseException as e:
        raise e
    sys.exit(return_code)


# TODO: support for arguments (file to open)
if __name__ == "__main__":
    main()
