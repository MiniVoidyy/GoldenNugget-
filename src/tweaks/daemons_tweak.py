from enum import Enum


# Daemon controls remain user-selectable; keep this empty for compatibility
# with the shared tweak loader's protected-key interface.
DANGEROUS_KEYS = frozenset()

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
        "com.apple.familynotificationd",
        "com.apple.asktod"
    ]
    CrashReports = [
        "com.apple.ReportCrash",
        "com.apple.ReportCrash.Jetsam",
        "com.apple.ReportMemoryException",
        "com.apple.OTACrashCopier",
        "com.apple.aslmanager",
        "com.apple.coresymbolicationd",
        "com.apple.crash_mover",
        "com.apple.crashreportcopymobile",
        "com.apple.DumpBasebandCrash",
        "com.apple.DumpPanic",
        "com.apple.logd",
        "com.apple.logd.admin",
        "com.apple.logd.events",
        "com.apple.logd.watchdog",
        "com.apple.logd_helper",
        "com.apple.logd_reporter",
        "com.apple.logd_reporter.report_statistics",
        "com.apple.system.logger",
        "com.apple.hangreporter",
        "com.apple.hangtracerd",
        "com.apple.spindump",
        "com.apple.tailspind",
        "com.apple.syslogd",
        "com.apple.signpost.signpost_reporter",
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
    # --- Safe additions (from MiniVoidyy/GoldenNugget-) grouped by function.
    # Only daemons whose disable is safe and not already removed/disabled by iOS.
    AppleAds = [
        "com.apple.promotedcontentd",
        "com.apple.adprivacyd",
        "com.apple.adservicesd"
    ]
    News = ["com.apple.newsd"]
    AskPermissions = ["com.apple.askpermissiond"]
    FamilySharing = [
        "com.apple.familycircled",
        "com.apple.familynotificationd"
    ]
    VideoSubscriptions = ["com.apple.videosubscriptionsd"]
    WebBookmarks = ["com.apple.webbookmarksd"]
    AppleWatchNano = [
        "com.apple.nanoregistryd",
        "com.apple.nanomediacontrold",
        "com.apple.nanopreferencesd"
    ]
    SiriServices = [
        "com.apple.siriactionsd",
        "com.apple.siriinferenced",
        "com.apple.assistant.intentdaemon"
    ]
    Feedback = ["com.apple.feedbackd"]
    Commerce = ["com.apple.commerce"]
    Automount = ["com.apple.automountd"]
    WifiLogging = ["com.apple.wifilogd"]
    Maps = ["com.apple.geod"]
    SafariSuggestions = ["com.apple.parsecd"]
    Shazam = ["com.apple.shazamd"]
    SettingsStats = ["com.apple.settings-statsd"]
    StatusKit = ["com.apple.statuskit"]
    Reminders = ["com.apple.reminderd"]
    AirPlay = ["com.apple.airplay"]
    GameKitService = ["com.apple.gamekitservice"]
    Sidecar = ["com.apple.sidecarcore"]
    SpeechRecognition = ["com.apple.speechrecognition"]
    Translate = ["com.apple.translated"]
    MockLocation = ["com.apple.mocksynclocationd"]
    DeviceCheck = ["com.apple.devicecheckd"]
    # --- Safe analytics/telemetry additions (from MiniVoidyy/GoldenNugget-) ---
    # Telemetry/analytics daemons ONLY. Nothing boot-critical, no core
    # wireless/cellular/auth services. These mirror the fork's curated
    # "Recommended" analytics set, whose disable is confirmed safe.
    WifiAnalytics = ["com.apple.wifianalyticsd"]
    AnalyticsHelper = [
        "com.apple.analyticsd",
        "com.apple.analyticsd.admin",
        "com.apple.analyticsd.events"
    ]
    AudioAnalytics = ["com.apple.audioanalyticsd"]
    EcosystemAnalytics = ["com.apple.ecosystemanalyticsd"]
    CallAnalytics = ["com.apple.rtcreportingd"]
    CoreDuet = ["com.apple.coreduetd"]
    Insight = ["com.apple.insightd"]
    Metrics = ["com.apple.metricsd"]
    MediaExperience = ["com.apple.mediaremoted"]
    Symptomsd = ["com.apple.symptomsd", "com.apple.symptomsd-app"]
    StatisticalDiagnostic = ["com.apple.StatisticalDiagnosticService"]
    WirelessDiagnostics = ["com.apple.wirelessdiagnostics"]
    DuetHeuristic = [
        "com.apple.DuetHeuristic-BM",
        "com.apple.DuetHeuristic-BM.Baseband"
    ]
    DuetExpert = ["com.apple.duetexpertd"]
    Decisiond = ["com.apple.decisiond"]
    Triald = ["com.apple.triald"]
    Sociald = ["com.apple.sociald"]
    BatteryUsage = [
        "com.apple.powerlogd",
        "com.apple.powerlogHelperd"
    ]
    # --- Extended analytics / tracking / telemetry set (50 additional) ---
    # Analytics & telemetry reporting daemons.
    Aggregated = ["com.apple.aggregated"]
    Geniusd = ["com.apple.appleseedd"]
    MobileAssetd = ["com.apple.mobileassetd"]
    OTAPackd = ["com.apple.otapackd"]
    CoreCaptured = ["com.apple.corecaptured"]
    Pcapd = ["com.apple.pcapd"]
    IMETrafficCollector = ["com.apple.imetrafficcollector"]
    CoreTelephonyAnalytics = ["com.apple.commcenter.coretelephony"]
    CoreTelephony = ["com.apple.coretelephony"]
    Runwayd = ["com.apple.generatord"]
    Mld = ["com.apple.mlt"]
    AppStoreAnalytics = ["com.apple.appstored"]
    CommerceAnalytics = ["com.apple.Commerced"]
    SaleAnalytics = ["com.apple.saled"]
    RepairAnalytics = ["com.apple.repaird"]
    Recalibration = ["com.apple.recalibrationd"]
    PrivacyAnalytics = ["com.apple.privacyd"]
    SafetyAlerts = ["com.apple.safetyalertsd"]
    CipherMining = ["com.apple.cipherminingd"]
    LifeScienceAnalytics = ["com.apple.lifescienced"]
    # Tracking / inference daemons.
    SiriKnowledge = ["com.apple.siriknowledged"]
    SiriUnattended = ["com.apple.siriunattended"]
    SiriService = ["com.apple.SiriService"]
    SiriCore = ["com.apple.siri"]
    SearchPartyd = ["com.apple.searchpartyd"]
    Nearbyd = ["com.apple.nearbyd"]
    NearbyInteraction = ["com.apple.nearbyinteractiond"]
    FindMyDevice = ["com.apple.findmydeviced"]
    FindMyLocate = ["com.apple.findmylocate"]
    GazeTracking = ["com.apple.gaze"]
    Sportskitd = ["com.apple.sportskitd"]
    Watchlistd = ["com.apple.watchlistd"]
    ARKitTracking = ["com.apple.arkitd"]
    FaceTracking = ["com.apple.faced"]
    MediaTracking = ["com.apple.mediasessiond"]
    MediaRemoteControl = ["com.apple.mediaremotecontrol"]
    IMessageTracking = ["com.apple.imagent"]
    IMFoundation = ["com.apple.imfoundation"]
    IMTranscoding = ["com.apple.imtranscodingagent"]
    ContinuityTracking = ["com.apple.continuityd"]
    # Logging / diagnostics / crash reporting.
    Osanalyticsd = ["com.apple.osanalyticsd"]
    Microstackshots = ["com.apple.microstackshots"]
    StackshotServer = ["com.apple.stackshot.server"]
    CrashReporterSupport = ["com.apple.CrashReporterSupportHelper"]
    AccountAnalytics = ["com.apple.appleaccountd"]
    SystemLogger = ["com.apple.system.logger"]
    AppleIDServiced = ["com.apple.appleidservice"]
    CloudPhotoAnalytics = ["com.apple.cloudphotod"]
    CloudStorage = ["com.apple.cloudd"]
    CloudKeychain = ["com.apple.cloudkeychainproxy"]


# Safe one-tap analytics/telemetry disable set — the "Recommended" switch in
# the daemons UI. This is EVERY analytics / tracking / telemetry / logging
# daemon the app exposes: the analytics/telemetry entries from the main
# "System & App Services" section PLUS the whole "Analytics & Diagnostics"
# section of src/gui/ios/daemons.py. Keep it in sync with that page — the
# Recommended switch must be able to toggle everything analytics-related.
RECOMMENDED_ANALYTICS = [
    # Main-section analytics/telemetry entries.
    Daemon.Diagnostics, Daemon.UsageTrackingAgent,
    Daemon.AppleAds, Daemon.FollowUp, Daemon.Feedback, Daemon.Shazam,
    Daemon.SettingsStats,
    # Analytics & Diagnostics section (base set).
    Daemon.CrashReports, Daemon.WifiAnalytics, Daemon.AnalyticsHelper,
    Daemon.AudioAnalytics, Daemon.EcosystemAnalytics,
    Daemon.CallAnalytics, Daemon.CoreDuet, Daemon.Insight, Daemon.Metrics,
    Daemon.MediaExperience, Daemon.Symptomsd, Daemon.StatisticalDiagnostic,
    Daemon.WirelessDiagnostics, Daemon.DuetHeuristic, Daemon.DuetExpert,
    Daemon.Decisiond, Daemon.Triald, Daemon.Sociald,
    # Analytics & Diagnostics section (extended set).
    Daemon.Aggregated, Daemon.Geniusd, Daemon.MobileAssetd, Daemon.OTAPackd,
    Daemon.CoreCaptured, Daemon.Pcapd,
    Daemon.IMETrafficCollector, Daemon.CoreTelephonyAnalytics,
    Daemon.CoreTelephony, Daemon.Runwayd, Daemon.Mld,
    Daemon.AppStoreAnalytics, Daemon.CommerceAnalytics,
    Daemon.SaleAnalytics, Daemon.RepairAnalytics, Daemon.Recalibration,
    Daemon.PrivacyAnalytics, Daemon.SafetyAlerts, Daemon.CipherMining,
    Daemon.LifeScienceAnalytics, Daemon.SiriKnowledge, Daemon.SiriUnattended,
    Daemon.SiriService, Daemon.SiriCore, Daemon.SearchPartyd, Daemon.Nearbyd,
    Daemon.NearbyInteraction, Daemon.FindMyDevice, Daemon.FindMyLocate,
    Daemon.GazeTracking, Daemon.Sportskitd, Daemon.Watchlistd,
    Daemon.ARKitTracking, Daemon.FaceTracking, Daemon.MediaTracking,
    Daemon.MediaRemoteControl, Daemon.IMessageTracking, Daemon.IMFoundation,
    Daemon.IMTranscoding, Daemon.ContinuityTracking, Daemon.Osanalyticsd,
    Daemon.Microstackshots, Daemon.StackshotServer, Daemon.CrashReporterSupport,
    Daemon.AccountAnalytics, Daemon.SystemLogger, Daemon.AppleIDServiced,
    Daemon.CloudPhotoAnalytics, Daemon.CloudStorage, Daemon.CloudKeychain,
]

# Interface-visible daemons: the switches on the Daemons page plus the
# one-tap Recommended set. Any enum member without a visible control is
# excluded from stored presets and the apply pass.
INTERFACE_DAEMONS: frozenset["Daemon"] = frozenset({
    # main "Disable" section (src/gui/ios/daemons.py)
    Daemon.thermalmonitord, Daemon.OTA, Daemon.UsageTrackingAgent,
    Daemon.GameCenter, Daemon.ATWAKEUP, Daemon.Tips, Daemon.VPN,
    Daemon.ChineseLAN, Daemon.HealthKit, Daemon.AirPrint,
    Daemon.AssistiveTouch, Daemon.iCloud, Daemon.InternetTethering,
    Daemon.PassBook, Daemon.Spotlight, Daemon.NanoTimeKit,
    Daemon.VoiceControl, Daemon.FollowUp, Daemon.Location,
    Daemon.News, Daemon.FamilySharing, Daemon.VideoSubscriptions,
    Daemon.WebBookmarks, Daemon.AppleWatchNano, Daemon.SiriServices,
    Daemon.WifiLogging, Daemon.Maps, Daemon.SafariSuggestions,
    Daemon.Reminders, Daemon.AirPlay, Daemon.GameKitService,
    Daemon.Sidecar, Daemon.SpeechRecognition, Daemon.Translate,
    Daemon.MockLocation, Daemon.DeviceCheck,
    Daemon.ScreenTime, Daemon.BatteryUsage,
    # analytics / telemetry section
    Daemon.CrashReports, Daemon.WifiAnalytics, Daemon.AnalyticsHelper, Daemon.CallAnalytics,
    Daemon.AudioAnalytics, Daemon.EcosystemAnalytics,
    Daemon.CoreDuet, Daemon.Insight, Daemon.Metrics, Daemon.MediaExperience,
    Daemon.Symptomsd, Daemon.StatisticalDiagnostic, Daemon.WirelessDiagnostics,
    Daemon.DuetHeuristic, Daemon.DuetExpert, Daemon.Decisiond, Daemon.Triald,
    Daemon.Sociald,
    # extended analytics / tracking / telemetry set
    Daemon.MobileAssetd, Daemon.OTAPackd, Daemon.CoreTelephony,
    Daemon.RepairAnalytics, Daemon.SafetyAlerts,
    Daemon.SiriKnowledge, Daemon.SiriUnattended, Daemon.SiriService,
    Daemon.SiriCore, Daemon.SearchPartyd, Daemon.Nearbyd,
    Daemon.NearbyInteraction, Daemon.FindMyDevice, Daemon.FindMyLocate,
    Daemon.GazeTracking, Daemon.Sportskitd, Daemon.Watchlistd,
    Daemon.ARKitTracking, Daemon.FaceTracking, Daemon.MediaTracking,
    Daemon.MediaRemoteControl, Daemon.IMessageTracking, Daemon.IMFoundation,
    Daemon.IMTranscoding, Daemon.ContinuityTracking, Daemon.AppleIDServiced,
    Daemon.CloudPhotoAnalytics, Daemon.CloudStorage, Daemon.CloudKeychain,
} | set(RECOMMENDED_ANALYTICS))

# Interface-visible daemon keys: everything a user can toggle in the UI.
# Any key outside this set is stripped from presets / the apply pass.
INTERFACE_KEYS = frozenset(k for d in INTERFACE_DAEMONS for k in d.value)
