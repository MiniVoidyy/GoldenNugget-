from .tweak_names import TweakID
from .tweak_classes import FeatureFlagTweak, BasicPlistTweak, AdvancedPlistTweak, NullifyFileTweak
from .posterboard.posterboard_tweak import PosterboardTweak
from .posterboard.template_options.templates_tweak import TemplatesTweak
from .status_bar.status_bar_tweak import StatusBarTweak
from .passcode_theme_tweak import PasscodeThemeTweak
    
tweaks = {
    ## PosterBoard
    TweakID.PosterBoard: PosterboardTweak(),

    ## Templates
    TweakID.Templates: TemplatesTweak(),

    ## Status Bar
    TweakID.StatusBar: StatusBarTweak(),

    ## Passcode Theme
    TweakID.Passcode: PasscodeThemeTweak(),
}