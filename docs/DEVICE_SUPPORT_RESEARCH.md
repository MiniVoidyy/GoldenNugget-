# Preference and service research

Investigated October 15, 2026. Follow-up research after PR #56.

## Service candidates

No new disable switches or purported live diagnostics were added for these
services. Their names do not establish their launchd labels, writable override
paths, or whether iOS 27 honors an override. Likewise, a diagnostics viewer
requires an actual readable device service/data source; an information card
cannot substitute for measured diagnostics.

| Candidate | Proposed direction | Finding / remaining requirement |
| --- | --- | --- |
| `batteryintelligenced` | Battery intelligence viewer | Referenced by the 27.2 beta sandbox diff. Need a readable battery-intelligence data source and actual launchd metadata. Existing battery percentage is not this service's intelligence output. |
| `memoryanalyticsd` | Memory diagnostics | Listed under removed executables in the 27.0 prerelease-to-release diff. Do not assume it is present on current devices. Need per-build presence and a memory diagnostic reader. |
| `anomalydetectiond` | Anomaly diagnostics | Referenced in a later 27.2 sandbox diff. Need an accessible output/schema; disabling remains unverified. |
| `gamepolicyd` | Gaming performance research | A historical executable reference is insufficient to establish a current launchd target or a supported performance control. |
| `biomesyncd` | Background intelligence explorer | Need validated service metadata and a permitted, scoped data source. No reliable read/disable route established. |
| `eligibilityd` | Read-only eligibility diagnostics | Keep separate from existing eligibility modifications. Need a verified read-only query/schema. |
| `eventkitsyncd` | Calendar synchronization diagnostics | Need a readable synchronization status source. Disabling may affect calendar functionality; no current disable behavior established. |
| `mlhostd` | ML service viewer | Need verified process/service metadata and readable ML status. No current read/disable route established. |
| `inboxupdaterd` | Background inbox diagnostics | Referenced in the 27.2 beta sandbox diff. This does not identify a safe override or readable inbox diagnostic schema. |
| `visioncompaniond` | Device-specific explorer | Need model-specific presence and capability evidence. Do not expose universally based on the name. |
| `icloudmailagent` | iCloud Mail information | Need a supported data source. Do not equate absence of logs with absence of the service or assume disabling is safe for mail. |
| `countryd` | Region-service diagnostics | Referenced in the 27.2 beta sandbox diff. Need a documented/readable output and verified label; no region override was inferred. |

Primary diff references:

- [27.0 prerelease → release](https://github.com/blacktop/ipsw-diffs/blob/main/iOS/27_0_24A5430a_vs_27_0_24A435/README.md).
- [27.2 build 24B5089g → 24B5099f](https://github.com/blacktop/ipsw-diffs/blob/main/iOS/27_2_24B5089g_vs_27_2_24B5099f/README.md).
- [27.2 build 24B5099f → 24B5110a](https://github.com/blacktop/ipsw-diffs/blob/main/iOS/27_2_24B5099f_vs_27_2_24B5110a/README.md).

Diffs describe changes between particular images. A service not mentioned in a
diff is not necessarily absent. An executable or sandbox reference alone does
not prove a writable preference or launchd-disable mechanism.

## Other preference domains from the attachment

`com.apple.Preferences`, `com.apple.controlcenter`, `com.apple.Accessibility`,
`com.apple.MobileSMS`, `com.apple.camera`, `com.apple.Photos`, and keyboard/text
input domains remain research targets. No additional key/path was inferred
from a domain name. Existing SpringBoard, UIKit, Notes, pasteboard, motion, and
diagnostic options were not duplicated.

## Passcode Theme range

The requested UI policy is iOS 27.0 through 27.2 beta 3, inclusive. The supplied
beta-3 build is `24B5099f`. The earlier `24B5084k` and `24B5089g` builds are listed
in the same ipsw-diffs comparison sequence. Only these explicit 27.2 builds
are allowed; a plain ProductVersion of `27.2` is not proof of beta 3.

- iPhone versions from 27.0 up to, but excluding, 27.2 are allowed.
- 27.2 is allowed only for those three recognized builds.
- Earlier/later versions, unknown 27.2 builds, non-iPhones, and missing metadata
  are disabled with an explanation on the Home card.
- The page and worker repeat the gate before a device write, and the
  compatibility dialog uses the same helper.

This is an availability gate, not a claim that every allowed device/build has
been tested successfully with AirLift. Existing build warnings remain.
