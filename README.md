# Batch Buddy

A native iPhone batch-offer advisor with a CarPlay Live Activity and an optional user-started live screen monitor. All offer decisions stay with the driver.

## iPhone features

- Enter an offer manually or scan a screenshot/photo locally with Vision OCR.
- Estimate pay per kilometre, hourly rate, fuel, maintenance, and net earnings.
- Configure Canadian fuel price, vehicle economy, and personal acceptance thresholds.
- Publish TAKE, CONSIDER, SKIP, REVIEW, or SCANNING to a Live Activity.
- Display the Live Activity in CarPlay Dashboard on supported iOS versions.
- Optionally start Apple's system screen broadcast and let the ReplayKit extension inspect visible Instacart offer text locally while Shopper is open.

## Live offer monitoring

1. Open Batch Buddy and tap **Prepare live monitor**.
2. Tap the iOS broadcast control, select Batch Buddy, and confirm **Start Broadcast**.
3. Switch to Instacart Shopper and keep one offer visible.
4. Batch Buddy samples frames about every 1.25 seconds and performs on-device OCR.
5. When it can read one clear pay amount and one distance, it updates the existing Live Activity with the recommendation.
6. If several offers are visible or the item count is unclear, it shows REVIEW or waits instead of guessing.
7. Stop the broadcast using the iOS recording indicator or Control Center.

The extension ignores audio. Captured frames are processed in memory, not stored or uploaded. Batch Buddy does not log in to Instacart, call private APIs, click, accept, reject, or otherwise interact with Shopper. The driver must verify the offer and make every decision.

## CarPlay

Batch Buddy uses ActivityKit and WidgetKit, not a custom CarPlay app category. On supported iOS versions, the system can display the Live Activity in CarPlay Dashboard. iOS and the vehicle control its placement. See [CarPlay setup and testing](docs/CARPLAY.md).

## Build and install

GitHub Actions builds an unsigned iOS IPA on a macOS runner:

1. Open the repository's [Actions page](https://github.com/MedicBoy/batch-buddy/actions).
2. Open the latest **Build unsigned iPhone IPA** run.
3. Download the **BatchBuddy-unsigned-ipa** artifact.
4. Sign the IPA with your own sideloading method (for example, Sideloadly) before installing it.

The project targets iOS 18 or later. CarPlay Live Activity display requires an iOS version and vehicle configuration that support Live Activities in CarPlay. The live screen monitor uses Apple's ReplayKit Broadcast Upload Extension for iOS 26 compatibility; test it on the actual iPhone before relying on it.

## Important limitations

- OCR depends on the exact Instacart screen layout, screen brightness, and readable text. It is intentionally conservative and will not guess when it sees multiple prices or distances.
- No private Instacart API or account integration is used.
- No batch is ever accepted or rejected automatically.
- A successful CI build proves compilation and packaging only; real-device screen-capture and in-car CarPlay testing are still required.

## Web proof of concept

The original local browser proof of concept remains available through npm start and npm test. The native iPhone project is under ios/.
