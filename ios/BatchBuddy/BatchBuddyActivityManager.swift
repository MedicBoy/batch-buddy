import ActivityKit
import Foundation

@MainActor
enum BatchBuddyActivityManager {
    static func startMonitoring(
        gasPricePerLitre: Double,
        fuelLitresPer100Km: Double,
        maintenanceCostPerKm: Double,
        minimumPayPerKilometre: Double,
        minimumHourlyRate: Double
    ) {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        Task {
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

            do {
                _ = try Activity.request(
                    attributes: attributes,
                    content: ActivityContent(state: initialState, staleDate: Date().addingTimeInterval(30 * 60)),
                    pushType: nil
                )
            } catch {
                // The app remains usable if Live Activities are disabled or unavailable.
            }
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
                    _ = try Activity.request(attributes: attributes, content: content, pushType: nil)
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
}
