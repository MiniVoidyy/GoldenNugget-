from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QScrollArea, QWidget


class ViewportRows(QObject):
    def __init__(self, content):
        super().__init__(content)
        self._content = content
        self._rows = []
        self._scroll = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._refresh)
        content.installEventFilter(self)

    def wrap(self, card):
        row = _ViewportRow(card, self)
        self._rows.append(row)
        return row

    def clear(self):
        self._timer.stop()
        self._rows.clear()

    def request(self, *_args):
        if not self._timer.isActive():
            self._timer.start(0)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Show, QEvent.Type.Hide, QEvent.Type.Resize):
            self.request()
        return False

    def _refresh(self):
        if self._scroll is None:
            parent = self._content.parentWidget()
            while parent is not None and not isinstance(parent, QScrollArea):
                parent = parent.parentWidget()
            if parent is None:
                return
            self._scroll = parent
            parent.verticalScrollBar().valueChanged.connect(self.request)
            parent.viewport().installEventFilter(self)
        viewport = self._scroll.viewport()
        visible = viewport.rect().adjusted(0, -160, 0, 160)
        for row in self._rows:
            shown = row.isVisibleTo(self._content) and self._content.isVisible()
            if shown:
                position = row.mapTo(viewport, row.rect().topLeft())
                shown = visible.intersects(row.rect().translated(position))
            row.display(shown)


class _ViewportRow(QWidget):
    def __init__(self, card, controller):
        super().__init__()
        self._card = card
        self._controller = controller
        for key in ("searchText", "sortTitle", "categoryTitle"):
            value = card.property(key)
            if isinstance(value, str):
                self.setProperty(key, value)
        self.setToolTip(card.toolTip())
        self.setAccessibleDescription(card.accessibleDescription())
        self.setFixedHeight(max(76, card.sizeHint().height()))
        card.setParent(self)
        card.hide()

    def showEvent(self, event):
        super().showEvent(event)
        self._controller.request()

    def hideEvent(self, event):
        self._card.hide()
        super().hideEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._card.isVisible():
            self._fit()
        self._controller.request()

    def _fit(self):
        layout = self._card.layout()
        height = layout.totalHeightForWidth(self.width()) if layout is not None else -1
        height = max(76, height, self._card.minimumSizeHint().height())
        if self.minimumHeight() != height:
            self.setFixedHeight(height)
        self._card.setGeometry(0, 0, self.width(), height)

    def display(self, shown):
        if shown:
            self._fit()
            if self._card.isHidden():
                self._card.show()
        elif not self._card.isHidden():
            self._card.hide()
