from PySide6.QtCore import (
    Qt, QCoreApplication, Signal as pyqtSignal, QSize, QRectF,
    QPropertyAnimation, QEasingCurve, Property, QEvent,
)
from PySide6.QtGui import QPainter, QColor, QIcon
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSizePolicy, QDialog, QDialogButtonBox, QLineEdit, QSpinBox,
    QDoubleSpinBox, QVBoxLayout, QScrollArea, QButtonGroup, QToolButton,
)

from src.gui.theme import t, ColorThemeManager, theme_pixmap
from src.gui.widgets import (
    IOSSearchField,
    IOSSegmentedFilter,
    IOSSearchEmpty,
    IOSSectionHeader,
    IOSCard,
    IOSCollapsibleSection,
    IOSNavBar,
    IOSValueRow,
    IOSSettingsRow,
    IOSSettingsAction,
    IOSPrimaryButton,
    IOSDangerButton,
    IOSSwitch,
    _auto_retheme,
)



class TextInputDialog(QDialog):
    """iOS-style text input dialog."""
    def __init__(self, title: str, current_value: str = "", parent=None):
        super().__init__(parent)
        ColorThemeManager.instance().theme_changed.connect(self._retheme)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(320)
        self._retheme()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        self.input = QLineEdit()
        self.input.setText(current_value)
        self.input.setAccessibleName(title)
        self.input.setPlaceholderText(QCoreApplication.translate("TextInputDialog", "Enter value..."))
        layout.addWidget(self.input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet(t("text_input_dialog"))
        layout.addWidget(buttons)

    def _retheme(self):
        self.setStyleSheet(t("text_input_dialog"))

    def showEvent(self, event):
        super().showEvent(event)
        self.input.setFocus(Qt.OtherFocusReason)

    def get_value(self) -> str:
        return self.input.text()


def decimals_for_step(step) -> int:
    """Decimal places needed to express ``step`` (0.5 -> 1, 1 -> 0, 0.25 -> 2)."""
    try:
        text = f"{float(step):.6f}".rstrip("0")
    except (TypeError, ValueError):
        return 0
    if text.endswith("."):
        return 0
    return len(text.split(".", 1)[1])


class NumberInputDialog(QDialog):
    """iOS-style number input dialog.

    ``step`` picks the widget: an integral step keeps the integer spin box
    (every existing numeric tweak), a finer one switches to a decimal box so
    values like 0.5 are expressible. ``get_value`` returns an int in the
    integral case and a float otherwise.
    """
    def __init__(self, title: str, current_value: int = 0, min_val: int = 0, max_val: int = 999,
                 parent=None, step: float = 1.0):
        super().__init__(parent)
        ColorThemeManager.instance().theme_changed.connect(self._retheme)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(320)
        self._retheme()

        self._decimals = decimals_for_step(step)
        self._integral = self._decimals == 0

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        if self._integral:
            self.spin = QSpinBox()
            self.spin.setRange(int(min_val), int(max_val))
            self.spin.setValue(int(current_value))
            self.spin.setButtonSymbols(QSpinBox.NoButtons)
        else:
            self.spin = QDoubleSpinBox()
            self.spin.setDecimals(self._decimals)
            self.spin.setSingleStep(abs(float(step)))
            self.spin.setRange(float(min_val), float(max_val))
            self.spin.setValue(float(current_value))
            self.spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.spin.setStyleSheet(t('number_input_field'))
        layout.addWidget(self.spin)
        if not self._integral:
            hint = QLabel(QCoreApplication.translate("Nugget", "Range: {0} – {1} · Step: {2}").format(
                self.spin.locale().toString(float(min_val), 'f', self._decimals),
                self.spin.locale().toString(float(max_val), 'f', self._decimals),
                self.spin.locale().toString(float(step), 'f', self._decimals)))
            hint.setWordWrap(True)
            hint.setStyleSheet(t("home_subtitle"))
            layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _retheme(self):
        self.setStyleSheet(t('number_input_dialog'))
        if hasattr(self, 'spin'):
            self.spin.setStyleSheet(t('number_input_field'))

    def showEvent(self, event):
        super().showEvent(event)
        self.spin.setFocus(Qt.OtherFocusReason)
        self.spin.selectAll()

    def get_value(self):
        self.spin.interpretText()
        value = self.spin.value()
        return int(value) if self._integral else round(float(value), self._decimals)


class IOSSummaryDialog(QDialog):
    """iOS-style confirm dialog listing what an action will do.

    Built for the pre-apply summary: takes a title, a list of ``lines`` and an
    optional muted footer note, then offers Cancel / a themed confirm button.
    ``exec()`` returns ``QDialog.Accepted`` when the user confirms.

    An optional ``extra_button`` (e.g. "Update Cache") renders as an
    additional themed button that returns ``extra_result`` (default 2) so the
    caller can branch on it without closing with a plain confirm.
    """
    def __init__(self, title: str, lines: list[str], muted: str = "",
                 confirm_text: str = "", extra_button: str = "",
                 extra_result: int = 2, parent=None, details_callback=None,
                 header_widget=None, acknowledge_text: str = "", preview_callback=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setMinimumHeight(140)
        _auto_retheme(self)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        title_lbl = QLabel(title, self)
        title_lbl.setObjectName("confirmTitle")
        title_lbl.setWordWrap(True)
        header = QHBoxLayout()
        self._summary_icon = QLabel(self)
        self._summary_icon.setFixedSize(36, 36)
        header.addWidget(self._summary_icon)
        header.addWidget(title_lbl, 1)
        layout.addLayout(header)
        if header_widget is not None:
            header_widget.setParent(self)
            layout.addWidget(header_widget)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        summary = IOSCard()
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(12)
        for line in lines:
            row_lbl = QLabel(line, self)
            row_lbl.setObjectName("confirmRow")
            row_lbl.setWordWrap(True)
            summary_layout.addWidget(row_lbl)
        scroll.setWidget(summary)
        scroll.setMinimumHeight(140)
        scroll.setMaximumHeight(320)
        layout.addWidget(scroll, 1)

        if muted:
            muted_lbl = QLabel(muted, self)
            muted_lbl.setObjectName("confirmMuted")
            muted_lbl.setWordWrap(True)
            layout.addWidget(muted_lbl)

        layout.addStretch()

        secondary = QHBoxLayout()
        secondary.setSpacing(12)
        for text, callback in ((QCoreApplication.translate("ApplyPreview", "View changes"), details_callback),
                               (QCoreApplication.translate("DeviceTwin", "Preview on iPhone"), preview_callback)):
            if callback is None:
                continue
            button = QPushButton(text, self)
            button.setObjectName("cancelBtn")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, cb=callback: cb(self))
            secondary.addWidget(button)
        if secondary.count():
            layout.addLayout(secondary)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        if extra_button:
            extra_btn = QPushButton(extra_button, self)
            extra_btn.setObjectName("cancelBtn")
            extra_btn.setCursor(Qt.PointingHandCursor)
            extra_btn.clicked.connect(lambda: self.done(extra_result))
            buttons.addWidget(extra_btn)
        cancel_btn = QPushButton(QCoreApplication.translate("IOSSummaryDialog", "Cancel"), self)
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        self.confirm_btn = QPushButton(
            confirm_text or QCoreApplication.translate("IOSSummaryDialog", "Confirm"), self)
        self.confirm_btn.setObjectName("confirmBtn")
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.clicked.connect(self.accept)
        self.confirm_btn.setDefault(True)
        buttons.addWidget(self.confirm_btn)
        # A checkbox the user must tick before confirming (e.g. high risk).
        self.acknowledge = None
        if acknowledge_text:
            from PySide6.QtWidgets import QCheckBox
            self.acknowledge = QCheckBox(acknowledge_text, self)
            self.confirm_btn.setEnabled(False)
            self.confirm_btn.setDefault(False)
            cancel_btn.setDefault(True)
            self.acknowledge.toggled.connect(self.confirm_btn.setEnabled)
            layout.addWidget(self.acknowledge)
        layout.addLayout(buttons)
        for button in self.findChildren(QPushButton):
            button.setMinimumHeight(48)
        self._retheme()

    def _retheme(self):
        self.setStyleSheet(t("confirm_dialog") + t("summary_dialog"))
        from src.gui.ios.feature_icons import FEATURE_ICONS
        self._summary_icon.setPixmap(theme_pixmap(
            FEATURE_ICONS["Tweaks"], ColorThemeManager.instance().colors.text_primary,
            36, self.devicePixelRatioF()))
