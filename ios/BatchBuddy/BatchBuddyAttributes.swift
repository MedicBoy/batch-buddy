import ActivityKit
import Foundation

struct BatchBuddyAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var recommendation: String
        var pay: Double
        var kilometres: Double
        var items: Int
        var estimatedNet: Double
        var hourlyRate: Double
        var score: Int
        var message: String
        var updatedAt: Date
    }

    var sessionName: String
}
