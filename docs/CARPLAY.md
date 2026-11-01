# Batch Buddy CarPlay support

## What this build does

Batch Buddy uses ActivityKit and WidgetKit to publish the latest manually analyzed offer as a Live Activity. On iOS 26 and later, iOS can display Live Activities in CarPlay Dashboard without Batch Buddy being a full CarPlay-category app or requesting a separate CarPlay app entitlement.

The compact activity shows:
- TAKE, CONSIDER, or SKIP
- Offer pay in CAD
- Offer distance in kilometres and item count
- Estimated net after fuel and maintenance
- Estimated hourly rate

The activity is created or updated when the driver analyzes an offer in Batch Buddy. It is a glanceable read-only display in CarPlay; it does not accept, reject, or interact with an Instacart batch.

## Enable and test

1. Install the signed build on an iPhone running iOS 26 or later.
2. On iPhone, open Settings > Apps > Batch Buddy and allow Live Activities. Also check Settings > Face ID & Passcode > Live Activities if the device exposes that control.
3. Open Batch Buddy, enter or scan an offer, verify the extracted values, and tap Analyze batch.
4. Connect the iPhone to the vehicle's CarPlay system.
5. Open CarPlay Dashboard and look for the Batch Buddy Live Activity. If it isn't visible, check the CarPlay Dashboard layout and iPhone Live Activity settings.
6. Confirm the displayed recommendation and values match the iPhone result.

CarPlay presentations are controlled by iOS and the vehicle. A Live Activity may appear in Dashboard or as a notification; the app cannot force it to occupy a permanent panel.

## Not implemented

This release does not automatically detect offers inside Instacart. It still requires a user to enter or scan the offer and tap Analyze. Batch Buddy does not access Instacart credentials or private APIs, scrape the account, or automate acceptance/rejection. Automatic capture is a separate feasibility and privacy review, not a feature to claim as complete.

## Build status

The GitHub Actions workflow builds an unsigned IPA. An unsigned IPA must be signed with the user's own sideloading method before installation. A successful CI build does not replace real-device testing; the final CarPlay check must be performed in the user's car.
