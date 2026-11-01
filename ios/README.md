# Native iPhone experiment

This is the first native SwiftUI shell. The GitHub workflow creates an **unsigned** IPA using Xcode on a GitHub macOS runner. Download it and use Sideloadly on Windows to sign/install it with your Apple Account.

The app supports choosing a screenshot or photo through the system photo picker and reads visible offer text with Apple's on-device Vision framework. It fills detected pay, distance, and item values for review, then uses saved Canadian fuel and maintenance settings to estimate costs. It does not request unrestricted photo-library access and does not upload the selected image.

It does not yet include live screen sharing. The next native milestone is a user-initiated ScreenCaptureKit stream for iOS 18+, which must stay visible, consent-driven, and advisory-only.
