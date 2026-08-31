from enum import Enum, auto


class Daemon(Enum):
    thermalmonitord = ["com.apple.thermalmonitord"]
    OTA = [
        "com.apple.mobile.softwareupdated",
        "com.apple.OTATaskingAgent",
        "com.apple.softwareupdateservicesd",
        "com.apple.mobile.NRDUpdated"
    ]
    UsageTrackingAgent = ["com.apple.UsageTrackingAgent"]
    GameCenter = ["com.apple.gamed"]
    ScreenTime = [
        "com.apple.ScreenTimeAgent",
        "com.apple.homed",
        "com.apple.familycircled",
        "com.apple.familynotification",
        "com.apple.asktod"
    ]
    CrashReports = [
        "com.apple.ReportCrash",
        "com.apple.ReportCrash.Jetsam",
        "com.apple.ReportMemoryException",
        "com.apple.OTACrashCopier",
        "com.apple.analyticsd",
        "com.apple.wifianalyticsd",
        "com.apple.aslmanager",
        "com.apple.coresymbolicationd",
        "com.apple.crash_mover",
        "com.apple.crashreportcopymobile",
        "com.apple.DumpBasebandCrash",
        "com.apple.DumpPanic",
        "com.apple.rtcreportingd",
        "com.apple.pluginkit.pkreporter",
        "com.apple.ProxiedCrashCopier",
        "com.apple.ProxiedCrashCopier.ProxyingDevice",
        "com.apple.ReportSystemMemory"
    ]
    Diagnostics = [
        "com.apple.diagnosticd",
        "com.apple.diagnosticextensionsd",
        "com.apple.diagnosticservicesd",
        "com.apple.diagnosticspushd",
        "com.apple.symptomsd-diag",
        "com.apple.sysdiagnose",
        "com.apple.sysdiagnose.darwinos",
        "com.apple.sysdiagnose_helper"
    ]
    ATWAKEUP = ["com.apple.atc.atwakeup"]
    Tips = ["com.apple.tipsd"]
    VPN = ["com.apple.racoon"]
    Location = ["com.apple.locationd"]
    ChineseLAN = [
        "com.apple.wapic",
        "com.apple.wifi.wapic"
    ]
    HealthKit = ["com.apple.healthd"]
    AirPrint = ["com.apple.printd"]
    AssistiveTouch = ["com.apple.assistivetouchd"]
    iCloud = ["com.apple.itunescloudd"]
    InternetTethering = ["com.apple.MobileInternetSharing"]
    PassBook = ["com.apple.passd"]
    Spotlight = [
        "com.apple.searchd",
        "com.apple.corespotlightservice",
        "com.apple.spotlightknowledged",
        "com.apple.spotlightknowledged.updater",
        "com.apple.spotlight.IndexAgent"
    ]
    VoiceControl = [
        "com.apple.assistant_service",
        "com.apple.assistantd",
        "com.apple.voiced"
    ]
    NanoTimeKit = ["com.apple.nanotimekitcompaniond"]
    FollowUp = ["com.apple.followupd"]
    PromotedContent = ["com.apple.promotedcontentd"]
    WifiAnalytics = ["com.apple.wifianalyticsd"]
    News = ["com.apple.newsd"]
    AskPermissions = ["com.apple.askpermissiond"]
    FamilyCircle = ["com.apple.familycircled"]
    FamilyNotification = ["com.apple.familynotificationd"]
    AdPrivacy = ["com.apple.adprivacyd"]
    AdServices = ["com.apple.adservicesd"]
    VideosSubscriptions = ["com.apple.videosubscriptionsd"]
    WebBookmarks = ["com.apple.webbookmarksd"]
    NanoRegistry = ["com.apple.nanoregistryd"]
    NanoMediaControl = ["com.apple.nanomediacontrold"]
    NanoPreferences = ["com.apple.nanopreferencesd"]
    SiriActions = ["com.apple.siriactionsd"]
    SiriInference = ["com.apple.siriinferenced"]
    Feedback = ["com.apple.feedbackd"]
    Commerce = ["com.apple.commerce"]
    CoreDuet = ["com.apple.coreduetd"]
    Insight = ["com.apple.insightd"]
    Metrics = ["com.apple.metricsd"]
    AnalyticsHelper = [
        "com.apple.analyticsd",
        "com.apple.analyticsd.admin",
        "com.apple.analyticsd.events"
    ]
    CallAnalytics = ["com.apple.rtcreportingd"]
    Symptomsd = ["com.apple.symptomsd", "com.apple.symptomsd-app"]
    MobileAssetd = ["com.apple.mobileassetd"]
    Ubiquityd = ["com.apple.ubd"]
    CoreTelephonyAnalytics = ["com.apple.commcenter.coretelephony"]
    MediaExperience = ["com.apple.mediaremoted"]
    Automount = ["com.apple.automountd"]
    SiriIntent = ["com.apple.assistant.intentdaemon"]
    CloudKeychain = ["com.apple.cloudkeychainproxy", "com.apple.security.cloudkeychainproxy"]
    NetworkExtension = ["com.apple.networkextension"]
    DeviceCheck = ["com.apple.devicecheckd"]
    ManagedConfiguration = ["com.apple.managedconfiguration", "com.apple.managedconfiguration.mdm", "com.apple.managedconfiguration.tesla"]
    Containermanagerd = ["com.apple.containermanagerd"]
    MobileGestaltHelper = ["com.apple.mobilegestalt_helper"]
    TimeSync = ["com.apple.timed"]
    MockLocation = ["com.apple.mocksynclocationd"]
    Persistence = ["com.apple.persistence-helper", "com.apple.persistence-d"]
    Calendar = ["com.apple.calendar.database", "com.apple.CalendarAgent"]
    DataAccess = ["com.apple.dataaccess.dataaccessd"]
    Networkd = ["com.apple.networkd"]
    Privacy = ["com.apple.privacyd"]
    AppStore = ["com.apple.appstored"]
    Books = ["com.apple.bookdatastored"]
    Podcasts = ["com.apple.podcasts"]
    UserNotifications = ["com.apple.usernotificationsd"]
    Photos = ["com.apple.photolibraryd"]
    Music = ["com.apple.itunesstored"]
    AppleAccount = ["com.apple.appleaccountd"]
    Bluetooth = ["com.apple.bluetoothd"]
    WiFiManager = ["com.apple.wifi_manager"]
    WiFiLogging = ["com.apple.wifilogd"]
    Maps = ["com.apple.geod"]
    HealthSync = ["com.apple.healthd.sync"]
    AccountSync = ["com.apple.accountsd"]
    DiskArbitration = ["com.apple.DiskArbitrationd"]
    MediaRemoteControl = ["com.apple.mediaremotecontrol"]
    Notifications = ["com.apple.notificationd"]
    Parse = ["com.apple.parsecd"]
    Shazam = ["com.apple.shazamd"]
    Siri = ["com.apple.siri"]
    SettingsStats = ["com.apple.settings-statsd"]
    StatusKit = ["com.apple.statuskit"]
    Reminders = ["com.apple.reminderd"]
    ConfigurationProfiles = ["com.apple.managedconfigurationprofiles"]
    CertificateRevocation = ["com.apple.security.certrevocation"]
    EAP = ["com.apple.eapolclient"]
    AirPlay = ["com.apple.airplay"]
    iCloudContainer = ["com.apple.cloudd"]
    GameKitService = ["com.apple.gamekitservice"]
    NFC = ["com.apple.nfcd"]
    UARTPairing = ["com.apple.uarpairingd"]
    Sidecar = ["com.apple.sidecarcore"]
    Continuity = ["com.apple.continuityd"]
    Sharing = ["com.apple.sharingd"]
    FindMy = ["com.apple.findmylocate", "com.apple.findmydeviced"]
    NearbyInteraction = ["com.apple.nearbyinteractiond"]
    SignpostReporter = ["com.apple.signpost.signpost_reporter"]
    CoreTelephony = ["com.apple.coretelephony"]
    MediaSession = ["com.apple.mediasessiond"]
    SpeechRecognition = ["com.apple.speechrecognition"]
    ReplayKit = ["com.apple.replayd"]
    CoreBluetooth = ["com.apple.corebluetoothd"]


class DaemonCategory(Enum):
    """UI grouping for the standalone daemon toggles."""
    LOGGING = "Logging"
    ANALYTICS = "Analytics"
    TRACKING = "Tracking"
    OTHER = "Other"


# Category tag for every standalone daemon toggle. Determines which
# IOSSectionHeader the daemon appears under in the daemons page.
DAEMON_CATEGORY = {
    # Logging / crash-report / diagnostic capture
    Daemon.CrashReports: DaemonCategory.LOGGING,
    Daemon.Diagnostics: DaemonCategory.LOGGING,
    Daemon.WiFiLogging: DaemonCategory.LOGGING,
    Daemon.SignpostReporter: DaemonCategory.LOGGING,
    Daemon.Symptomsd: DaemonCategory.LOGGING,

    # Analytics / telemetry / usage / advertising data
    Daemon.UsageTrackingAgent: DaemonCategory.ANALYTICS,
    Daemon.WifiAnalytics: DaemonCategory.ANALYTICS,
    Daemon.AnalyticsHelper: DaemonCategory.ANALYTICS,
    Daemon.CallAnalytics: DaemonCategory.ANALYTICS,
    Daemon.CoreDuet: DaemonCategory.ANALYTICS,
    Daemon.Insight: DaemonCategory.ANALYTICS,
    Daemon.Metrics: DaemonCategory.ANALYTICS,
    Daemon.AdPrivacy: DaemonCategory.ANALYTICS,
    Daemon.AdServices: DaemonCategory.ANALYTICS,
    Daemon.PromotedContent: DaemonCategory.ANALYTICS,
    Daemon.Commerce: DaemonCategory.ANALYTICS,
    Daemon.SettingsStats: DaemonCategory.ANALYTICS,
    Daemon.StatusKit: DaemonCategory.ANALYTICS,
    Daemon.MediaExperience: DaemonCategory.ANALYTICS,
    Daemon.DataAccess: DaemonCategory.ANALYTICS,
    Daemon.Feedback: DaemonCategory.ANALYTICS,
    Daemon.News: DaemonCategory.ANALYTICS,
    Daemon.VideosSubscriptions: DaemonCategory.ANALYTICS,
    Daemon.WebBookmarks: DaemonCategory.ANALYTICS,
    Daemon.MobileAssetd: DaemonCategory.ANALYTICS,
    Daemon.NanoRegistry: DaemonCategory.ANALYTICS,
    Daemon.CoreTelephonyAnalytics: DaemonCategory.ANALYTICS,

    # Tracking / activity / on-device behavior & suggestions
    Daemon.SiriInference: DaemonCategory.TRACKING,
    Daemon.SiriActions: DaemonCategory.TRACKING,
    Daemon.SiriIntent: DaemonCategory.TRACKING,
    Daemon.Siri: DaemonCategory.TRACKING,
    Daemon.FollowUp: DaemonCategory.TRACKING,
    Daemon.Parse: DaemonCategory.TRACKING,
    Daemon.Spotlight: DaemonCategory.TRACKING,
    Daemon.GameCenter: DaemonCategory.TRACKING,
    Daemon.GameKitService: DaemonCategory.TRACKING,
    Daemon.Shazam: DaemonCategory.TRACKING,
    Daemon.Location: DaemonCategory.TRACKING,
    Daemon.VoiceControl: DaemonCategory.TRACKING,
    Daemon.ScreenTime: DaemonCategory.TRACKING,
    Daemon.AskPermissions: DaemonCategory.TRACKING,
    Daemon.AccountSync: DaemonCategory.TRACKING,
    Daemon.NanoMediaControl: DaemonCategory.TRACKING,
    Daemon.NanoTimeKit: DaemonCategory.TRACKING,
    Daemon.Ubiquityd: DaemonCategory.TRACKING,
}


def daemon_category(daemon: Daemon) -> DaemonCategory:
    """Return the UI category for a daemon, defaulting to OTHER."""
    return DAEMON_CATEGORY.get(daemon, DaemonCategory.OTHER)


class DaemonGroup(Enum):
    """Grouped selections that enable a set of daemons in one tap."""
    Recommended = auto()


# Analytics / telemetry / tracking daemons selected by "Recommended".
# Disabling these reduces data collection while keeping core device
# functionality intact. Core logging/cellular/security daemons are
# intentionally EXCLUDED to avoid boot/setup loops.
RECOMMENDED_ANALYTICS = [
    Daemon.CrashReports,
    Daemon.Diagnostics,
    Daemon.UsageTrackingAgent,
    Daemon.WifiAnalytics,
    Daemon.AnalyticsHelper,
    Daemon.CallAnalytics,
    Daemon.AdPrivacy,
    Daemon.AdServices,
    Daemon.PromotedContent,
    Daemon.News,
    Daemon.VideosSubscriptions,
    Daemon.WebBookmarks,
    Daemon.CoreDuet,
    Daemon.Insight,
    Daemon.Metrics,
    Daemon.Feedback,
    Daemon.SiriInference,
    Daemon.SiriActions,
    Daemon.FollowUp,
    Daemon.StatusKit,
    Daemon.MediaExperience,
    Daemon.Commerce,
    Daemon.DataAccess,
    Daemon.Symptomsd,
    Daemon.SettingsStats,
    Daemon.GameCenter,
    Daemon.Shazam,
]
