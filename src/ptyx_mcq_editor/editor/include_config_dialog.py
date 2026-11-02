import sys

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
)

from ptyx_mcq.tools.evaluation_strategies import ScoringStrategy


class ConfigDialog(QDialog):
    def __init__(
        self,
        strategy: ScoringStrategy = ScoringStrategy.CORRECT_MINUS_INCORRECT,
        weight: float = 1.0,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Edit configuration")

        self._strategy_box = QComboBox()
        self._strategy_box.addItem("", userData=None)
        for s in ScoringStrategy:
            self._strategy_box.addItem(str(s), userData=s)  # store the enum member itself
        self._strategy_box.setCurrentIndex(self._strategy_box.findData(strategy))

        self._weight_box = QDoubleSpinBox()
        self._weight_box.setMinimum(0.0)  # positive or zero only
        self._weight_box.setMaximum(1_000_000.0)  # default max is 99.99, so raise it
        self._weight_box.setDecimals(3)
        self._weight_box.setSingleStep(0.1)
        self._weight_box.setValue(weight)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("Evaluation mode:", self._strategy_box)
        layout.addRow("Weight:", self._weight_box)
        layout.addRow(buttons)

    @property
    def strategy(self) -> ScoringStrategy | None:
        return self._strategy_box.currentData()

    @property
    def weight(self) -> float:
        return self._weight_box.value()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = ConfigDialog(ScoringStrategy.CORRECT_MINUS_INCORRECT, 2.5)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        print(dlg.strategy, dlg.weight)
    else:
        print("Cancelled")
