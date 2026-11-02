import inspect

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QToolButton,
    QWidget,
    QTextEdit,
)

from ptyx_mcq.tools.evaluation_strategies import (
    ScoringImplementations,
    ScoringStrategy,
    DEFAULT_SCORING_STRATEGY,
)


def strategy_help(strategy: ScoringStrategy | None) -> str:
    """Return the (dedented) docstring of the method implementing `strategy`."""
    if strategy is None:
        return "Use the global scoring strategy, defined in the header of the `.ptyx` file."
    elif strategy is ScoringStrategy.SKIP:
        return (
            "Ignore the question (alternatively, you can set the weight to zero)."
            "\nThis is useful to neutralize a faulty question."
        )
    method = getattr(ScoringImplementations, str(strategy), None)
    return inspect.getdoc(method) or "" if method is not None else ""


class ConfigDialog(QDialog):
    def __init__(
        self,
        strategy: ScoringStrategy = DEFAULT_SCORING_STRATEGY,
        weight: float = 1.0,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Edit configuration")

        self._strategy_box = QComboBox()
        self._strategy_box.addItem("", userData=None)
        for s in ScoringStrategy:
            self._strategy_box.addItem(
                str(s) + (" (recommended)" if s is DEFAULT_SCORING_STRATEGY else ""), userData=s
            )  # store the enum member itself
        self._strategy_box.setCurrentIndex(self._strategy_box.findData(strategy))

        # Help toggle button, placed right next to the combo box
        self._help_button = QToolButton()
        self._help_button.setText("?")
        self._help_button.setCheckable(True)
        self._help_button.setToolTip("Show/hide help about the selected evaluation mode")
        self._help_button.toggled.connect(self._toggle_help)

        combo_row = QWidget()
        combo_layout = QHBoxLayout(combo_row)
        combo_layout.setContentsMargins(0, 0, 0, 0)
        combo_layout.addWidget(self._strategy_box, stretch=1)
        combo_layout.addWidget(self._help_button)

        # Help panel: persistent, scrollable, read-only
        self._help_view = QTextEdit()
        self._help_view.setReadOnly(True)
        self._help_view.setMinimumHeight(120)
        self._help_view.hide()

        self._strategy_box.currentIndexChanged.connect(self._update_help)

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
        layout.addRow("Evaluation mode:", combo_row)
        layout.addRow(self._help_view)  # spans the full width
        layout.addRow("Weight:", self._weight_box)
        layout.addRow(buttons)

        self._update_help()
        self.resize(600, self.sizeHint().height())

    # ---- help handling -------------------------------------------------

    def _update_help(self) -> None:
        text = strategy_help(self.strategy)
        self._help_view.setMarkdown(text)
        has_help = bool(text)
        self._help_button.setEnabled(has_help)
        if not has_help:
            # Empty selection (or no docstring): close the panel
            self._help_button.setChecked(False)

    def _toggle_help(self, visible: bool) -> None:
        self._help_view.setVisible(visible)
        # keep the current width (whatever the user chose), adapt only the height
        self.resize(self.width(), self.sizeHint().height())

    # ---- public API ----------------------------------------------------

    @property
    def strategy(self) -> ScoringStrategy | None:
        return self._strategy_box.currentData()

    @property
    def weight(self) -> float:
        return self._weight_box.value()
