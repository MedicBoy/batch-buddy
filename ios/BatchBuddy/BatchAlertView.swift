import SwiftUI
import UIKit

struct BatchAlertView: View {
    @Binding var showPopup: Bool
    let pay: Double
    let kilometres: Double
    let items: Int
    let advice: OfferAdvice

    private var recommendationColor: Color {
        advice.recommendation == "TAKE" ? .green : (advice.recommendation == "SKIP" ? .red : .orange)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 5) {
                    Text("Instacart batch").font(.title3.weight(.bold))
                    Text("\(kilometres, specifier: "%.1f") km • \(items) items")
                        .font(.subheadline)
                        .foregroundStyle(.white.opacity(0.60))
                }
                Spacer()
                Button { showPopup = false } label: {
                    Image(systemName: "xmark")
                        .font(.subheadline.weight(.bold))
                        .foregroundStyle(.white.opacity(0.65))
                        .padding(9)
                        .background(.white.opacity(0.10), in: Circle())
                }
                .accessibilityLabel("Close batch alert")
            }

            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(pay, format: .currency(code: "CAD"))
                        .font(.system(size: 42, weight: .bold, design: .rounded))
                    Text("Estimated batch pay")
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.55))
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 5) {
                    Text("NET")
                        .font(.caption2.weight(.bold))
                        .foregroundStyle(.white.opacity(0.55))
                    Text(advice.estimatedNet, format: .currency(code: "CAD"))
                        .font(.headline.weight(.bold))
                        .foregroundStyle(.green)
                    Text("\(advice.hourlyRate, format: .currency(code: "CAD"))/hr")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(.cyan)
                }
            }
            .padding(16)
            .background(.black.opacity(0.20), in: RoundedRectangle(cornerRadius: 18, style: .continuous))

            Label("BatchBuddy recommends: \(advice.recommendation)", systemImage: advice.recommendation == "TAKE" ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(recommendationColor)
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
                .background(recommendationColor.opacity(0.14), in: Capsule())

            Text(advice.message)
                .font(.caption)
                .foregroundStyle(.white.opacity(0.70))

            HStack(spacing: 12) {
                Button("Ignore") { showPopup = false }
                    .font(.headline.weight(.semibold))
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 15)
                    .background(Color.white.opacity(0.12), in: RoundedRectangle(cornerRadius: 14, style: .continuous))

                Button("Accept") {
                    if let url = URL(string: "instacartshopper://") {
                        UIApplication.shared.open(url)
                    }
                    showPopup = false
                }
                .font(.headline.weight(.bold))
                .foregroundStyle(.black)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 15)
                .background(Color.green, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
            }
        }
        .padding(22)
        .frame(maxWidth: 360)
        .background(Color(red: 28.0 / 255.0, green: 28.0 / 255.0, blue: 30.0 / 255.0), in: RoundedRectangle(cornerRadius: 28, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 28, style: .continuous).stroke(.white.opacity(0.10), lineWidth: 1))
        .shadow(color: .black.opacity(0.45), radius: 30, y: 14)
        .padding(24)
        .accessibilityAddTraits(.isModal)
    }
}

#Preview {
    ZStack {
        Color.black.ignoresSafeArea()
        BatchAlertView(
            showPopup: .constant(true),
            pay: 22.25,
            kilometres: 20,
            items: 18,
            advice: OfferAdvice(
                recommendation: "TAKE",
                score: 92,
                payPerKilometre: 1.11,
                hourlyRate: 28.50,
                fuelCost: 3.46,
                maintenanceCost: 2.40,
                estimatedNet: 16.39,
                estimatedMinutes: 47,
                message: "Clears both targets."
            )
        )
    }
}
