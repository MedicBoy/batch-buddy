# Batch Buddy

Batch Buddy is a Canadian batch-offer decision companion. The current application is a mobile-friendly installable web app with local screenshot OCR and an earnings/vehicle-cost advisor.

## Current working features

- Installable web app on iPhone through Safari's Add to Home Screen.
- User-selected batch screenshot with browser-based OCR.
- Extraction of pay, miles or kilometres, item count and store count from visible text.
- Editable Canadian vehicle, fuel, maintenance and decision thresholds.
- Estimated shopping and driving time when no manual time estimate is supplied.
- Estimated fuel, maintenance, net pay, pay per mile and hourly earnings.
- TAKE / CONSIDER / SKIP recommendation with spoken summary.
- Settings stored locally in the browser; no Instacart credentials or account access.

## Run and test

Requires Node.js 20+.

```sh
npm test
npm start
```

Open http://127.0.0.1:4173. To install on iPhone, host the app over HTTPS, open it in Safari, tap Share, then Add to Home Screen.

## Important platform boundary

This repository does **not** yet provide automatic access to Instacart Shopper offers, background monitoring of another app, or a CarPlay dashboard. iOS apps cannot silently inspect another app's private UI or automate its acceptance controls. Screen capture requires explicit user/system authorization and does not create unrestricted background access. CarPlay apps require Apple's approved app category and entitlements; an ordinary batch-shopping dashboard cannot assume approval.

The next engineering stage is a native iOS companion and an explicitly user-started capture workflow, subject to current Apple API availability and App Review restrictions. CarPlay support is conditional on Apple granting the necessary entitlement/category approval. No feature should be called automatic until it has been built, tested on a physical iPhone, and verified against the real Shopper offer screen.

## Privacy and safety

Batch Buddy does not request Instacart passwords, make network calls to Instacart, or accept/reject batches. OCR is initiated by the user for a selected image. Extracted values are suggestions and must be checked before relying on the recommendation.
