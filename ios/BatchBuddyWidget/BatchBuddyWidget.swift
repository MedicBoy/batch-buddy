import ActivityKit
import SwiftUI
import WidgetKit

@main
struct BatchBuddyWidgetBundle: WidgetBundle {
    var body: some Widget {
        BatchBuddyLiveActivityWidget()
    }
}

struct BatchBuddyLiveActivityWidget: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: BatchBuddyAttributes.self) { context in
            BatchBuddyActivityView(state: context.state)
                .activityBackgroundTint(Color(red: 0.025, green: 0.055, blue: 0.10))
                .activitySystemActionForegroundColor(.white)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    Text(context.state.recommendation)
                        .font(.headline.bold())
                        .foregroundStyle(verdictColor(context.state.recommendation))
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Text(context.state.pay, format: .currency(code: "CAD"))
                        .font(.headline.bold())
                }
                DynamicIslandExpandedRegion(.bottom) {
                    HStack {
                        Label(String(format: "%.1f km", context.state.kilometres), systemImage: "car")
                        Spacer()
                        Text("Net \(context.state.estimatedNet, format: .currency(code: "CAD"))")
                    }
                    .font(.caption)
                }
            } compactLeading: {
                Text(String(context.state.recommendation.prefix(1)))
                    .foregroundStyle(verdictColor(context.state.recommendation))
            } compactTrailing: {
                Text(context.state.pay, format: .currency(code: "CAD"))
                    .font(.caption2.bold())
            } minimal: {
                Text(String(context.state.recommendation.prefix(1)))
                    .foregroundStyle(verdictColor(context.state.recommendation))
            }
        }
        .supplementalActivityFamilies([.small])
    }
}

private struct BatchBuddyActivityView: View {
    let state: BatchBuddyAttributes.ContentState

    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack {
                Text("BATCH BUDDY")
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(.cyan)
                Spacer()
                Text(state.recommendation)
                    .font(.headline.weight(.black))
                    .foregroundStyle(verdictColor(state.recommendation))
            }
            HStack(alignment: .firstTextBaseline) {
                Text(state.pay, format: .currency(code: "CAD"))
                    .font(.system(size: 27, weight: .bold, design: .rounded))
                Spacer()
                Text("\(state.kilometres, specifier: "%.1f") km • \(state.items) items")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            HStack {
                Text("Net est. \(state.estimatedNet, format: .currency(code: "CAD"))")
                Spacer()
                Text("\(state.hourlyRate, format: .currency(code: "CAD"))/hr")
            }
            .font(.caption2.weight(.semibold))
            .foregroundStyle(.white.opacity(0.85))
        }
        .foregroundStyle(.white)
        .padding(12)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Batch Buddy verdict: \(state.recommendation), pay \(state.pay, format: .currency(code: "CAD")), \(state.kilometres, specifier: "%.1f") kilometres, estimated net \(state.estimatedNet, format: .currency(code: "CAD"))")
    }
}

private func verdictColor(_ recommendation: String) -> Color {
    switch recommendation {
    case "TAKE": return .green
    case "SKIP": return .red
    default: return .orange
    }
}
