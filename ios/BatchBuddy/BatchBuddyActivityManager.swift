import ActivityKit
import Foundation

@MainActor
enum BatchBuddyActivityManager {
    static let pushTokenKey = "batchBuddy.liveActivityPushToken"

    enum StartError: LocalizedError {
        case disabled

        var errorDescription: String? {
            switch self {
            case .disabled:
                return "Live Activities are disabled for Batch Buddy. Enable them in iPhone Settings and try again."
            }
        }
    }

    static func startMonitoring(
        gasPricePerLitre: Double,
        fuelLitresPer100Km: Double,
        maintenanceCostPerKm: Double,
        minimumPayPerKilometre: Double,
        minimumHourlyRate: Double
    ) async throws -> Bool {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else {
            throw StartError.disabled
        }

        for activity in Activity<BatchBuddyAttributes>.activities {
            await activity.end(nil, dismissalPolicy: .immediate)
        }

        let attributes = makeAttributes(
            gasPricePerLitre: gasPricePerLitre,
            fuelLitresPer100Km: fuelLitresPer100Km,
            maintenanceCostPerKm: maintenanceCostPerKm,
            minimumPayPerKilometre: minimumPayPerKilometre,
            minimumHourlyRate: minimumHourlyRate
        )
        let initialState = BatchBuddyAttributes.ContentState(
            recommendation: "SCANNING",
            pay: 0,
            kilometres: 0,
            items: 0,
            estimatedNet: 0,
            hourlyRate: 0,
            score: 0,
            message: "Waiting for a visible Instacart offer. Start the screen broadcast, then open Shopper.",
            updatedAt: Date()
        )

        let content = ActivityContent(state: initialState, staleDate: Date().addingTimeInterval(30 * 60))
        do {
            let activity = try Activity.request(attributes: attributes, content: content, pushType: .token)
            observePushToken(for: activity)
            return true
        } catch {
            // Unsigned/sideloaded builds may not carry aps-environment. Keep the
            // local Live Activity usable even when remote push tokens are unavailable.
            let activity = try Activity.request(attributes: attributes, content: content, pushType: nil)
            _ = activity
            return false
        }
    }

    static func publish(
        advice: OfferAdvice,
        pay: Double,
        kilometres: Double,
        items: Int,
        gasPricePerLitre: Double,
        fuelLitresPer100Km: Double,
        maintenanceCostPerKm: Double,
        minimumPayPerKilometre: Double,
        minimumHourlyRate: Double
    ) {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        let state = BatchBuddyAttributes.ContentState(
            recommendation: advice.recommendation,
            pay: pay,
            kilometres: kilometres,
            items: items,
            estimatedNet: advice.estimatedNet,
            hourlyRate: advice.hourlyRate,
            score: advice.score,
            message: advice.message,
            updatedAt: Date()
        )
        let content = ActivityContent(state: state, staleDate: Date().addingTimeInterval(30 * 60))
        let attributes = makeAttributes(
            gasPricePerLitre: gasPricePerLitre,
            fuelLitresPer100Km: fuelLitresPer100Km,
            maintenanceCostPerKm: maintenanceCostPerKm,
            minimumPayPerKilometre: minimumPayPerKilometre,
            minimumHourlyRate: minimumHourlyRate
        )

        Task {
            if let activity = Activity<BatchBuddyAttributes>.activities.first {
                await activity.update(content)
            } else {
                do {
                    let activity = try Activity.request(attributes: attributes, content: content, pushType: .token)
                    observePushToken(for: activity)
                } catch {
                    // Live Activities are optional; the in-app advisor remains available.
                }
            }
        }
    }

    static func endCurrentActivity() {
        Task {
            for activity in Activity<BatchBuddyAttributes>.activities {
                await activity.end(nil, dismissalPolicy: .immediate)
            }
        }
    }

    private static func makeAttributes(
        gasPricePerLitre: Double,
        fuelLitresPer100Km: Double,
        maintenanceCostPerKm: Double,
        minimumPayPerKilometre: Double,
        minimumHourlyRate: Double
    ) -> BatchBuddyAttributes {
        BatchBuddyAttributes(
            sessionName: "Current batch",
            gasPricePerLitreCAD: gasPricePerLitre,
            fuelLitresPer100Km: fuelLitresPer100Km,
            maintenanceCostPerKmCAD: maintenanceCostPerKm,
            minimumPayPerKilometreCAD: minimumPayPerKilometre,
            minimumHourlyRateCAD: minimumHourlyRate
        )
    }

    private static func observePushToken(for activity: Activity<BatchBuddyAttributes>) {
        Task {
            for await tokenData in activity.pushTokenUpdates {
                let token = tokenData.map { String(format: "%02x", $0) }.joined()
                UserDefaults.standard.set(token, forKey: pushTokenKey)
                NotificationCenter.default.post(
                    name: .batchBuddyPushTokenUpdated,
                    object: token
                )
            }
        }
    }
}

extension Notification.Name {
    static let batchBuddyPushTokenUpdated = Notification.Name("batchBuddyPushTokenUpdated")
}
