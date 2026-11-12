import functools
from typing import Any, Callable

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QWidget


class _Worker(QThread):
    succeeded = pyqtSignal()
    failed = pyqtSignal(object)

    def __init__(self, func: Callable[[], Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._func = func

    def run(self) -> None:
        try:
            self._func()
        except Exception as e:
            self.failed.emit(e)
        else:
            self.succeeded.emit()


# class _BusyDialog(QProgressDialog):
#     def keyPressEvent(self, event: QKeyEvent | None) -> None:
#         if event is not None:
#             event.ignore()  # swallow Esc


def run_with_progress(
    title: str = "Please wait",
    label: str = "Working…",
    success_message: str | None = "Done.",
):
    """Run the decorated method in a thread, with a busy dialog.

    Calls made while it is still running are silently ignored.
    The decorated method runs outside the GUI thread: it must not touch widgets.
    """

    def decorator(method: Callable[..., Any]) -> Callable[..., None]:
        running: set[int] = set()  # ids of the instances currently running the method

        @functools.wraps(method)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> None:
            key = id(self)
            if key in running:
                return
            running.add(key)
            main_window = self.main_window
            dialog = QProgressDialog(label, "", 0, 0, main_window)  # range (0, 0) => busy indicator
            dialog.setWindowTitle(title)
            dialog.setCancelButton(None)  # type: ignore[arg-type]
            dialog.setWindowModality(Qt.WindowModality.WindowModal)
            dialog.setMinimumDuration(0)
            dialog.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
            dialog.show()

            def cleanup() -> None:
                dialog.hide()
                dialog.deleteLater()
                running.discard(key)

            def done_ok() -> None:
                cleanup()
                if success_message:
                    QMessageBox.information(main_window, title, success_message)

            def done_err(error: Exception) -> None:
                cleanup()
                QMessageBox.critical(main_window, title, f"Operation failed:\n{error}")
                raise error

            worker = _Worker(lambda: method(self, *args, **kwargs), main_window)
            worker.succeeded.connect(done_ok)
            worker.failed.connect(done_err)
            worker.finished.connect(worker.deleteLater)
            worker.start()

        return wrapper

    return decorator
