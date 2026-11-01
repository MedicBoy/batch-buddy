import ActivityKit
import Foundation

@MainActor
enum BatchBuddyActivityManager {
    static func publish(advice: OfferAdvice, pay: Double, kilometres: Double, items: Int) {
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

        Task {
            if let activity = Activity<BatchBuddyAttributes>.activities.first {
                await activity.update(content)
            } else {
                do {
                    _ = try Activity.request(
                        attributes: BatchBuddyAttributes(sessionName: "Current batch"),
                        content: content,
                        pushType: nil
                    )
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
}
