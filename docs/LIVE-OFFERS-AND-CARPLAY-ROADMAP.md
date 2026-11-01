# Batch Buddy: live offers and in-car experience roadmap

## Goal

Build one Canadian batch-advisor engine that can serve the iPhone app and, only if Apple permits it, a CarPlay interface. Keep all account access and batch acceptance decisions under the driver's control.

## Current baseline

The native SwiftUI app already supports:
- Manual entry of offer pay, kilometres, and item count.
- User-selected screenshots/photos with on-device Vision text recognition.
- Canadian-dollar fuel and maintenance estimates and editable decision targets.
- TAKE / CONSIDER / SKIP advice.
- No Instacart login, private API, automated tapping, or automatic acceptance/rejection.

The current native app is not a CarPlay app and does not receive live Instacart offers.

## Workstreams

### 1. Shared offer and cost model

- Extract offer inputs, vehicle costs, thresholds, and recommendation output into a reusable model that is independent of SwiftUI views.
- Keep CAD and kilometres as the canonical units.
- Add explicit validation for missing/ambiguous OCR fields; never silently treat an unreadable field as zero.
- Add tests for fuel cost, maintenance reserve, net estimate, pay/km, hourly estimate, and recommendation boundaries.
- Preserve the existing Elantra defaults, while keeping vehicle settings editable.

**Acceptance:** the same test vectors produce the same result from the iPhone entry screen, screenshot scanner, and any future supported in-car surface.

### 2. User-initiated live offer assistance

- Investigate Apple's currently supported iOS screen-capture/broadcast APIs and App Store rules before implementation.
- Capture only after the user explicitly starts the system's screen-sharing/broadcast flow.
- Process frames locally at a conservative sampling rate; discard frames after parsing.
- Show extracted values for confirmation before calculating.
- Keep the app visibly active during capture and provide a clear stop control.
- Do not attempt to read Instacart's private app data, bypass iOS privacy controls, hide capture, or automate taps.
- Do not promise continuous background monitoring. iOS does not provide unrestricted access to another app's screen.

**Acceptance:** a user can deliberately start capture, see the capture state, confirm parsed values, stop capture, and use manual entry if capture is unavailable. No offer is accepted or rejected by Batch Buddy.

### 3. CarPlay feasibility gate

CarPlay is not a general-purpose mirror of an iPhone app. Apple limits CarPlay apps to approved categories and requires the relevant entitlement/approval. A batch-profit calculator is not obviously within an eligible category, so a native CarPlay dashboard must be treated as **unconfirmed**, not assumed buildable.

Before writing a CarPlay target:
- Check Apple's current CarPlay app categories, entitlement process, and review requirements.
- Confirm whether this app's actual purpose qualifies and whether Apple will grant the required entitlement.
- Do not add a fake CarPlay target or claim CarPlay support without the entitlement and a working head-unit test.

If Apple does not approve this use case, the fallback is an iPhone-first, glanceable parked-use dashboard plus permitted audio/notification cues. Do not encourage interaction while driving.

**Acceptance:** CarPlay is only marked supported after entitlement approval, successful build, and real vehicle/head-unit testing. Otherwise document the limitation and ship the fallback.

### 4. Build and release

- Keep the existing unsigned IPA workflow for test builds.
- Build and test on a supported macOS/Xcode runner.
- Run the JavaScript tests and add native model tests before publishing an IPA.
- Do not call a source commit an installable IPA; record the exact source SHA used for each build.
- Test installation and update behavior on the user's iPhone before calling a build release-ready.

## Immediate next engineering steps

1. Extract and test the shared offer calculation model.
2. Add a clear capture status/consent flow and investigate the currently supported capture API on a real iOS 18+ device.
3. Complete the CarPlay eligibility check before investing in a CarPlay-specific implementation.
4. Produce a test IPA from the resulting commit and identify it by commit SHA.

## Non-goals and safety boundaries

- No Instacart credentials or account scraping.
- No private/undocumented Instacart APIs.
- No automated acceptance, rejection, or checkout.
- No covert screen capture or background surveillance.
- No interaction prompts intended to be operated while the vehicle is moving.
