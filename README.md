# Batch Buddy proof of concept

This is a local batch-offer advisor. It calculates estimated pay per mile, hourly rate, driving cost, and a human-readable **TAKE**, **CONSIDER**, or **SKIP** recommendation. The user retains every account and acceptance decision.

## Run locally

1. Install Node.js 20 or later.
2. From this folder, run `npm start`.
3. Open `http://127.0.0.1:4173` in a browser.

Run the checks with `npm test`.

## What works today

- Pasting a visible offer summary or entering offer values manually.
- Choosing a batch screenshot or photo, then scanning its visible text locally in the browser before reviewing the extracted values.
- Custom earnings, mileage, and vehicle-cost thresholds.
- Canadian fuel and maintenance-cost estimates, with editable vehicle and gas-price settings stored on the device.
- A local calculation and optional spoken advice.
- No Instacart login, API calls, account interaction, clicking, accepting, rejecting, or screen upload.

## iPhone feasibility and recommended path

The practical target for the capture proof of concept is **iOS 18 or later**. Apple’s current ScreenCaptureKit guidance supports presenting the system’s content-sharing picker, where the user explicitly chooses either the full display or in-app content. A full-display selection can include the Shopper app while the share is active. Use it only after the user starts the share, process a low frame rate locally, discard frames after extracting offer fields, and keep all accept/reject actions manual. Apple’s older ReplayKit sample-buffer broadcast extension is now marked deprecated, so this project should use ScreenCaptureKit for the modern implementation.

This is feasible for a private experiment but not yet a completed iPhone app: the PC does not have Xcode or an iPhone connection. Apple’s Xcode support matrix lists macOS as its host platform, so a Mac (local, borrowed, or hosted build service that supports the required native capability) is needed to compile and package the Swift iOS app. A Windows PC can still use Sideloadly to install a finished IPA.

Free Apple signing is suitable for a prototype only: Apple says a Personal Team permits 3 apps per device and profiles expire after 7 days; Sideloadly documents the same 7-day lifetime and offers refresh support. Keep one stable bundle identifier so updates preserve local app data.

## Next build milestone

On a Mac with Xcode and an iOS 18+ test iPhone, create the native SwiftUI host app and its ScreenCaptureKit stream. The stream should send only sampled, user-authorized frames to an offer parser. The parser should return structured fields to the already-built advisor endpoint, then show and speak a recommendation. Add an AI vision endpoint only after choosing an API provider and securely storing its key on a backend; never embed a secret in the iOS app.

## Sources

- [Apple: Capturing screen content on iOS](https://developer.apple.com/documentation/screencapturekit/capturing-screen-content-on-ios)
- [Apple: ScreenCaptureKit](https://developer.apple.com/documentation/screencapturekit)
- [Apple: Personal Team limits](https://developer.apple.com/help/account/basics/about-your-developer-account)
- [Apple: Xcode system requirements](https://developer.apple.com/xcode/system-requirements)
- [Sideloadly FAQ](https://sideloadly.io/faq)


## Planned live-offer and in-car work

See [the live-offer and CarPlay roadmap](docs/LIVE-OFFERS-AND-CARPLAY-ROADMAP.md). CarPlay support is a feasibility question until Apple confirms the required category/entitlement; live screen assistance must be user-initiated and advisory-only.

## Native calculation model

The iPhone advisor now has a normalized `OfferInput` model with CAD and kilometres as its canonical units. The calculation entry point is independent of SwiftUI so the same logic can be called by manual entry, reviewed OCR results, and future interfaces if platform rules permit. Native XCTest coverage has been added for strong/weak offers, invalid numeric inputs, and zero-distance handling.

These changes are on the `feature/carplay-and-live-offer-roadmap` branch and have not yet been built or tested on an Xcode runner. They do not add CarPlay entitlement or live screen capture.


## CarPlay verdict display (iOS 26)

The native iPhone app now includes a WidgetKit Live Activity target. When you manually analyze an offer in the iPhone app, Batch Buddy publishes the resulting TAKE / CONSIDER / SKIP verdict to a Live Activity. On iOS 26, supported Live Activities can appear in CarPlay Dashboard. Enable Live Activities for Batch Buddy in iPhone Settings and allow the activity to start from the app.

This is the first display integration only: it does **not** detect Instacart offers automatically. A new offer still has to reach the advisor through a supported, user-authorized input path. CarPlay Live Activities are glance-only; they do not accept or decline batches.
