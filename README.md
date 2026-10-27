# Batch Buddy proof of concept

This is a local batch-offer advisor. It calculates estimated pay per mile, hourly rate, driving cost, and a human-readable **TAKE**, **CONSIDER**, or **SKIP** recommendation. The user retains every account and acceptance decision.

## Run locally

1. Install Node.js 20 or later.
2. From this folder, run `npm start`.
3. Open `http://127.0.0.1:4173` in a browser.

Run the checks with `npm test`.

## What works today

- Pasting a visible offer summary or entering offer values manually.
- Custom earnings, mileage, and vehicle-cost thresholds.
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
