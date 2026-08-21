from .tweaks import tweaks, TweakID
from .registry import SPECS
from .basic_plist_locations import FileLocation
from .tweak_classes import BasicPlistTweak, AdvancedPlistTweak, NullifyFileTweak


def _build_spec(spec):
    if spec.factory is not None:
        return spec.factory()
    return BasicPlistTweak(spec.location, spec.key, value=spec.value)


def load_plist_tweaks():
    """Register every registry-defined tweak that isn't loaded yet (idempotent)."""
    tweaks.update({spec.id: _build_spec(spec) for spec in SPECS if spec.id not in tweaks})


# Kept as thin aliases — classic pages and preset_manager call the per-group names.
def load_internal():
    load_plist_tweaks()
def load_liquidglass():
    load_plist_tweaks()
def load_springboard():
    load_plist_tweaks()


def load_daemons():
    if TweakID.Daemons in tweaks:
        return
    tweaks.update({
        TweakID.Daemons: AdvancedPlistTweak(
            FileLocation.disabledDaemons,
            {
                "com.apple.magicswitchd.companion": True,
                "com.apple.security.otpaird": True,
                "com.apple.dhcp6d": True,
                "com.apple.bootpd": True,
                "com.apple.ftp-proxy-embedded": False,
                "com.apple.relevanced": True
            },
            owner=0, group=0
        ),
        TweakID.ClearScreenTimeAgentPlist: NullifyFileTweak(FileLocation.screentime),
    })