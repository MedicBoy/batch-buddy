import SwiftUI
import UIKit

struct BatchAlertView: View {
    @Binding var showPopup: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 5) {
                    Text("Instacart batch").font(.title3.weight(.bold))
                    Text("20.0 km • 2 stores • 18 items").font(.subheadline).foregroundStyle(.white.opacity(0.60))
                }
                Spacer()
                Button { showPopup = false } label: {
                    Image(systemName: "xmark").font(.subheadline.weight(.bold)).foregroundStyle(.white.opacity(0.65)).padding(9).background(.white.opacity(0.10), in: Circle())
                }.accessibilityLabel("Close batch alert")
            }

            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("$22.25").font(.system(size: 42, weight: .bold, design: .rounded))
                    Text("Estimated batch pay").font(.caption).foregroundStyle(.white.opacity(0.55))
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 5) {
                    Text("NET").font(.caption2.weight(.bold)).foregroundStyle(.white.opacity(0.55))
                    Text("$16.25").font(.headline.weight(.bold)).foregroundStyle(.green)
                    Text("$24.38/hr").font(.subheadline.weight(.semibold)).foregroundStyle(.cyan)
                }
            }
            .padding(16).background(.black.opacity(0.20), in: RoundedRectangle(cornerRadius: 18, style: .continuous))

            Label("BatchBuddy recommends: Accept", systemImage: "checkmark.circle.fill")
                .font(.subheadline.weight(.semibold)).foregroundStyle(.green)
                .padding(.horizontal, 12).padding(.vertical, 10)
                .background(.green.opacity(0.14), in: Capsule())

            HStack(spacing: 12) {
                Button("Ignore") { showPopup = false }
                    .font(.headline.weight(.semibold)).foregroundStyle(.white)
                    .frame(maxWidth: .infinity).padding(.vertical, 15)
                    .background(Color.white.opacity(0.12), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                Button("Accept") {
                    UIApplication.shared.open(URL(string: "instacartshopper://")!)
                    showPopup = false
                }
                .font(.headline.weight(.bold)).foregroundStyle(.black)
                .frame(maxWidth: .infinity).padding(.vertical, 15)
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
    ZStack { Color.black.ignoresSafeArea(); BatchAlertView(showPopup: .constant(true)) }
}
