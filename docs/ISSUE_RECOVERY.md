# Recovery for issues #58 and #59

## Missing missed-call notifications (#58)

The report associates the failure with the previous Recommended daemon set
and Disable Spotlight. It does not isolate a single responsible service.
The Recommended shortcut now excludes shared system services, including
CoreDuet, MediaRemote, Duet Expert, RTC reporting, and Follow Up.

For a device already affected, open Daemons and select **Restore Call
Notification Services**, then apply changes and reboot. This prepares explicit
`false` disabled-daemon overrides for Spotlight and the entire previous
Recommended set, including settings loaded from old presets. Merely removing
services from the shortcut would leave previous disabled overrides in place.
Unrelated daemon settings are preserved. HotLoad-locked services stay disabled.

Confirm the result with a missed call on the affected device. Device validation
is still required; the report alone does not establish the precise dependency
or guarantee this resolves every notification failure.

## PosterBoard database not selected (#59)

An automatic PosterBoard database fetch failure now stops apply before any
restore, preserving the original connection, validation, encryption, or storage
error. A locked-device failure asks the user to unlock and keep the device
awake. A failed fresh fetch never silently falls back to an older selected
database. Resolve the reported cause, then retry; do not replace the database
with an empty file.

Offline coverage: `tools/test_active_issues.py`.
