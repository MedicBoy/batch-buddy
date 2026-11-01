# Batch Buddy CarPlay and live offer monitoring

## CarPlay display

Batch Buddy uses ActivityKit and WidgetKit to publish the latest offer as a Live Activity. On iOS 26 and later, iOS can display Live Activities in CarPlay Dashboard without Batch Buddy being a full CarPlay-category app or requesting a separate CarPlay app entitlement.

The compact activity shows:
- TAKE, CONSIDER, SKIP, REVIEW, or SCANNING
- Offer pay in CAD
- Offer distance in kilometres and item count
- Estimated net after fuel and maintenance
- Estimated hourly rate

CarPlay controls the placement and size of Live Activities. Batch Buddy cannot force a permanent panel.

## Live offer monitor

On supported iOS versions, Batch Buddy includes a user-started ReplayKit Broadcast Upload Extension. It lets the driver start Apple's system screen broadcast, switch to Instacart Shopper, and have Batch Buddy read visible offer text locally.

1. Install the signed build on an iPhone running iOS 26.
2. Allow Live Activities for Batch Buddy in iPhone Settings.
3. Open Batch Buddy and tap **Prepare live monitor**.
4. Tap the system broadcast control, choose Batch Buddy, and confirm **Start Broadcast**.
5. Switch to Instacart Shopper. Keep a single offer visible for OCR to inspect.
6. Batch Buddy samples video frames about once every 1.25 seconds, performs on-device Vision OCR, and updates the existing Live Activity.
7. Stop the broadcast using the iOS recording indicator or Control Center when finished.

The extension ignores audio. It does not save or upload captured frames and does not sign in to Instacart, access private APIs, accept/reject batches, or tap anything in Shopper.

## Conservative detection rules

The OCR parser only proceeds when it sees one clear pay amount and one clear distance. If multiple offer amounts/distances are visible, it waits rather than guessing. If it cannot read a single item count, it displays **REVIEW** and does not invent a TAKE/SKIP recommendation. The driver must still verify the actual offer details and make every decision manually.

The exact Instacart screen layout and OCR accuracy must be tested on the user's iPhone. This is not a guarantee that every offer card or every UI revision will be recognized.

## Build and installation

GitHub Actions builds an unsigned IPA. The IPA must be signed with the user's own sideloading method before installation. The build includes the Live Activity widget extension and the ReplayKit broadcast extension. A successful CI build does not replace real-device testing; the final screen capture and CarPlay check must be performed on the user's iPhone and in the vehicle.
