import ActivityKit
import CoreMedia
import CoreVideo
import ReplayKit
import Vision

final class SampleHandler: RPBroadcastSampleHandler {
    private var lastProcessedAt = Date.distantPast
    private var lastOfferFingerprint: String?

    override func broadcastStarted(withSetupInfo setupInfo: [String : NSObject]?) {
        updateMonitorStatus(recommendation: "SCANNING", message: "Screen monitor is active. Waiting for one visible Instacart offer.")
    }

    override func processSampleBuffer(_ sampleBuffer: CMSampleBuffer, with sampleBufferType: RPSampleBufferType) {
        guard sampleBufferType == .video else { return }

        let now = Date()
        guard now.timeIntervalSince(lastProcessedAt) >= 1.25 else { return }
        lastProcessedAt = now

        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .fast
        request.usesLanguageCorrection = false
        request.minimumTextHeight = 0.012

        do {
            try VNImageRequestHandler(cvPixelBuffer: pixelBuffer).perform([request])
        } catch {
            return
        }

        let lines = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
        let recognizedText = lines.joined(separator: "\n")
        guard let offer = LiveOfferParser.parse(recognizedText) else { return }
        guard offer.fingerprint != lastOfferFingerprint else { return }
        lastOfferFingerprint = offer.fingerprint

        updateActivities(for: offer)
    }

    override func broadcastFinished() {
        Task { @MainActor in
            for activity in Activity<BatchBuddyAttributes>.activities {
                var state = activity.content.state
                state.recommendation = "PAUSED"
                state.message = "Screen monitoring stopped. Start the broadcast again to resume live offer detection."
                state.updatedAt = Date()
                await activity.update(ActivityContent(state: state, staleDate: Date().addingTimeInterval(5 * 60)))
            }
        }
    }

    private func updateMonitorStatus(recommendation: String, message: String) {
        Task { @MainActor in
            for activity in Activity<BatchBuddyAttributes>.activities {
                var state = activity.content.state
                state.recommendation = recommendation
                state.message = message
                state.updatedAt = Date()
                await activity.update(ActivityContent(state: state, staleDate: Date().addingTimeInterval(30 * 60)))
            }
        }
    }

    private func updateActivities(for offer: LiveOfferSnapshot) {
        Task { @MainActor in
            for activity in Activity<BatchBuddyAttributes>.activities {
                let profile = activity.attributes
                let items = offer.itemCount ?? 0
                let estimate = OfferAdvisor.analyze(
                    pay: offer.payCAD,
                    kilometres: offer.kilometres,
                    items: items,
                    gasPricePerLitre: profile.gasPricePerLitreCAD,
                    fuelLitresPer100Km: profile.fuelLitresPer100Km,
                    maintenanceCostPerKm: profile.maintenanceCostPerKmCAD,
                    minimumPayPerKilometre: profile.minimumPayPerKilometreCAD,
                    minimumHourlyRate: profile.minimumHourlyRateCAD
                )

                let state: BatchBuddyAttributes.ContentState
                if let itemCount = offer.itemCount, !offer.isAmbiguous {
                    state = BatchBuddyAttributes.ContentState(
                        recommendation: estimate.recommendation,
                        pay: offer.payCAD,
                        kilometres: offer.kilometres,
                        items: itemCount,
                        estimatedNet: estimate.estimatedNet,
                        hourlyRate: estimate.hourlyRate,
                        score: estimate.score,
                        message: "Detected from the visible offer. Check the order details before deciding. " + estimate.message,
                        updatedAt: Date()
                    )
                } else {
                    state = BatchBuddyAttributes.ContentState(
                        recommendation: "REVIEW",
                        pay: offer.payCAD,
                        kilometres: offer.kilometres,
                        items: 0,
                        estimatedNet: estimate.estimatedNet,
                        hourlyRate: 0,
                        score: 0,
                        message: "Pay and distance detected, but the item count wasn't clear. Review the offer manually before deciding.",
                        updatedAt: Date()
                    )
                }

                await activity.update(ActivityContent(state: state, staleDate: Date().addingTimeInterval(30 * 60)))
            }
        }
    }
}
