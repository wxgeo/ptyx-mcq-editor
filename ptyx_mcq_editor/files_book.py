from PyQt6 import QtWidgets


class FilesBook(QtWidgets.QTabWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setDocumentMode(True)
        self.setTabBarAutoHide(True)
        self.setTabsClosable(True)
        self.setMovable(True)

        self.tabCloseRequested.connect(self.close_tab)

    def close_tab(self, index: int) -> None:
        print(f"closing tab {index}")
        widget = self.widget(index)
        if widget is not None and widget.close():
            self.removeTab(index)
            widget.destroy()
