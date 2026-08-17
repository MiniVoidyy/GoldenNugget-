from PySide6.QtCore import Qt, QSize, QCoreApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QPushButton, QScrollArea, QToolButton, QStackedWidget, QSizePolicy,
    QCheckBox, QComboBox
)
from PySide6.QtGui import QPixmap, QIcon

from src.gui.ios.components import IOSNavBar, IOSCard, IOSPrimaryButton, IOSSettingsRow, IOSSwitch
from src.tweaks.tweaks import tweaks, TweakID
from src.qt.mainwindow_ui import Ui_Nugget


class TemplatePreviewCard(QLabel):
    """Clickable preview image that can show full size"""
    def __init__(self, pixmap: QPixmap, preview_name: str, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(200, 200)
        self.setStyleSheet(
            "QLabel { background-color: #1C1C1E; border-radius: 12px; border: 1px solid #3A3A3C; }"
        )
        self._original_pixmap = pixmap
        self._preview_name = preview_name
        self.setPixmap(pixmap.scaled(190, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def mousePressEvent(self, event):
        # Could open full-size preview dialog here
        pass


class IOSPosterboardPage(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setObjectName("iosContainer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Nav bar with add tendies button
        nav = IOSNavBar(
            QCoreApplication.translate("IOSPosterboardPage", "PosterBoard"),
            window=self.window,
            right_action=(QCoreApplication.translate("IOSPosterboardPage", "+ Add Tendies"), self.show_add_tendies_dialog)
        )
        layout.addWidget(nav)

        # Tab bar
        self.tab_stack = QStackedWidget()
        layout.addWidget(self.tab_stack)

        # Tendies tab
        self.tendies_page = self._create_tendies_tab()
        self.tab_stack.addWidget(self.tendies_page)

        # Templates tab
        self.templates_page = self._create_templates_tab()
        self.tab_stack.addWidget(self.templates_page)

        # Video tab
        self.video_page = self._create_video_tab()
        self.tab_stack.addWidget(self.video_page)

        # Bottom tab bar
        tab_bar = QWidget()
        tab_bar.setFixedHeight(56)
        tab_bar.setStyleSheet("background-color: #1e1e1e; border-top: 1px solid #1C1C1E;")
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)

        self.tendies_tab_btn = self._make_tab_button(QCoreApplication.translate("IOSPosterboardPage", "Tendies"), ":/icon/wallpaper.svg", 0)
        self.templates_tab_btn = self._make_tab_button(QCoreApplication.translate("Nugget", "Templates"), ":/icon/photo-stack.svg", 1)
        self.video_tab_btn = self._make_tab_button(QCoreApplication.translate("IOSPosterboardPage", "Video"), ":/icon/play-circle.svg", 2)

        tab_layout.addWidget(self.tendies_tab_btn, 1)
        tab_layout.addWidget(self.templates_tab_btn, 1)
        tab_layout.addWidget(self.video_tab_btn, 1)

        layout.addWidget(tab_bar)

        # Set initial tab
        self._switch_tab(0)

        # Load existing tendies
        self.refresh_tendies()

    def _make_tab_button(self, text: str, icon_path: str, index: int) -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        btn.setIconSize(QSize(24, 24))
        from PySide6.QtGui import QIcon
        btn.setIcon(QIcon(icon_path))
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                color: #8E8E93;
                font-size: 11px;
                padding: 8px 0;
                border: none;
            }
            QToolButton:checked {
                color: #007AFF;
            }
        """)
        btn.clicked.connect(lambda: self._switch_tab(index))
        return btn

    def _switch_tab(self, index: int):
        self.tab_stack.setCurrentIndex(index)
        self.tendies_tab_btn.setChecked(index == 0)
        self.templates_tab_btn.setChecked(index == 1)
        self.video_tab_btn.setChecked(index == 2)

    def _create_tendies_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1e1e1e; border: none;")
        content = QWidget()
        scroll.setWidget(content)

        self.tendies_grid = QGridLayout(content)
        self.tendies_grid.setContentsMargins(16, 16, 16, 32)
        self.tendies_grid.setSpacing(12)
        self.tendies_grid.setAlignment(Qt.AlignTop)

        # Add tendies button as first item if no tendies
        self.add_tendies_card = self._create_add_tendies_card()
        self.tendies_grid.addWidget(self.add_tendies_card, 0, 0)

        return scroll

    def _create_add_tendies_card(self) -> QWidget:
        card = IOSCard()
        card.setFixedSize(140, 160)
        card.setCursor(Qt.PointingHandCursor)
        card.mousePressEvent = lambda e: self.show_add_tendies_dialog()

        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 16, 16, 16)
        inner.setSpacing(12)
        inner.setAlignment(Qt.AlignCenter)

        plus_icon = QLabel()
        plus_icon.setFixedSize(64, 64)
        plus_icon.setAlignment(Qt.AlignCenter)
        plus_icon.setStyleSheet(
            "QLabel { background-color: #1C1C1E; border-radius: 12px; border: 2px dashed #3A3A3C; }"
        )
        plus_icon.setText("+")
        plus_icon.setStyleSheet(plus_icon.styleSheet() + "font-size: 36px; color: #007AFF;")
        inner.addWidget(plus_icon, 0, Qt.AlignCenter)

        label = QLabel(QCoreApplication.translate("Nugget", "  Import Files (.tendies)"))
        label.setStyleSheet("font-size: 14px; color: #8E8E93; text-align: center;")
        label.setAlignment(Qt.AlignCenter)
        inner.addWidget(label)

        return card

    def _create_templates_tab(self) -> QWidget:
        """Port of classic templates page - uses template.create_ui() for full functionality"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1e1e1e; border: none;")
        scroll.setFrameStyle(QScrollArea.NoFrame)
        
        content = QWidget()
        self.templates_layout = QVBoxLayout(content)
        self.templates_layout.setContentsMargins(16, 16, 16, 32)
        self.templates_layout.setSpacing(12)
        self.templates_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(content)

        # Import button (classic style)
        import_btn = IOSPrimaryButton(QCoreApplication.translate("Nugget", "  Import Templates (.batter)"))
        import_btn.clicked.connect(self.show_add_templates_dialog)
        self.templates_import_btn = import_btn
        self.templates_layout.addWidget(import_btn)

        self.templates_placeholder = QLabel(QCoreApplication.translate("IOSPosterboardPage", "No templates added yet"))
        self.templates_placeholder.setStyleSheet("font-size: 15px; color: #8E8E93;")
        self.templates_placeholder.setAlignment(Qt.AlignCenter)
        self.templates_layout.addWidget(self.templates_placeholder)

        # Load existing templates using classic create_ui()
        self._load_templates_list()

        return scroll

    def show_add_templates_dialog(self):
        """Port of classic on_importTemplatesBtn_clicked"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        selected_files, _ = QFileDialog.getOpenFileNames(
            self.window, QCoreApplication.translate("IOSPosterboardPage", "Select Nugget Template Files"), "", "Zip Files (*.batter)"
        )
        if selected_files:
            templates_tweak = tweaks[TweakID.Templates]
            try:
                device_version = self.window.device_manager.get_current_device_version()
            except Exception:
                device_version = None
            for file in selected_files:
                try:
                    templates_tweak.add_template(file, device_version)
                except Exception as e:
                    QMessageBox.warning(self.window, "Import Failed", f"Failed to load template:\n{file}\n\n{str(e)}")
            self._load_templates_list()

    def _load_templates_list(self):
        """Port of classic load_templates_list / load_pb_templates - uses template.create_ui()"""
        from src.tweaks.tweaks import tweaks, TweakID
        templates = tweaks[TweakID.Templates].templates
        if not templates:
            self.templates_placeholder.show()
            return
        self.templates_placeholder.hide()

        # Clear existing template widgets (keep import button and placeholder)
        for i in reversed(range(self.templates_layout.count())):
            widget = self.templates_layout.itemAt(i).widget()
            if widget is not None and widget not in (self.templates_placeholder, self.templates_import_btn):
                widget.deleteLater()

        # Classic approach: call template.create_ui() for each template
        # This creates the full UI with previews, pickers, bundle ID, etc.
        widgets = {}
        for template in templates:
            template.create_ui(self.window, tweaks[TweakID.Templates], widgets, self.templates_layout)

    def refresh_templates(self):
        """Refresh templates list (alias for _load_templates_list)"""
        self._load_templates_list()

    def _create_video_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1e1e1e; border: none;")
        content = QWidget()
        scroll.setWidget(content)

        v_layout = QVBoxLayout(content)
        v_layout.setContentsMargins(16, 16, 16, 32)
        v_layout.setSpacing(16)

        # Thumbnail
        thumb_row = QHBoxLayout()
        thumb_label = QLabel(QCoreApplication.translate("IOSPosterboardPage", "Thumbnail"))
        thumb_label.setStyleSheet("font-size: 15px; color: #FFFFFF; min-width: 100px;")
        self.thumb_btn = QPushButton(QCoreApplication.translate("Nugget", "Choose Freeze Frame (.HEIC)"))
        self.thumb_btn.setCursor(Qt.PointingHandCursor)
        self.thumb_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1E;
                border-radius: 10px;
                color: #007AFF;
                font-size: 15px;
                padding: 12px 24px;
                border: none;
            }
            QPushButton:hover { background-color: #2C2C2E; }
        """)
        self.thumb_btn.clicked.connect(self.on_choose_thumb_clicked)
        thumb_row.addWidget(thumb_label)
        thumb_row.addWidget(self.thumb_btn, 1)
        v_layout.addLayout(thumb_row)

        # Video
        video_row = QHBoxLayout()
        video_label = QLabel(QCoreApplication.translate("IOSPosterboardPage", "Video"))
        video_label.setStyleSheet("font-size: 15px; color: #FFFFFF; min-width: 100px;")
        self.video_btn = QPushButton(QCoreApplication.translate("Nugget", "Choose Video"))
        self.video_btn.setCursor(Qt.PointingHandCursor)
        self.video_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1E;
                border-radius: 10px;
                color: #007AFF;
                font-size: 15px;
                padding: 12px 24px;
                border: none;
            }
            QPushButton:hover { background-color: #2C2C2E; }
        """)
        self.video_btn.clicked.connect(self.on_choose_video_clicked)
        video_row.addWidget(video_label)
        video_row.addWidget(self.video_btn, 1)
        v_layout.addLayout(video_row)

        # Options
        v_layout.addWidget(QLabel(QCoreApplication.translate("IOSPosterboardPage", "Options")))
        self.loop_chk = QCheckBox(QCoreApplication.translate("Nugget", "Loop (use CoreAnimation method)"))
        self.loop_chk.setStyleSheet("color: #FFFFFF; font-size: 15px;")
        self.loop_chk.setChecked(tweaks[TweakID.PosterBoard].loop_video)
        self.loop_chk.toggled.connect(self.on_loop_toggled)
        v_layout.addWidget(self.loop_chk)

        self.reverse_chk = QCheckBox(QCoreApplication.translate("Nugget", "Reverse on Loop"))
        self.reverse_chk.setStyleSheet("color: #FFFFFF; font-size: 15px;")
        self.reverse_chk.setChecked(tweaks[TweakID.PosterBoard].reverse_video)
        self.reverse_chk.toggled.connect(self.on_reverse_toggled)
        v_layout.addWidget(self.reverse_chk)

        self.foreground_chk = QCheckBox(QCoreApplication.translate("Nugget", "Make Foreground (hides clock)"))
        self.foreground_chk.setStyleSheet("color: #FFFFFF; font-size: 15px;")
        self.foreground_chk.setChecked(tweaks[TweakID.PosterBoard].use_foreground)
        self.foreground_chk.toggled.connect(self.on_foreground_toggled)
        v_layout.addWidget(self.foreground_chk)

        v_layout.addStretch()

        self._update_video_labels()

        return scroll

    def _update_video_labels(self):
        pb = tweaks[TweakID.PosterBoard]
        thumb = pb.videoThumbnail if pb.videoThumbnail else None
        video = pb.videoFile if pb.videoFile else None
        self.thumb_btn.setText(QCoreApplication.translate("Nugget", "Choose Freeze Frame (.HEIC)") if not thumb else thumb)
        self.video_btn.setText(QCoreApplication.translate("Nugget", "Choose Video") if not video else video)
        self.reverse_chk.setVisible(pb.loop_video)
        self.foreground_chk.setVisible(pb.loop_video)

    def on_choose_thumb_clicked(self):
        from PySide6.QtWidgets import QFileDialog
        selected_file, _ = QFileDialog.getOpenFileName(
            self.window, QCoreApplication.translate("IOSPosterboardPage", "Select Image File"), "", "Image Files (*.heic)"
        )
        pb = tweaks[TweakID.PosterBoard]
        if selected_file:
            pb.videoThumbnail = selected_file
        else:
            pb.videoThumbnail = None
        self._update_video_labels()

    def on_choose_video_clicked(self):
        from PySide6.QtWidgets import QFileDialog
        selected_file, _ = QFileDialog.getOpenFileName(
            self.window, QCoreApplication.translate("IOSPosterboardPage", "Select Video File"), "", "Video Files (*.mov *.mp4 *.mkv)"
        )
        pb = tweaks[TweakID.PosterBoard]
        if selected_file:
            pb.videoFile = selected_file
        else:
            pb.videoFile = None
        self._update_video_labels()

    def on_loop_toggled(self, checked: bool):
        tweaks[TweakID.PosterBoard].loop_video = checked
        self.reverse_chk.setVisible(checked)
        self.foreground_chk.setVisible(checked)

    def on_reverse_toggled(self, checked: bool):
        tweaks[TweakID.PosterBoard].reverse_video = checked

    def on_foreground_toggled(self, checked: bool):
        tweaks[TweakID.PosterBoard].use_foreground = checked

    def show_add_tendies_dialog(self):
        from PySide6.QtWidgets import QFileDialog
        selected_files, _ = QFileDialog.getOpenFileNames(
            self.window, QCoreApplication.translate("IOSPosterboardPage", "Select PosterBoard Files"), "", "Zip Files (*.tendies)"
        )
        if selected_files:
            for file in selected_files:
                if not tweaks[TweakID.PosterBoard].add_tendie(file):
                    break
            self.refresh_tendies()

    def refresh_tendies(self):
        # Clear existing grid except add card
        for i in reversed(range(self.tendies_grid.count())):
            widget = self.tendies_grid.itemAt(i).widget()
            if widget and widget != self.add_tendies_card:
                widget.deleteLater()

        tendies = tweaks[TweakID.PosterBoard].tendies
        if not tendies:
            # Only add card
            self.tendies_grid.addWidget(self.add_tendies_card, 0, 0)
            return

        row = 0
        col = 0
        for tendie in tendies:
            card = self._create_tendie_card(tendie)
            self.tendies_grid.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        # Add the add card at the end
        self.tendies_grid.addWidget(self.add_tendies_card, row, col)

    def _create_tendie_card(self, tendie) -> QWidget:
        card = IOSCard()
        card.setFixedSize(140, 160)
        card.setCursor(Qt.PointingHandCursor)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(8, 8, 8, 8)
        inner.setSpacing(8)
        inner.setAlignment(Qt.AlignTop)

        # Icon from tendie
        icon = QLabel()
        icon.setFixedSize(80, 80)
        icon.setAlignment(Qt.AlignCenter)
        try:
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(tendie.get_icon())
            if not pixmap.isNull():
                icon.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                icon.setStyleSheet("background-color: #2C2C2E; border-radius: 10px;")
        except Exception:
            icon.setStyleSheet("background-color: #2C2C2E; border-radius: 10px;")
        inner.addWidget(icon, 0, Qt.AlignCenter)

        # Name
        name = QLabel(tendie.name.replace(".tendies", ""))
        name.setStyleSheet("font-size: 13px; color: #8E8E93; text-align: center;")
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(True)
        inner.addWidget(name)

        # Delete button
        del_btn = QToolButton()
        del_btn.setIconSize(QSize(20, 20))
        from PySide6.QtGui import QIcon
        del_btn.setIcon(QIcon(":/icon/trash.svg"))
        del_btn.setStyleSheet(
            "QToolButton { background-color: #1C1C1E; border-radius: 12px; color: #FF3B30; padding: 8px; }"
            "QToolButton:hover { background-color: #FF3B30; color: white; }"
        )
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda: self._delete_tendie(tendie))
        inner.addWidget(del_btn, 0, Qt.AlignCenter)

        return card

    def _delete_tendie(self, tendie):
        from src.tweaks.tweaks import tweaks, TweakID
        if tendie in tweaks[TweakID.PosterBoard].tendies:
            tweaks[TweakID.PosterBoard].tendies.remove(tendie)
        self.refresh_tendies()

def refresh_templates(self):
        self._load_templates_list()
