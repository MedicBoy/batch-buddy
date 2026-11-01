# ActivitySmith, native Live Activity, and CarPlay

Batch Buddy uses two delivery paths:

1. ActivitySmith sends the immediate notification and its own Live Activity.
2. Apple ActivityKit updates Batch Buddy's native Live Activity, which is the UI that can appear in CarPlay Dashboard.

## One-time setup

1. Build and install the unsigned IPA after signing it.
2. Open Batch Buddy and tap **Prepare live monitor**.
3. Copy the displayed ActivityKit push token.
4. On the desktop monitor, enter the token, Apple Team ID, Apple Key ID, and the path to the matching APNs `.p8` key.
5. Keep the monitor computer awake and online.

The desktop bridge defaults to Apple’s development APNs environment, which is normally the correct choice for a sideloaded development-signed IPA. Use the production endpoint only when the installed app and provisioning profile use the production push environment.

The Apple key is never sent to ActivitySmith. It is used locally by `apns_live_activity.py` to sign the provider request to Apple.

## What appears where

- ActivitySmith notification: immediate alert with batch details and actions.
- ActivitySmith Live Activity: persistent alert-style activity in the ActivitySmith app.
- Batch Buddy Live Activity: native Batch Buddy design on the iPhone Lock Screen, Dynamic Island, and eligible CarPlay Dashboard.

CarPlay controls are intentionally informational. Apple can disable interactive Live Activity controls in CarPlay, so Accept remains a phone action that only opens Shopper. No action accepts or rejects a batch automatically.
