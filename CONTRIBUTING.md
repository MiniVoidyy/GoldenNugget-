# note: This is 8.x branch (main, stable) only bug fixes accepts here. For development use 9.0 branch (unstable) but be ready for rapid changes
# contribute guide
## 1. about AI usage
# 1. Terms of AI use 
AI is currently one of the best tools to help development\
but YOU must test code on YOUR device before creating PR\
Any untested or too unstable code will be REJECTED
# 2. How to send evidence of test?
You must add screen-shots or video of your code working correctly.\
And as i said already if there is NO EVIDENCE of work, your PR will be auto-rejected.
## 2. Bug Fixes
About bug fixes.\
This fixes shouldn't cause more bugs. Even trough nugget was ALWAYS really unstable in long perspective\
I still want to have normal stability\
That's all.
## 3. New Features
# 1. QOL (goldennugget app features)
New features should NOT be useless.\
GoldenNugget is already a HUGE project. And i don't want to turn goldennugget into "elephant" or superapp.
# 2. Tweaks (New features for customization)
As a "new tweaks" i accept:
1. Old tweaks on new IOS versions
2. New plist-based tweaks (like easyspeak workaround on iOS 27)
3. New exploit-based tweaks (like bookrestore/sparserestore)
## 4. Pull Request Naming Convention

To keep the repository history clean and easy to read, please use the following tags at the beginning of your PR title:

* **[TWEAK]** - For new iOS tweaks or plist modifications.
* **[FIX]** - For bug fixes and stability improvements.
* **[QOL]** - For app features, UI changes, or overall GoldenNugget improvements.
* **[DOCS]** - For updates to the README, documentation, or this guide.

**Good PR Titles:**
* `[TWEAK] Add easyspeak (status bar) support for iOS 27`
* `[FIX] Fix SEGV after restore`
* `[QOL] Improve logging`

**Bad PR Titles:**
* `fixed bug`
* `added new tweak please merge`
* `update`

If your PR does not follow this format, you need to rename it before it gets reviewed.
# End
That's all, i hope this guideline was useful.\
You can leave you opinion about it in discussion.\
Written entirely by awesomenull. can be updated anytime, already created pull requests will not be affected in case of update.
