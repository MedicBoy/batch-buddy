import SwiftUI

@main
struct BatchBuddyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @State private var pay = "24.50"
    @State private var miles = "7.2"
    @State private var items = "18"
    @State private var advice: OfferAdvice?

    var body: some View {
        NavigationStack {
            Form {
                Section("Offer details") {
                    TextField("Batch pay (CAD)", text: $pay).keyboardType(.decimalPad)
                    TextField("Total miles", text: $miles).keyboardType(.decimalPad)
                    TextField("Item count", text: $items).keyboardType(.numberPad)
                }
                Button("Analyze batch") {
                    advice = OfferAdvisor.analyze(pay: Double(pay) ?? 0, miles: Double(miles) ?? 0, items: Int(items) ?? 0)
                }
                if let advice {
                    Section(advice.recommendation) {
                        Text(advice.message)
                        LabeledContent("Pay per mile", value: advice.payPerMile, format: .currency(code: "CAD"))
                        LabeledContent("Estimated hourly rate", value: advice.hourlyRate, format: .currency(code: "CAD"))
                    }
                }
                Section("Privacy") {
                    Text("Advice only. You choose every batch. This app does not sign in to Instacart, accept or reject batches, or upload screen content.")
                }
            }
            .navigationTitle("Batch Buddy")
        }
    }
}
