import asyncio
import os.path
import plistlib
import sys
import traceback

from tempfile import TemporaryDirectory
from typing import Optional
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding
from uuid import uuid4

from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit
from PySide6.QtCore import QSettings, QCoreApplication

from packaging.version import Version

from pymobiledevice3 import usbmux
from pymobiledevice3.ca import create_keybag_file
from pymobiledevice3.services.mobile_config import MobileConfigService
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.exceptions import MuxException, PasswordRequiredError, ConnectionTerminatedError, AccessDeniedError, InvalidServiceError
from pymobiledevice3.services.afc import AfcService
from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service
import pymobiledevice3.service_connection as _sc


from src.exceptions.device_errors import is_device_locked_error as _is_device_locked_error

# Bump SSL handshake timeout from 10s to 60s for all lockdown services.
_sc.DEFAULT_SSL_HANDSHAKE_TIMEOUT = 60

# Temporarily allow writing up to this many PosterBoard tendies in a single
# restore. Applying more than one tendie at once can race PosterBoard's sqlite
# regeneration, so the count is capped.
MAX_TENDIES_PER_RESTORE = 3

from src.devicemanagement.constants import Device, Version
from src.devicemanagement.data_singleton import DataSingleton
from .preference_manager import PreferenceManager

from src.gui.thread_workers.apply_worker import ApplyAlertMessage
from src.gui.pages.pages_list import Page
from src.controllers.path_handler import fix_windows_path

from src.exceptions.nugget_exception import NuggetException

from src.tweaks.tweaks import tweaks, TweakID, BasicPlistTweak, AdvancedPlistTweak, NullifyFileTweak, StatusBarTweak, PasscodeThemeTweak
from src.tweaks.posterboard.posterboard_tweak import PosterboardTweak
from src.tweaks.posterboard.template_options.templates_tweak import TemplatesTweak
from src.tweaks.basic_plist_locations import FileLocation

from src.restore.restore import restore_files, FileToRestore
from src.restore.original_plist import psysbackup, materialize_plist, is_empty_plist, mobile_user_fallback_path

def get_files_list_str(files_list: list[FileToRestore] = None) -> str:
    files_str: str = ""
    if files_list != None:
        files_str = "FILES LIST:"
        print("\nFile List:\n")
        for file in files_list:
            file_info = f"\n    Domain: {file.domain}\n    Path: {file.restore_path}"
            files_str += file_info
            print(file_info)
    return files_str

def show_apply_error(e: Exception, update_label=lambda x: None, files_list: list[FileToRestore] = None):
    print(traceback.format_exc())
    update_label("Failed to restore")
    if "Find My" in str(e):
        return ApplyAlertMessage(QCoreApplication.tr("Find My must be disabled in order to use this tool."),
                       detailed_txt=QCoreApplication.tr("Disable Find My from Settings (Settings -> [Your Name] -> Find My) and then try again."))
    elif "Encrypted Backup MDM" in str(e):
        return ApplyAlertMessage(QCoreApplication.tr("Nugget cannot be used on this device. Click Show Details for more info."),
                       detailed_txt=QCoreApplication.tr("Your device is managed and MDM backup encryption is on. This must be turned off in order for Nugget to work. Please do not use Nugget on your school/work device!"))
    elif "SessionInactive" in str(e) or "ConnectionAbortedError" in str(e):
        return ApplyAlertMessage(QCoreApplication.tr("The session was terminated. Refresh the device list and try again."))
    elif "PasswordRequiredError" in str(e):
        return ApplyAlertMessage(QCoreApplication.tr("Device is password protected! You must trust the computer on your device."),
                       detailed_txt=QCoreApplication.tr("Unlock your device. On the popup, click \"Trust\", enter your password, then try again."))
    elif isinstance(e, ConnectionTerminatedError):
        files_str: str = get_files_list_str(files_list)
        return ApplyAlertMessage(QCoreApplication.tr("Device failed in sending files. The file list is possibly corrupted or has duplicates. Click Show Details for more info."),
                                 detailed_txt=files_str + "TRACEBACK:\n\n" + str(traceback.format_exc()))
    elif isinstance(e, AccessDeniedError):
        return ApplyAlertMessage(QCoreApplication.tr("Access denied while sending files."), detailed_txt="Try running the program with sudo.")
    elif isinstance(e, InvalidServiceError):
        return ApplyAlertMessage(QCoreApplication.tr("You must enable developer mode on your device. You can do it in the Settings app."),
                                 detailed_txt=QCoreApplication.tr("Applying tweaks requires developer mode.\n\nYou can enable this at the bottom of Settings > Privacy & Security > Developer Mode on your iPhone or iPad."))
    elif isinstance(e, NuggetException):
        return ApplyAlertMessage(str(e), detailed_txt=e.detailed_text)
    else:
        files_str: str = get_files_list_str(files_list)
        error_msg = type(e).__name__ + ": " + repr(e)
        # Check if this is a protective backup failure with a backup path
        backup_path = None
        error_str = str(e)
        if "protective backup kept at:" in error_str:
            import re
            match = re.search(r'protective backup kept at:\s*(\S+)', error_str)
            if match:
                backup_path = match.group(1)
        return ApplyAlertMessage(
            error_msg, 
            detailed_txt=files_str + "TRACEBACK:\n\n" + str(traceback.format_exc()),
            backup_path=backup_path
        )

class DeviceManager:
    ## Class Functions
    def __init__(self):
        self.devices: list[Device] = []
        self.data_singleton = DataSingleton()
        self.current_device_index = 0

        # preferences
        self.pref_manager = PreferenceManager(None)
        
        # Backup password (for encrypted backups)
        self._backup_password: Optional[str] = None
        
        # Test mode
        self._test_mode = "--test-mode" in sys.argv
    
    def _get_backup_password(self) -> str:
        """Get backup password from settings or return empty string."""
        if self._backup_password:
            return self._backup_password
        # Try to get from settings
        if hasattr(self, 'pref_manager') and self.pref_manager.settings:
            pwd = self.pref_manager.settings.value("backup_password", "", type=str)
            if pwd:
                self._backup_password = pwd
                return pwd
        return ""
    
    def get_devices(self, settings: QSettings, show_alert=lambda x: None):
        asyncio.run(self._get_devices(settings, show_alert))
    async def _get_devices(self, settings: QSettings, show_alert=lambda x: None):
        # Test mode: use mock device already set up in main_app.py
        if self._test_mode:
            self.pref_manager.settings = settings
            return
        
        self.devices.clear()
        # handle errors when failing to get connected devices
        try:
            connected_devices = await usbmux.list_devices()
        except Exception:
            sysmsg = QCoreApplication.tr("If you are on Linux, make sure you have usbmuxd and libimobiledevice installed.")
            if os.name == 'nt':
                sysmsg = QCoreApplication.tr("Make sure you have the \"Apple Devices\" app from the Microsoft Store or iTunes from Apple's website.")
            show_alert(ApplyAlertMessage(
                txt=QCoreApplication.tr("Failed to get device list. Click \"Show Details\" for the traceback.") + f"\n\n{sysmsg}", detailed_txt=str(traceback.format_exc())
            ))
            self.set_current_device(index=None)
            return
        # Connect via usbmuxd
        for device in connected_devices:
            try:
                ld = await create_using_usbmux(serial=device.serial)
                # Check backup encryption status if experimental option not enabled
                if not self.pref_manager.use_encrypted_backup:
                    try:
                        from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service
                        mb = Mobilebackup2Service(ld)
                        await mb.connect()
                        is_encrypted = await mb.get_will_encrypt()
                        await mb.close()
                        if is_encrypted:
                            show_alert(ApplyAlertMessage(
                                txt=QCoreApplication.tr("Backup encryption is enabled on your iPhone."),
                                detailed_txt=QCoreApplication.tr(
                                    "GoldenNugget needs to temporarily disable backup encryption to apply tweaks safely.\n\n"
                                    "Please choose one:\n"
                                    "1. Disable encryption on your iPhone: Settings → General → Transfer or Reset iPhone → Backup Password → Turn Off\n"
                                    "2. Or enable \"Use Encrypted Backups (Experimental)\" in GoldenNugget Settings → enter your backup password when prompted.\n\n"
                                    "Tip: Option 1 is simpler if you don't know your backup password."
                                )
                            ))
                            self.set_current_device(index=None)
                            return
                    except Exception:
                        pass  # If we can't check, continue anyway
                vals = ld.all_values
                model = vals['ProductType']
                hardware = vals['HardwareModel']
                cpu = vals['HardwarePlatform']
                try:
                    product_type = settings.value(device.serial + "_model", "", type=str)
                    hardware_type = settings.value(device.serial + "_hardware", "", type=str)
                    cpu_type = settings.value(device.serial + "_cpu", "", type=str)
                    if product_type == "":
                        # save the new product type
                        settings.setValue(device.serial + "_model", model)
                    else:
                        model = product_type
                    if hardware_type == "":
                        # save the new hardware model
                        settings.setValue(device.serial + "_hardware", hardware)
                    else:
                        hardware = hardware_type
                    if cpu_type == "":
                        # save the new cpu model
                        settings.setValue(device.serial + "_cpu", cpu)
                    else:
                        cpu = cpu_type
                except Exception:
                    show_alert(ApplyAlertMessage(txt=QCoreApplication.tr("Click \"Show Details\" for the traceback."), detailed_txt=str(traceback.format_exc())))
                locale = await ld.get_locale()
                dev = Device(
                        udid=device.serial,
                        usb=device.is_usb,
                        name=vals['DeviceName'],
                        version=vals['ProductVersion'],
                        build=vals['BuildVersion'],
                        model=model,
                        hardware=hardware,
                        cpu=cpu,
                        locale=locale,
                    )
                self.devices.append(dev)
            except PasswordRequiredError as e:
                show_alert(ApplyAlertMessage(txt=QCoreApplication.tr("Device is password protected! You must trust the computer on your device.\n\nUnlock your device. On the popup, click \"Trust\", enter your password, then try again.")))
            except MuxException as e:
                # there is probably a cable issue
                print(f"MUX ERROR with lockdown device with UUID {device.serial}")
                show_alert(ApplyAlertMessage(txt="MuxException: " + repr(e) + "\n\n" + QCoreApplication.tr("If you keep receiving this error, try using a different cable or port."),
                               detailed_txt=str(traceback.format_exc())))
            except Exception as e:
                print(f"ERROR with lockdown device with UUID {device.serial}")
                show_alert(ApplyAlertMessage(txt=f"{type(e).__name__}: {repr(e)}", detailed_txt=str(traceback.format_exc())))
            finally:
                await ld.close()
        
        if len(self.devices) > 0:
            self.set_current_device(index=0)
        else:
            self.set_current_device(index=None)

    ## CURRENT DEVICE
    def set_current_device(self, index: int = None):
        if index == None or len(self.devices) == 0:
            self.data_singleton.current_device = None
            self.data_singleton.device_available = False
            self.current_device_index = 0
        else:
            self.data_singleton.current_device = self.devices[index]
            if not self.devices[index].is_supported_by_fork():
                # hard-block old versions (< 26.2): the device is listed so the
                # user sees it, but every action is refused.
                self.data_singleton.device_available = False
            else:
                self.data_singleton.device_available = True
            self.current_device_index = index
        
    def get_current_device_name(self) -> str:
        if self.data_singleton.current_device == None:
            return QCoreApplication.tr("No Device")
        else:
            return self.data_singleton.current_device.name
        
    def get_current_device_version(self) -> str:
        if self.data_singleton.current_device == None:
            return ""
        else:
            return self.data_singleton.current_device.version
    
    def get_current_device_build(self) -> str:
        if self.data_singleton.current_device == None:
            return ""
        else:
            return self.data_singleton.current_device.build
    
    def get_current_device_udid(self) -> Optional[str]:
        if self.data_singleton.current_device == None:
            return None
        else:
            return self.data_singleton.current_device.udid
        
    def get_current_device_model(self) -> str:
        if self.data_singleton.current_device == None:
            return ""
        else:
            return self.data_singleton.current_device.model
        
    def get_current_device_supported(self) -> bool:
        if self.data_singleton.current_device == None:
            return False
        else:
            return self.data_singleton.current_device.supported()
    
    def get_current_device_patched(self) -> bool:
        if self.data_singleton.current_device == None:
            return True
        else:
            return self.data_singleton.current_device.is_exploit_fully_patched()
        
    def get_current_device_is_supported_by_fork(self) -> bool:
        if self.data_singleton.current_device == None:
            return False
        else:
            return self.data_singleton.current_device.is_supported_by_fork()

    def get_current_device_partially_supported(self) -> bool:
        """iOS 27 devices use the experimental three-phase protective restore."""
        if self.data_singleton.current_device == None:
            return False
        try:
            return Version(self.data_singleton.current_device.version) >= Version("27.0")
        except Exception:
            return False
        
    def reset_device_pairing(self):
        asyncio.run(self._reset_device_pairing())
    async def _reset_device_pairing(self):
        # first, unpair it
        if self.data_singleton.current_device == None:
            return
        ld = await create_using_usbmux(serial=self.data_singleton.current_device.udid)
        await ld.unpair()
        # next, pair it again
        await ld.pair()
        await ld.close()
        QMessageBox.information(None, QCoreApplication.tr("Pairing Reset"), QCoreApplication.tr("Your device's pairing was successfully reset. Refresh the device list before applying."))
        
    async def add_skip_setup(self, files_to_restore: list[FileToRestore], restoring_domains: bool):
        # TODO: Probably should move this to its own file
        if self.pref_manager.skip_setup and (not self.get_current_device_supported() or restoring_domains):
            # get the already existing cloud config info
            ld = await create_using_usbmux(serial=self.data_singleton.current_device.udid)
            async with MobileConfigService(lockdown=ld) as mcs:
                cloud_config_plist = await mcs.get_cloud_configuration()
            await ld.close()
            # add the 2 skip setup files
            cloud_config_plist["SkipSetup"] = [
                    'Location',
                    'Restore',
                    'SIMSetup',
                    'Android',
                    'AppleID',
                    'IntendedUser',
                    'TOS',
                    'Siri',
                    'ScreenTime',
                    'Diagnostics',
                    'SoftwareUpdate',
                    'Passcode',
                    'Biometric',
                    'Payment',
                    'Zoom',
                    'DisplayTone',
                    'MessagingActivationUsingPhoneNumber',
                    'HomeButtonSensitivity',
                    'CloudStorage',
                    'ScreenSaver',
                    'TapToSetup',
                    'WatchMigration',
                    'OnBoarding',
                    'TVProviderSignIn',
                    'TVHomeScreenSync',
                    'Privacy',
                    'TVRoom',
                    'iMessageAndFaceTime',
                    'AppStore',
                    'Safety',
                    'Multitasking',
                    'ActionButton',
                    'TermsOfAddress',
                    'AccessibilityAppearance',
                    'Welcome',
                    'Appearance',
                    'RestoreCompleted',
                    'UpdateCompleted',
                    'WiFi',
                    'Display',
                    'Tone',
                    'TouchID',
                    'TrueToneDisplay',
                    'FileVault',
                    'iCloudStorage',
                    'iCloudDiagnostics',
                    'Registration',
                    'DeviceToDeviceMigration',
                    'UnlockWithWatch',
                    'Accessibility',
                    'All',
                    'N/A',
                    'Avatar',
                    'DeviceProtection',
                    'Key',
                    'LockdownMode',
                    'Wallpaper',
                    'PrivacySubtitle',
                    'SecuritySubtitle',
                    'DataSubtitle',
                    'AppleIDSubtitle',
                    'AppearanceSubtitle',
                    'OnboardingSubtitle',
                    'AppleTVSubtitle',
                    'Intelligence',
                    'WebContentFiltering',
                    'CameraButton',
                    'AdditionalPrivacySettings',
                    'EnableLockdownMode',
                    'OSShowcase',
                    'SafetyAndHandling',
                    'Tips',
                    "AgeBasedSafetySettings",
                ]
            cloud_config_plist["AllowPairing"] = True
            cloud_config_plist["ConfigurationWasApplied"] = True
            cloud_config_plist["CloudConfigurationUIComplete"] = True
            cloud_config_plist["IsSupervised"] = False
            cloud_config_plist["ConfigurationSource"] = 0
            cloud_config_plist["PostSetupProfileWasInstalled"] = True
            if self.pref_manager.supervised == True:
                cloud_config_plist["IsSupervised"] = True
                # create/add the keybag
                if self.pref_manager.organization_name != None and self.pref_manager.organization_name != "":
                    with TemporaryDirectory() as temp_dir:
                        keybag_file = Path(temp_dir) / 'keybag'
                        create_keybag_file(keybag_file, self.pref_manager.organization_name)
                        cer = x509.load_pem_x509_certificate(keybag_file.read_bytes())
                        public_key = cer.public_bytes(Encoding.DER)
                        # make sure the mdm is removable
                        cloud_config_plist["OrganizationName"] = self.pref_manager.organization_name
                        cloud_config_plist['OrganizationMagic'] = str(uuid4())
                        cloud_config_plist['IsMDMUnremovable'] = False
                        cloud_config_plist['SupervisorHostCertificates'] = [public_key]
                else:
                    # remove keybag info
                    if 'OrganizationMagic' in cloud_config_plist:
                        cloud_config_plist.pop('OrganizationMagic')
                    if 'SupervisorHostCertificates' in cloud_config_plist:
                        cloud_config_plist.pop('SupervisorHostCertificates')
            files_to_restore.append(FileToRestore(
                contents=plistlib.dumps(cloud_config_plist),
                restore_path="Library/ConfigurationProfiles/CloudConfigurationDetails.plist",
                domain="SysSharedContainerDomain-systemgroup.com.apple.configurationprofiles"
            ))
            purplebuddy_plist: dict = {
                "SetupDone": True,
                "SetupFinishedAllSteps": True
            }
            files_to_restore.append(FileToRestore(
                contents=plistlib.dumps(purplebuddy_plist),
                restore_path="mobile/com.apple.purplebuddy.plist",
                domain="ManagedPreferencesDomain"
            ))

    def get_domain_for_path(self, path: str, owner: int = 501) -> str:
        # returns Domain: str?, Path: str
        fully_patched = True
        # just make the Sys Containers to use the regular way (won't work for mga)
        sysSharedContainer = "SysSharedContainerDomain-"
        sysContainer = "SysContainerDomain-"
        mappings: dict = {
            "/var/Managed Preferences/": "ManagedPreferencesDomain",
            "/var/root/": "RootDomain",
            "/var/preferences/": "SystemPreferencesDomain",
            "/var/MobileDevice/": "MobileDeviceDomain",
            "/var/mobile/": "HomeDomain",
            "/var/db/": "DatabaseDomain",
            "/var/containers/Shared/SystemGroup/": sysSharedContainer,
            "/var/containers/Data/SystemGroup/": sysContainer
        }
        for mapping in mappings.keys():
            if path.startswith(mapping):
                new_path = path.replace(mapping, "")
                new_domain = mappings[mapping]
                # if patched, include the next part of the path in the domain
                if fully_patched and (new_domain == sysSharedContainer or new_domain == sysContainer):
                    parts = new_path.split("/")
                    new_domain += parts[0]
                    new_path = new_path.replace(parts[0] + "/", "")
                return new_path, new_domain
        return path, ""
    
    def concat_file(self, contents: str, path: str, files_to_restore: list[FileToRestore], owner: int = 501, group: int = 501):
        # TODO: try using inodes here instead
        file_path, domain = self.get_domain_for_path(path, owner=owner)
        files_to_restore.append(FileToRestore(
            contents=contents,
            restore_path=file_path,
            domain=domain,
            owner=owner, group=group
        ))
    
    ## APPLYING OR REMOVING TWEAKS AND RESTORING
    def _raise_if_unsupported(self):
        if not self.get_current_device_is_supported_by_fork():
            raise NuggetException(QCoreApplication.tr(
                "This version of iOS is not supported by this fork.\n\n"
                "GoldenNugget only supports iOS 26.2 and newer. "
                "Please use the original Nugget for iOS 26.1 and earlier."))

    async def start_restore(self, files_to_restore: list[FileToRestore], update_label=lambda x: None, backup_password: str = ""):
        # hard-block any restore on an unsupported (old) iOS version
        self._raise_if_unsupported()
        self.update_label = update_label
        self.do_not_unplug = ""
        if self.data_singleton.current_device.connected_via_usb:
            self.do_not_unplug = "\n" + QCoreApplication.tr("DO NOT UNPLUG")
        # Use manual try/finally instead of async with so that ld.close()
        # errors (e.g. ConnectionTerminatedError after device reboot) do not
        # propagate as a misleading "Connection Lost" error to the UI.
        ld = await create_using_usbmux(serial=self.data_singleton.current_device.udid)
        try:
            update_label(QCoreApplication.tr("Preparing to restore...") + self.do_not_unplug)
            await restore_files(
                files=files_to_restore, reboot=self.pref_manager.auto_reboot,
                lockdown_client=ld,
                progress_callback=self.progress_callback,
                backup_password=backup_password
            )
            tweaks[TweakID.PosterBoard].config_manager.save_staged_ids(self.get_current_device_udid())
            msg = QCoreApplication.tr("Your device will now restart.\n\nRemember to turn Find My back on!")
            if not self.pref_manager.auto_reboot:
                msg = QCoreApplication.tr("Please restart your device to see changes.")
            return ApplyAlertMessage(txt=QCoreApplication.tr("All done! ") + msg, title=QCoreApplication.tr("Success!"), icon=QMessageBox.Information)
        finally:
            # Safely close the lockdown client — after a device reboot the
            # underlying connection is already severed and close() will raise
            # ConnectionTerminatedError. Suppress it so the real result (success
            # or a genuine error) reaches the caller correctly.
            try:
                await ld.close()
            except Exception:
                pass

    def progress_callback(self, progress):
        if self.update_label == None:
            return
        if isinstance(progress, str):
            self.update_label(progress)
            return
        prog = ""
        if progress != None:
            prog = f" ({progress:6.1f}% )"
        self.update_label(QCoreApplication.tr("Restoring to device...{0}{1}").format(prog, self.do_not_unplug))
    def _backup_progress(self, update_label):
        """Progress callback for backup-driven captures (psysbackup).

        Unlike ``progress_callback`` it does not depend on ``self.update_label``
        (only set by ``start_restore``), so it is safe to call before any
        restore has started. Status strings pass through as labels; anything
        that is not a number is dropped so the bar never sees garbage.
        """
        def _cb(progress):
            if isinstance(progress, str):
                update_label(progress)
                return
            if isinstance(progress, bool) or not isinstance(progress, (int, float)):
                return
            update_label(QCoreApplication.tr("Backing up device... ({0:.1f}%)").format(progress))
        return _cb
    def apply_changes(self, update_label=lambda x: None, show_alert=lambda x: None):
        asyncio.run(self._apply_changes(update_label, show_alert))
    async def _apply_changes(self, update_label=lambda x: None, show_alert=lambda x: None):
        files_to_restore: list[FileToRestore] = []
        final_alert = None
        pb = tweaks[TweakID.PosterBoard]
        original_tendies = list(pb.tendies)
        try:
            self._raise_if_unsupported()
            update_label(QCoreApplication.tr("Applying changes to files..."))
            device_values = await self._get_lockdown_values()

            # iOS 26.2+ (iOS 27 era) uses the heavy three-phase protective restore
            pb.tendies = original_tendies[:MAX_TENDIES_PER_RESTORE]
            # fetch a fresh copy of the PosterBoard database before the
            # restore so the config manager builds on the current on-device
            # state. GOLDENNUGGET_SKIP_PB_BACKUP=1 skips the backup.
            if not os.environ.get("GOLDENNUGGET_SKIP_PB_BACKUP"):
                await self._backup_posterboard_database(update_label, force=True)
            final_alert, files_to_restore = await self._apply_tweak_pass(
                update_label,
                templates=tweaks[TweakID.Templates].templates,
                device_values=device_values,
            )
            update_label(QCoreApplication.tr("Success!"))
        except Exception as e:
            final_alert = show_apply_error(e, update_label, files_list=files_to_restore)
        finally:
            pb.tendies = original_tendies
            show_alert(final_alert)

    async def _backup_posterboard_database(self, update_label=lambda x: None, force: bool = False):
        """Fetch the device's PosterBoard sqlite database before applying wallpapers.

        The database (PBFPosterExtensionDataStoreSQLiteDatabase.sqlite3) holds the
        user's current wallpapers. A fresh copy is pulled from the device every
        time a tendie is about to be applied (``force=True``) so the config
        manager always builds on top of the current on-device state. Previously
        fetched copies are only reused when the database is genuinely needed and
        a fresh one isn't required (``force=False``).

        Uses the same mechanism as the "Fetch Database File" wizard
        (``backup_posterboard_database`` in ``src/gui/dialogs/pb_dialog.py``),
        i.e. a full mobilebackup2 backup + Manifest.db lookup. Failure is
        non-fatal: the apply continues and config mode surfaces its own clear
        error later.
        """
        udid = self.get_current_device_udid()
        if not udid:
            return
        # already backed up for this device and no fresh copy required -> reuse it
        if not force and PreferenceManager.has_pbconfig_data(udid):
            return
        pb = tweaks[TweakID.PosterBoard]
        if (len(pb.tendies) == 0 and pb.videoFile is None
                and len(tweaks[TweakID.Templates].templates) == 0):
            # no wallpapers being added, nothing to back up
            return

        update_label(QCoreApplication.tr("Fetching PosterBoard database..."))
        from src.gui.dialogs.pb_dialog import backup_posterboard_database
        try:
            db_file_path = await backup_posterboard_database(udid, update_label)
            if not db_file_path or not os.path.exists(db_file_path):
                raise NuggetException("The PosterBoard database file doesn't exist!")
            update_label(QCoreApplication.tr("Saving PosterBoard database..."))
            if not pb.config_manager.update_database_file(db_file_path, udid):
                raise NuggetException("The PosterBoard database is not of the correct format!")
            pb.config_manager.update_for_saved_database(udid)
            update_label(QCoreApplication.tr("PosterBoard database backed up successfully."))
        except Exception as e:
            print(f"Failed to back up PosterBoard database: {e}")
            print(traceback.format_exc())
            if _is_device_locked_error(e):
                update_label(QCoreApplication.tr("Warning: could not back up PosterBoard database — device is locked. Please unlock your device and try again."))
            else:
                update_label(QCoreApplication.tr("Warning: could not back up the PosterBoard database automatically."))

    async def _get_lockdown_values(self) -> dict:
        udid = self.get_current_device_udid()
        if not udid:
            return {}
        ld = await create_using_usbmux(serial=udid)
        try:
            return dict(ld.all_values)
        finally:
            try:
                await ld.close()
            except Exception:
                pass

    async def _get_current_global_preferences_plist(self) -> Optional[dict]:
        """Read the device's current HomeDomain .GlobalPreferences.plist.

        On iOS 27 the "safe state recovery" wipe clears HomeDomain files that
        are not part of the restore backup. The tweak pass writes its own
        copy of .GlobalPreferences.plist to HomeDomain so tweak keys survive,
        but that copy only carries tweak keys — the user's region, language
        and appearance settings (AppleLanguages, AppleLocale,
        AppleInterfaceStyle, UIBoldText, ...) would be lost. Merging the
        on-device plist into the copy keeps both.

        Returns the parsed plist, or None if it cannot be read (fresh device,
        locked, AFC hiccup) — callers fall back to their own content.
        """
        udid = self.get_current_device_udid()
        if not udid:
            return None
        try:
            ld = await create_using_usbmux(serial=udid)
            try:
                async with AfcService(ld) as afc:
                    data = await afc.get_file_contents(
                        "Library/Preferences/.GlobalPreferences.plist")
            finally:
                try:
                    await ld.close()
                except Exception:
                    pass
            return plistlib.loads(data)
        except Exception as e:
            print(f"Could not read device .GlobalPreferences.plist: {e}")
            return None

    def _get_original_plist_paths(self) -> list[str]:
        return [loc.value for loc in FileLocation]

    async def _capture_original_plists(self, udid: str, update_label) -> dict:
        """Run the psysbackup capture and return usable originals.

        The mobile-user copy (HomeDomain) of a managed-preference file is
        preferred over the managed copy: tweaks and resets write only to
        ``/var/Managed Preferences/mobile/*.plist``, so the HomeDomain copy is
        the truest original even when tweaks were applied before the capture
        ran. The managed copy is used only when no HomeDomain copy exists.
        Entries that are still empty after both sources are dropped — a nulled
        plist must never be stored as an "original", otherwise reset keeps
        restoring the nulled state.
        """
        paths = self._get_original_plist_paths()
        fallbacks = [mobile_user_fallback_path(p) for p in paths]
        fallbacks = [f for f in fallbacks if f is not None and f not in paths]
        captured = await psysbackup(
            udid, paths + fallbacks, update_label, self._backup_progress(update_label), self._get_backup_password())
        originals = {}
        for path in paths:
            data = None
            fallback = mobile_user_fallback_path(path)
            if fallback:
                data = captured.get(fallback)
            if data is None or is_empty_plist(data):
                data = captured.get(path)
            if data is not None and not is_empty_plist(data):
                originals[path] = data
        return originals

    async def _apply_tweak_pass(self, update_label=lambda x: None, templates: list = None, device_values: dict = None):
        """Generate all tweak files and restore them to the device in one pass.

        Returns (alert, files_to_restore) so the caller can surface the result
        and keep the file list for error reporting.
        """
        if templates is None:
            templates = tweaks[TweakID.Templates].templates
        # create the other plists
        flag_plist: dict = {}
        basic_plists: dict = {}
        basic_plists_ownership: dict = {}
        files_data: dict = {}
        uses_domains: bool = False
        # create the restore file list
        files_to_restore: list[FileToRestore] = [
        ]
        tmp_dirs = [] # temporary directory for unzipping pb and template files

        try:
            # set the plist keys
            for tweak_name in tweaks:
                tweak = tweaks[tweak_name]
                if isinstance(tweak, PasscodeThemeTweak):
                    passcode_files = tweak.apply_tweak()
                    if passcode_files is not None and len(passcode_files) > 0:
                        files_to_restore.extend(passcode_files)
                elif isinstance(tweak, BasicPlistTweak) or isinstance(tweak, AdvancedPlistTweak):
                    basic_plists = tweak.apply_tweak(basic_plists)
                    basic_plists_ownership[tweak.file_location] = tweak.owner
                elif isinstance(tweak, NullifyFileTweak):
                    tweak.apply_tweak(files_data)
                    if tweak.enabled and tweak.file_location.value.startswith("/var/mobile/"):
                        uses_domains = True
                elif isinstance(tweak, PosterboardTweak) or isinstance(tweak, TemplatesTweak):
                    tmp_dirs.append(TemporaryDirectory())
                    tweak.apply_tweak(
                        files_to_restore=files_to_restore,
                        output_dir=fix_windows_path(tmp_dirs[len(tmp_dirs)-1].name),
                        templates=templates,
                        version=self.get_current_device_version(),
                        force_pb_refresh=self.pref_manager.auto_refresh_posterboard,
                        update_label=update_label
                    )
                    if tweak.uses_domains():
                        uses_domains = True
                elif isinstance(tweak, StatusBarTweak):
                    # iOS 27: the status bar is Speakeasy, a SpringBoard
                    # feature flag — writing fails due to no write permissions.
                    # The feature is disabled on iOS 27+.
                    flag_plist = tweak.apply_tweak(flag_plist, version=self.get_current_device_version())

            # Generate backup
            update_label(QCoreApplication.tr("Generating backup..."))
            if len(flag_plist) > 0:
                self.concat_file(
                    contents=plistlib.dumps(flag_plist),
                    path=FileLocation.featureflags.value,
                    files_to_restore=files_to_restore
                )
            
            self.add_skip_setup(files_to_restore, uses_domains)
            for location, plist in basic_plists.items():
                if location in basic_plists_ownership:
                    ownership = basic_plists_ownership[location]
                else:
                    ownership = 501
                self.concat_file(
                    contents=plistlib.dumps(plist),
                    path=location.value,
                    files_to_restore=files_to_restore,
                    owner=ownership, group=ownership
                )
            # iOS 27+: Also write .GlobalPreferences.plist to HomeDomain so
            # tweaks that depend on it survive the Phase 3 protective backup restore.
            # ManagedPreferencesDomain is the primary location; HomeDomain is a
            # secondary copy for iOS 27 compatibility. The copy is merged with
            # the device's current on-device plist so the user's region, language
            # and appearance settings survive the "safe state recovery" wipe too
            # (Phase 3 skips this file to avoid overwriting the tweak copy).
            home_plist = basic_plists.get(FileLocation.globalPreferences, {})
            current = await self._get_current_global_preferences_plist()
            if current:
                current.update(home_plist)
                home_plist = current
            self.concat_file(
                contents=plistlib.dumps(home_plist),
                path=FileLocation.globalPreferencesHomeDomain.value,
                files_to_restore=files_to_restore,
                owner=501, group=501
            )

            for location, data in files_data.items():
                if isinstance(data, NullifyFileTweak):
                    ownership = data.owner
                else:
                    ownership = 501
                self.concat_file(
                    contents=data,
                    path=location.value,
                    files_to_restore=files_to_restore,
                    owner=ownership, group=ownership
                )

            # Check if backup encryption is enabled and handle it
            backup_password = ""
            if Version(self.get_current_device_version()) >= Version("27.0"):
                # Check if backup encryption is enabled on device
                check_ld = await create_using_usbmux(serial=self.get_current_device_udid())
                try:
                    async with Mobilebackup2Service(check_ld) as mb:
                        is_encrypted = await mb.get_will_encrypt()
                    if is_encrypted:
                        from PySide6.QtWidgets import QInputDialog
                        if self.pref_manager.use_encrypted_backup:
                            # User wants to keep encryption - ask for password to use it
                            update_label(QCoreApplication.tr("Backup encryption is enabled. We'll use it for the restore."))
                            update_label(QCoreApplication.tr("Please enter your iTunes/Finder backup password:"))
                            password, ok = QInputDialog.getText(
                                None,
                                QCoreApplication.tr("Backup Encryption Password"),
                                QCoreApplication.tr("Enter your iTunes/Finder backup password (required for encrypted restore):"),
                                QLineEdit.Password
                            )
                            if ok and password:
                                backup_password = password
                                from src.restore.protective import log_info
                                log_info("Using existing backup encryption with provided password")
                                update_label(QCoreApplication.tr("Password accepted. Proceeding with encrypted restore..."))
                            else:
                                raise NuggetException(QCoreApplication.tr("Backup password is required for encrypted restore. Please provide the password or disable encryption in iTunes/Finder."))
                        else:
                            # User doesn't want encryption - show friendly error
                            raise NuggetException(QCoreApplication.tr(
                                "Backup encryption is enabled on your iPhone.\n\n"
                                "GoldenNugget needs to temporarily disable it to apply tweaks safely.\n\n"
                                "Please choose one:\n"
                                "1. Disable encryption on your iPhone: Settings → General → Transfer or Reset iPhone → Backup Password → Turn Off\n"
                                "2. Or enable \"Use Encrypted Backups (Experimental)\" in GoldenNugget Settings → enter your backup password when prompted.\n\n"
                                "Tip: Option 1 is simpler if you don't know your backup password."
                            ))
                except Exception as e:
                    if isinstance(e, NuggetException):
                        raise
                    from src.restore.protective import log_warn
                    log_warn(f"Failed to check backup encryption status: {e}")
                finally:
                    try:
                        await check_ld.close()
                    except Exception:
                        pass

            # restore to the device
            final_alert = await self.start_restore(files_to_restore, update_label, backup_password=backup_password)
            return final_alert, files_to_restore
        finally:
            if len(tmp_dirs) > 0:
                for tmp_dir in tmp_dirs:
                    try:
                        tmp_dir.cleanup()
                    except Exception as e:
                        # ignore clean up errors
                        print(str(e))

    ## RESETTING TWEAKS
    def reset_tweaks(self, reset_pages: list[Page], settings: QSettings, update_label=lambda x: None, show_alert=lambda x: None):
        asyncio.run(self._reset_tweaks(reset_pages, settings, update_label, show_alert))
    async def _reset_tweaks(self, reset_pages: list[Page], settings: QSettings, update_label=lambda x: None, show_alert=lambda x: None):
        try:
            self._raise_if_unsupported()
            # create the restore file list
            files_to_restore: list[FileToRestore] = []
            # Capture the device's original plists fresh via psysbackup so the
            # reset can restore the user's files instead of empty ones.
            udid = self.get_current_device_udid()
            if not udid:
                raise NuggetException(QCoreApplication.tr("No device connected."))
            all_values = await self._get_lockdown_values()
            update_label(QCoreApplication.tr("Capturing original plists..."))
            captured = await self._capture_original_plists(udid, update_label)
            original_plists = {}
            for path, data in captured.items():
                try:
                    original_plists[path] = plistlib.loads(data)
                except Exception:
                    continue
            files_to_null: list[str] = []
            uses_domains = False

            # use if-statements instead of match (switch) statements for compatibility with Python 3.9
            for page in reset_pages:
                if page == Page.StatusBar:
                    ## STATUS BAR
                    # iOS 26.2+ (iOS 27 era): the status bar is Speakeasy, a SpringBoard
                    # feature flag — disable it instead of writing the
                    # unread classic statusBarOverrides file. An empty flag
                    # dict (no "Enabled" key) keeps SpringBoard's default
                    # behavior — {"Enabled": False} could be read as
                    # disabling the whole Speakeasy status bar.
                    self.concat_file(
                        contents=plistlib.dumps({
                            "SpringBoard": {
                                "SpeakeasyNewStatusBar": {}
                            }
                        }),
                        path=FileLocation.featureflags.value,
                        files_to_restore=files_to_restore
                    )
                elif page == Page.Springboard:
                    ## SPRINGBOARD
                    files_to_null.append(FileLocation.springboard.value)
                    files_to_null.append(FileLocation.uikit.value)
                elif page == Page.Daemons:
                    ## DAEMONS
                    default_daemons = {
                        "com.apple.magicswitchd.companion": True,
                        "com.apple.security.otpaird": True,
                        "com.apple.dhcp6d": True,
                        "com.apple.bootpd": True,
                        "com.apple.ftp-proxy-embedded": False,
                        "com.apple.relevanced": True
                    }
                    self.concat_file(
                        contents=plistlib.dumps(default_daemons),
                        path=FileLocation.disabledDaemons.value,
                        files_to_restore=files_to_restore,
                        owner=0, group=0
                    )
                    uses_domains = True
                elif page == Page.InternalOptions:
                    ## INTERNAL OPTIONS
                    files_to_null.append(FileLocation.globalPreferences.value)
                    files_to_null.append(FileLocation.appStore.value)
                    files_to_null.append(FileLocation.backboardd.value)
                    files_to_null.append(FileLocation.coreMotion.value)
                    files_to_null.append(FileLocation.pasteboard.value)
                    files_to_null.append(FileLocation.notes.value)

            # add the files to null from the list
            for file_path in files_to_null:
                original = original_plists.get(file_path)
                if original is not None:
                    contents = plistlib.dumps(materialize_plist(original, all_values))
                else:
                    # Restore a valid empty plist instead of a zero-byte
                    # file: on iOS 26.2+ a truncated plist (e.g. an empty
                    # com.apple.springboard.plist) makes SpringBoard crash
                    # at boot, which sends the device into a boot loop. An
                    # empty dict parses fine and makes the system fall back
                    # to its default values.
                    contents = plistlib.dumps({})
                self.concat_file(
                    contents=contents,
                    path=file_path,
                    files_to_restore=files_to_restore
                )

            await self.add_skip_setup(files_to_restore, uses_domains)

            # restore to the device
            final_alert = await self.start_restore(files_to_restore, update_label)
            update_label(QCoreApplication.tr("Success!"))
        except Exception as e:
            final_alert = show_apply_error(e, update_label, files_list=files_to_restore)
        finally:
            show_alert(final_alert)
