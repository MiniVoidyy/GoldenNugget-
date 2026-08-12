import os
import sys

from ..page import Page
from ..pages_list import Page as PageItem
from src.qt.mainwindow_ui import Ui_Nugget

from PySide6.QtCore import QCoreApplication, QLocale, QSize, Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QListWidget, QMessageBox, QSizePolicy, QSpacerItem,
    QToolButton, QVBoxLayout, QWidget,
)

from src.tweaks.tweak_loader import load_rdar_fix
from src.tweaks.tweaks import tweaks
from src.controllers.video_handler import set_ignore_frame_limit
from src.controllers.preset_manager import PresetManager
from src.restore.bookrestore import BookRestoreFileTransferMethod, BookRestoreApplyMethod

available_languages = {
    "English": "en",
    "Español": "es",
    "Español (México)": "es_MX",
    "Português": "pt",
    "Français": "fr",
    "Français (Canada)": "fr_CA",
    "Français (Belgium)": "fr_BE",
    "Deutsch": "de",
    "Deutsch (Austria)": "de_AT",
    "Italiano": "it",
    "Русский": "ru",
    "日本語": "ja",
    "普通话": "zh_CN",
    "臺灣話": "zh_TW",
    "Tiếng Việt": "vi",
    "ภาษาไทย": "th",
    "한국어": "ko",
    "Polski": "pl",
    "Türkçe": "tr",
    "Magyar": "hu",
    "Nederlands": "nl",
    "Čeština": "cs",
    "Gaeilge": "ga",
    "Indonesian": "id",
    "Български": "bg",
    "العربية": "ar",
    "العربية (Saudi Arabia)": "ar_SA",
    "مَصرى (Egypt)": "ar_EG",
    "Аҧсуа бызшәа": "ab",
}

class SettingsPage(Page):
    def __init__(self, window, ui: Ui_Nugget):
        super().__init__()
        self.window = window
        self.ui = ui
        self.lang_indexes = []
        self.preset_manager = PresetManager()
        self.presetList = None
        self.presetNameTxt = None
        self.toggle_UAC_btn(self.window.device_manager.pref_manager.bookrestore_apply_mode == BookRestoreApplyMethod.AFC)
        self.setup_presets_ui()
        self.setup_pb_database_ui()
        self.setup_originals_ui()

    def setup_presets_ui(self):
        # Presets section, inserted between the PosterBoard settings and the
        # BookRestore options
        presets_widget = QWidget(self.ui.settingsPageContent)
        presets_widget.setObjectName("presetsWidget")
        presets_layout = QVBoxLayout(presets_widget)
        presets_layout.setObjectName("presetsLayout")
        presets_layout.setContentsMargins(0, 0, 0, 0)
        presets_layout.setSpacing(6)

        # divider
        presets_divider = QFrame(presets_widget)
        presets_divider.setObjectName("presetsDivider")
        presets_divider.setStyleSheet("QFrame {\n\tcolor: #414141;\n}")
        presets_divider.setFrameShadow(QFrame.Plain)
        presets_divider.setFrameShape(QFrame.Shape.HLine)
        presets_layout.addWidget(presets_divider)

        # title + save row
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(-1, -1, -1, 0)
        presets_title = QLabel(presets_widget)
        presets_title.setObjectName("presetsTitle")
        presets_title.setText(QCoreApplication.tr("Presets"))
        title_layout.addWidget(presets_title)
        title_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        presets_layout.addLayout(title_layout)

        # name input + description + save button
        save_layout = QHBoxLayout()
        save_layout.setContentsMargins(-1, -1, -1, 0)
        self.presetNameTxt = QLineEdit(presets_widget)
        self.presetNameTxt.setObjectName("presetNameTxt")
        self.presetNameTxt.setPlaceholderText(QCoreApplication.tr("Preset name"))
        save_layout.addWidget(self.presetNameTxt, 2)
        self.presetDescTxt = QLineEdit(presets_widget)
        self.presetDescTxt.setObjectName("presetDescTxt")
        self.presetDescTxt.setPlaceholderText(QCoreApplication.tr("Description (optional)"))
        save_layout.addWidget(self.presetDescTxt, 3)
        self.presetSaveBtn = QToolButton(presets_widget)
        self.presetSaveBtn.setObjectName("presetSaveBtn")
        self.presetSaveBtn.setText(QCoreApplication.tr("Save Preset"))
        save_layout.addWidget(self.presetSaveBtn)
        presets_layout.addLayout(save_layout)

        # saved presets list with metadata
        self.presetList = QListWidget(presets_widget)
        self.presetList.setObjectName("presetList")
        self.presetList.setMinimumSize(0, 140)
        self.presetList.setStyleSheet("QListWidget {\n"
                                      "\tbackground-color: #3b3b3b;\n"
                                      "\tborder: none;\n"
                                      "\tborder-radius: 8px;\n"
                                      "\tcolor: #e8e8e8;\n"
                                      "\tfont-size: 14px;\n"
                                      "\tpadding: 4px;\n"
                                      "}\n"
                                      "QListWidget::item {\n"
                                      "\tpadding: 8px;\n"
                                      "}\n"
                                      "QListWidget::item:selected {\n"
                                      "\tbackground-color: #535353;\n"
                                      "\tcolor: #ffffff;\n"
                                      "}")
        presets_layout.addWidget(self.presetList, 1)

        # load / delete / refresh / export / import row
        btns_layout = QHBoxLayout()
        btns_layout.setContentsMargins(-1, -1, -1, 0)
        self.presetLoadBtn = QToolButton(presets_widget)
        self.presetLoadBtn.setObjectName("presetLoadBtn")
        self.presetLoadBtn.setText(QCoreApplication.tr("Load Preset"))
        btns_layout.addWidget(self.presetLoadBtn)
        self.presetDeleteBtn = QToolButton(presets_widget)
        self.presetDeleteBtn.setObjectName("presetDeleteBtn")
        self.presetDeleteBtn.setText(QCoreApplication.tr("Delete Preset"))
        btns_layout.addWidget(self.presetDeleteBtn)
        self.presetRefreshBtn = QToolButton(presets_widget)
        self.presetRefreshBtn.setObjectName("presetRefreshBtn")
        self.presetRefreshBtn.setText(QCoreApplication.tr("Refresh"))
        btns_layout.addWidget(self.presetRefreshBtn)
        self.presetExportBtn = QToolButton(presets_widget)
        self.presetExportBtn.setObjectName("presetExportBtn")
        self.presetExportBtn.setText(QCoreApplication.tr("Export"))
        btns_layout.addWidget(self.presetExportBtn)
        self.presetImportBtn = QToolButton(presets_widget)
        self.presetImportBtn.setObjectName("presetImportBtn")
        self.presetImportBtn.setText(QCoreApplication.tr("Import"))
        btns_layout.addWidget(self.presetImportBtn)
        presets_layout.addLayout(btns_layout)

        # insert the section after the PosterBoard checkboxes, before BookRestore
        layout = self.ui._21
        idx = layout.indexOf(self.ui.rebuildSBApplicationStateDBChk)
        layout.insertWidget(idx + 1, presets_widget)

    def setup_pb_database_ui(self):
        # The PosterBoard "Setup" page (apply method / database / saved ids)
        # used to be the first tab of the PosterBoard page. It moved here into
        # Settings: the widgets are the ones from the generated UI, just
        # reparented, and the handlers stay in posterboard.py untouched.
        pb_setup = self.ui.pbSetupPage
        pb_setup.setParent(self.ui.settingsPageContent)

        # drop the expanding spacer so the section stays tight inside Settings
        self.ui.descriptorsSpacer.changeSize(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        layout = self.ui._21
        idx = layout.indexOf(self.ui.bookrestoreWidget)
        layout.insertWidget(idx, pb_setup)

    def setup_originals_ui(self):
        # Original Plists section: back up the system plists Nugget overwrites
        # so Reset can restore the user's original settings. Placed before the
        # BookRestore options.
        originals_widget = QWidget(self.ui.settingsPageContent)
        originals_widget.setObjectName("originalsWidget")
        originals_layout = QVBoxLayout(originals_widget)
        originals_layout.setObjectName("originalsLayout")
        originals_layout.setContentsMargins(0, 0, 0, 0)
        originals_layout.setSpacing(6)

        originals_divider = QFrame(originals_widget)
        originals_divider.setObjectName("originalsDivider")
        originals_divider.setStyleSheet("QFrame {\n\tcolor: #414141;\n}")
        originals_divider.setFrameShadow(QFrame.Plain)
        originals_divider.setFrameShape(QFrame.Shape.HLine)
        originals_layout.addWidget(originals_divider)

        originals_title = QLabel(originals_widget)
        originals_title.setObjectName("originalsTitle")
        originals_title.setText(QCoreApplication.tr("Original Plists"))
        originals_layout.addWidget(originals_title)

        originals_desc = QLabel(originals_widget)
        originals_desc.setObjectName("originalsDesc")
        originals_desc.setWordWrap(True)
        originals_desc.setText(QCoreApplication.tr(
            "Back up the system plists Nugget overwrites so Reset can restore your "
            "original settings instead of empty ones. Save from a clean (just "
            "restored) device for the best result. Saved files only apply to "
            "devices of the same model and iOS build."))
        originals_layout.addWidget(originals_desc)

        self.originalsStatusLbl = QLabel(originals_widget)
        self.originalsStatusLbl.setObjectName("originalsStatusLbl")
        originals_layout.addWidget(self.originalsStatusLbl)

        originals_btns = QHBoxLayout()
        originals_btns.setContentsMargins(-1, -1, -1, 0)
        self.originalsSaveBtn = QToolButton(originals_widget)
        self.originalsSaveBtn.setObjectName("originalsSaveBtn")
        self.originalsSaveBtn.setText(QCoreApplication.tr("Save Originals"))
        originals_btns.addWidget(self.originalsSaveBtn)
        self.originalsDeleteBtn = QToolButton(originals_widget)
        self.originalsDeleteBtn.setObjectName("originalsDeleteBtn")
        self.originalsDeleteBtn.setText(QCoreApplication.tr("Delete Originals"))
        originals_btns.addWidget(self.originalsDeleteBtn)
        originals_layout.addLayout(originals_btns)

        layout = self.ui._21
        idx = layout.indexOf(self.ui.bookrestoreWidget)
        layout.insertWidget(idx, originals_widget)

    def load_page(self):
        self.ui.allowWifiApplyingChk.toggled.connect(self.on_allowWifiApplyingChk_toggled)
        self.ui.autoRebootChk.toggled.connect(self.on_autoRebootChk_toggled)
        self.ui.showAllSpoofableChk.toggled.connect(self.on_showAllSpoofableChk_toggled)

        self.ui.ignorePBFrameLimitChk.toggled.connect(self.on_ignorePBFrameLimitChk_toggled)
        self.ui.disableTendiesLimitChk.toggled.connect(self.on_disableTendiesLimitChk_toggled)
        self.ui.forcePBRefreshChk.toggled.connect(self.on_forcePBRefreshChk_toggled)
        self.ui.rebuildSBApplicationStateDBChk.toggled.connect(self.on_rebuildSBApplicationStateDBChk_toggled)

        self.ui.brApplyModeDrp.activated.connect(self.on_brApplyModeDrp_activated)
        self.ui.brTransferModeDrp.activated.connect(self.on_brTransferModeDrp_activated)
        self.ui.booksContainerUUIDTxt.textEdited.connect(self.on_booksContainerUUIDTxt_textEdited)

        self.ui.trustStoreChk.toggled.connect(self.on_trustStoreChk_toggled)
        # Experimental: encrypted backup option
        if not hasattr(self.ui, 'encryptedBackupChk'):
            from PySide6.QtWidgets import QCheckBox
            from PySide6.QtCore import Qt, QCoreApplication
            self.ui.encryptedBackupChk = QCheckBox(self.ui.settingsPageContent)
            self.ui.encryptedBackupChk.setObjectName("encryptedBackupChk")
            self.ui.encryptedBackupChk.setCursor(Qt.CursorShape.PointingHandCursor)
            self.ui.encryptedBackupChk.setToolTip(QCoreApplication.tr(
                "EXPERIMENTAL: Allow encrypted backups (includes keychain). "
                "Requires knowing backup password. If disabled, encrypted backups are rejected."))
            self.ui.encryptedBackupChk.setText(QCoreApplication.tr(
                "Use Encrypted Backups (Experimental)"))
            # Insert after trustStoreChk in the layout
            layout = self.ui._21
            idx = layout.indexOf(self.ui.trustStoreChk)
            if idx >= 0:
                layout.insertWidget(idx + 1, self.ui.encryptedBackupChk)
            else:
                layout.addWidget(self.ui.encryptedBackupChk)
        self.ui.encryptedBackupChk.toggled.connect(self.on_encryptedBackupChk_toggled)

        self.ui.skipSetupChk.toggled.connect(self.on_skipSetupChk_toggled)
        self.ui.supervisionChk.toggled.connect(self.on_supervisionChk_toggled)
        self.ui.supervisionOrganization.textEdited.connect(self.on_supervisionOrgTxt_textEdited)
        self.ui.resetPairBtn.clicked.connect(self.on_resetPairBtn_clicked)

        # the PosterBoard Setup section now lives in Settings, so wire its
        # controls to the PosterBoard page handlers here (the page object is
        # only reachable via self.window.pages, which isn't built yet when
        # this page is constructed)
        posterboard_page = self.window.pages[PageItem.Posterboard]
        self.ui.pbGetDBBtn.clicked.connect(posterboard_page.on_pbGetDBBtn_clicked)
        self.ui.pbDBBtn.clicked.connect(posterboard_page.on_pbDBBtn_clicked)
        self.ui.clearSavedIdsBtn.clicked.connect(posterboard_page.on_clearSavedIdsBtn_clicked)
        self.ui.removeSelectedIdBtn.clicked.connect(posterboard_page.on_removeSelectedIdBtn_clicked)

        self.presetSaveBtn.clicked.connect(self.on_presetSaveBtn_clicked)
        self.presetLoadBtn.clicked.connect(self.on_presetLoadBtn_clicked)
        self.presetDeleteBtn.clicked.connect(self.on_presetDeleteBtn_clicked)
        self.presetRefreshBtn.clicked.connect(self.on_presetRefreshBtn_clicked)
        self.presetExportBtn.clicked.connect(self.on_presetExportBtn_clicked)
        self.presetImportBtn.clicked.connect(self.on_presetImportBtn_clicked)

        self.originalsSaveBtn.clicked.connect(self.on_originalsSaveBtn_clicked)
        self.originalsDeleteBtn.clicked.connect(self.on_originalsDeleteBtn_clicked)

        self.load_available_languages()
        self.ui.langDrp.activated.connect(self.on_langDrp_activated)
        self.refresh_presets()
        self.update_originals_status()

    # Load available languages
    def load_available_languages(self):
        for language in available_languages.keys():
            self.lang_indexes.append(available_languages[language])
            self.ui.langDrp.addItem(language)
        # load the saved option
        try:
            idx = self.lang_indexes.index(self.window.translator.get_saved_locale_code())
        except Exception:
            idx = 0
        self.ui.langDrp.setCurrentIndex(idx)

    # Toggle the UAC info
    def toggle_UAC_btn(self, visible: bool):
        if os.name != 'nt':
            self.ui.restartUACLbl.hide()
            self.ui.restartUACBtn.hide()
            return
        import pyuac
        show_btn = visible and not pyuac.isUserAdmin()
        self.ui.restartUACLbl.setVisible(show_btn)
        self.ui.restartUACBtn.setVisible(show_btn)

    ## ACTIONS
    def on_langDrp_activated(self, index: int):
        new_lang = self.lang_indexes[index]
        if new_lang != self.window.translator.get_saved_locale_code():
            self.window.translator.set_new_language(new_lang, restart=True)

    def on_allowWifiApplyingChk_toggled(self, checked: bool):
        self.window.device_manager.pref_manager.apply_over_wifi = checked
        # save the setting
        self.window.settings.setValue("apply_over_wifi", checked)
    def on_showAllSpoofableChk_toggled(self, checked: bool):
        self.window.device_manager.pref_manager.show_all_spoofable_models = checked
        # save the setting
        self.window.settings.setValue("show_all_spoofable_models", checked)
        # refresh the list of spoofable models
        self.window.pages[PageItem.Gestalt].setup_spoofedModelDrp_models()
    def on_ignorePBFrameLimitChk_toggled(self, checked: bool):
        set_ignore_frame_limit(checked)
        # save the setting
        self.window.settings.setValue("ignore_pb_frame_limit", checked)
    def on_disableTendiesLimitChk_toggled(self, checked: bool):
        self.window.device_manager.pref_manager.disable_tendies_limit = checked
        # save the setting
        self.window.settings.setValue("disable_tendies_limit", checked)
    def on_forcePBRefreshChk_toggled(self, checked: bool):
        self.window.device_manager.pref_manager.auto_refresh_posterboard = checked
        self.window.settings.setValue("auto_refresh_posterboard", checked)
    def on_rebuildSBApplicationStateDBChk_toggled(self, checked: bool):
        self.window.device_manager.pref_manager.rebuild_sb_application_state_db = checked
    def on_autoRebootChk_toggled(self, checked: bool):
        self.window.device_manager.pref_manager.auto_reboot = checked
        # save the setting
        self.window.settings.setValue("auto_reboot", checked)
    def on_trustStoreChk_toggled(self, checked: bool):
        self.window.device_manager.pref_manager.restore_truststore = checked
        # save the setting
        self.window.settings.setValue("restore_truststore", checked)

    # Experimental options
    def on_encryptedBackupChk_toggled(self, checked: bool):
        self.window.device_manager.pref_manager.use_encrypted_backup = checked
        self.window.settings.setValue("use_encrypted_backup", checked)

    def on_skipSetupChk_toggled(self, checked: bool):
        self.window.device_manager.pref_manager.skip_setup = checked
        # save the setting
        self.window.settings.setValue("skip_setup", checked)
        # hide/show the warning label
        if checked:
            self.ui.skipSetupOnLbl.show()
        else:
            self.ui.skipSetupOnLbl.hide()
    def on_supervisionOrgTxt_textEdited(self, text: str):
        self.window.device_manager.pref_manager.organization_name = text
        self.window.settings.setValue("organization_name", text)
    def on_supervisionChk_toggled(self, checked: bool):
        self.window.device_manager.pref_manager.supervised = checked
        # save the setting
        self.window.settings.setValue("supervised", checked)

    # BookRestore Options
    def on_booksContainerUUIDTxt_textEdited(self, text: str):
        self.window.device_manager.current_device_books_container_uuid_callback(text)
    def on_brTransferModeDrp_activated(self, index: int):
        new_mode = BookRestoreFileTransferMethod(index)
        self.window.device_manager.pref_manager.bookrestore_transfer_mode = new_mode
        # save the setting
        self.window.settings.setValue("bookrestore_transfer_mode", index)
    def on_brApplyModeDrp_activated(self, index: int):
        new_mode = BookRestoreApplyMethod(index)
        self.window.device_manager.pref_manager.bookrestore_apply_mode = new_mode
        show_btn = new_mode == BookRestoreApplyMethod.AFC and self.window.device_manager.get_current_device_uses_bookrestore()
        self.toggle_UAC_btn(show_btn)
        # save the setting
        self.window.settings.setValue("bookrestore_apply_mode", index)

    # Device Options
    def on_resetPairBtn_clicked(self):
        self.window.device_manager.reset_device_pairing()

    ## PRESETS
    def refresh_presets(self):
        self.presetList.clear()
        for meta in self.preset_manager.list_presets_with_metadata():
            name = meta["name"]
            desc = meta.get("description", "")
            model = meta.get("device_model", "Unknown")
            ios = meta.get("ios_version", "Unknown")
            tags = meta.get("tags", [])
            tag_str = "  #" + " #".join(tags) if tags else ""
            if desc:
                item_text = f"{name}\n  {desc}  ({model} • iOS {ios}){tag_str}"
            else:
                item_text = f"{name}  ({model} • iOS {ios}){tag_str}"
            self.presetList.addItem(item_text)

    def on_presetSaveBtn_clicked(self):
        default_name = self.presetNameTxt.text().strip()
        default_desc = self.presetDescTxt.text().strip()
        name, ok = QInputDialog.getText(
            self.window, QCoreApplication.tr("Save Preset"),
            QCoreApplication.tr("Enter a name for this preset:"),
            text=default_name
        )
        if not ok or name.strip() == "":
            return
        desc, ok2 = QInputDialog.getText(
            self.window, QCoreApplication.tr("Save Preset"),
            QCoreApplication.tr("Enter a description (optional):"),
            text=default_desc
        )
        if not ok2:
            desc = default_desc
        if self.preset_manager.save_preset(name.strip(), desc.strip(), tags=[]):
            self.presetNameTxt.clear()
            self.presetDescTxt.clear()
            self.refresh_presets()
            QMessageBox.information(
                self.window, QCoreApplication.tr("Save Preset"),
                QCoreApplication.tr("Preset \"{0}\" saved successfully.").format(name.strip())
            )
        else:
            QMessageBox.critical(
                self.window, QCoreApplication.tr("Save Preset"),
                QCoreApplication.tr("Failed to save the preset.")
            )

    def on_presetLoadBtn_clicked(self):
        if self.presetList.currentRow() < 0:
            QMessageBox.warning(
                self.window, QCoreApplication.tr("Load Preset"),
                QCoreApplication.tr("Select a preset to load first.")
            )
            return
        # Extract name from the first line of the item text
        item_text = self.presetList.currentItem().text()
        name = item_text.split("\n")[0].strip()
        meta = self.preset_manager.get_preset_metadata(name)
        desc = meta.get("description", "") if meta else ""
        model = meta.get("device_model", "Unknown") if meta else "Unknown"
        ios = meta.get("ios_version", "Unknown") if meta else "Unknown"
        confirm = QMessageBox.question(
            self.window, QCoreApplication.tr("Load Preset"),
            QCoreApplication.tr("Load preset \"{0}\"?\n\nDescription: {1}\nDevice: {2} • iOS {3}\n\nThis will replace your current configuration.").format(name, desc, model, ios)
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        if not self.preset_manager.load_preset(name):
            QMessageBox.critical(
                self.window, QCoreApplication.tr("Load Preset"),
                QCoreApplication.tr("Failed to load the preset.")
            )
            return
        # remember which preset was loaded so it can be restored after the app
        # restarts (the pages read the tweak state only once on startup)
        self.window.settings.setValue("last_loaded_preset", name)
        self.window.settings.sync()
        QMessageBox.information(
            self.window, QCoreApplication.tr("Load Preset"),
            QCoreApplication.tr("Preset \"{0}\" loaded.\n\nGoldenNugget will now restart to apply the changes.").format(name)
        )
        self.restart_app()

    def on_presetDeleteBtn_clicked(self):
        if self.presetList.currentRow() < 0:
            QMessageBox.warning(
                self.window, QCoreApplication.tr("Delete Preset"),
                QCoreApplication.tr("Select a preset to delete first.")
            )
            return
        item_text = self.presetList.currentItem().text()
        name = item_text.split("\n")[0].strip()
        confirm = QMessageBox.question(
            self.window, QCoreApplication.tr("Delete Preset"),
            QCoreApplication.tr("Delete preset \"{0}\"?").format(name)
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        if self.preset_manager.delete_preset(name):
            self.refresh_presets()
        else:
            QMessageBox.critical(
                self.window, QCoreApplication.tr("Delete Preset"),
                QCoreApplication.tr("Failed to delete the preset.")
            )

    def on_presetRefreshBtn_clicked(self):
        self.refresh_presets()

    def on_presetExportBtn_clicked(self):
        if self.presetList.currentRow() < 0:
            QMessageBox.warning(
                self.window, QCoreApplication.tr("Export Preset"),
                QCoreApplication.tr("Select a preset to export first.")
            )
            return
        item_text = self.presetList.currentItem().text()
        name = item_text.split("\n")[0].strip()
        file_path, _ = QFileDialog.getSaveFileName(
            self.window, QCoreApplication.tr("Export Preset"),
            f"{name}.json",
            QCoreApplication.tr("JSON Files (*.json)")
        )
        if not file_path:
            return
        if self.preset_manager.export_preset(name, file_path):
            QMessageBox.information(
                self.window, QCoreApplication.tr("Export Preset"),
                QCoreApplication.tr("Preset exported to:\n{0}").format(file_path)
            )
        else:
            QMessageBox.critical(
                self.window, QCoreApplication.tr("Export Preset"),
                QCoreApplication.tr("Failed to export preset.")
            )

    def on_presetImportBtn_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.window, QCoreApplication.tr("Import Preset"),
            "",
            QCoreApplication.tr("JSON Files (*.json)")
        )
        if not file_path:
            return
        success, result = self.preset_manager.import_preset(file_path)
        if success:
            self.refresh_presets()
            QMessageBox.information(
                self.window, QCoreApplication.tr("Import Preset"),
                QCoreApplication.tr("Preset \"{0}\" imported successfully.").format(result)
            )
        else:
            QMessageBox.critical(
                self.window, QCoreApplication.tr("Import Preset"),
                QCoreApplication.tr("Failed to import preset:\n{0}").format(result)
            )

    ## ORIGINAL PLISTS
    def update_originals_status(self):
        model = self.window.device_manager.get_current_device_model()
        build = self.window.device_manager.get_current_device_build()
        originals = {}
        if model and build:
            originals = self.window.device_manager.pref_manager.get_original_plists(model, build)
        if originals:
            self.originalsStatusLbl.setText(QCoreApplication.tr(
                "Saved: {0} files for {1} ({2})").format(len(originals), model, build))
            self.originalsStatusLbl.setStyleSheet("color: #7ed67e;")
        else:
            self.originalsStatusLbl.setText(QCoreApplication.tr(
                "Not saved yet. Connect a clean device and tap \"Save Originals\"."))
            self.originalsStatusLbl.setStyleSheet("color: #e8a33d;")

    def on_originalsSaveBtn_clicked(self):
        if not self.window.device_manager.get_current_device_udid():
            QMessageBox.warning(
                self.window, QCoreApplication.tr("Save Originals"),
                QCoreApplication.tr("No device connected."))
            return
        confirm = QMessageBox.question(
            self.window, QCoreApplication.tr("Save Originals"),
            QCoreApplication.tr(
                "Back up the current device's original plists?\n\n"
                "This may take a few minutes and the device may ask for its passcode. "
                "Save from a clean (just restored) device for the best result."))
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.window.capture_originals()

    def on_originalsDeleteBtn_clicked(self):
        model = self.window.device_manager.get_current_device_model()
        build = self.window.device_manager.get_current_device_build()
        if not model or not build:
            return
        confirm = QMessageBox.question(
            self.window, QCoreApplication.tr("Delete Originals"),
            QCoreApplication.tr(
                "Delete the saved original plists for {0} ({1})?\n\n"
                "Reset will fall back to writing empty plists.").format(model, build))
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.window.device_manager.pref_manager.remove_original_plists(model, build)
        self.update_originals_status()

    def restart_app(self):
        os.execl(sys.executable, sys.executable, *sys.argv)
