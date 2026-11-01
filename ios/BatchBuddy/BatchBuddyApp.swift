import SwiftUI
import PhotosUI
import Vision
import UIKit

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
    @State private var photoItem: PhotosPickerItem?
    @State private var scanStatus = "Choose a batch screenshot or photo to scan its visible text."
    @State private var extractedText = ""
    @AppStorage("vehicleName") private var vehicleName = "2019 Hyundai Elantra Sport"
    @AppStorage("gasPricePerLitre") private var gasPricePerLitre = 1.55
    @AppStorage("fuelLitresPer100Km") private var fuelLitresPer100Km = 8.8
    @AppStorage("maintenanceCostPerKm") private var maintenanceCostPerKm = 0.12

    var body: some View {
        NavigationStack {
            Form {
                Section("Scan a batch") {
                    PhotosPicker(selection: $photoItem, matching: .images) {
                        Label("Choose batch screenshot or photo", systemImage: "photo.on.rectangle")
                    }
                    Text(scanStatus).font(.footnote).foregroundStyle(.secondary)
                    if !extractedText.isEmpty {
                        DisclosureGroup("Text found in image") {
                            Text(extractedText).font(.caption).textSelection(.enabled)
                        }
                    }
                }
                Section("Offer details") {
                    TextField("Batch pay (CAD)", text: $pay).keyboardType(.decimalPad)
                    TextField("Total miles", text: $miles).keyboardType(.decimalPad)
                    TextField("Item count", text: $items).keyboardType(.numberPad)
                }
                Button("Analyze batch") {
                    advice = OfferAdvisor.analyze(
                        pay: Double(pay) ?? 0,
                        miles: Double(miles) ?? 0,
                        items: Int(items) ?? 0,
                        gasPricePerLitre: gasPricePerLitre,
                        fuelLitresPer100Km: fuelLitresPer100Km,
                        maintenanceCostPerKm: maintenanceCostPerKm
                    )
                }
                Section("Your car & costs") {
                    TextField("Vehicle", text: $vehicleName)
                    TextField("Gas price (CAD/L)", value: $gasPricePerLitre, format: .number.precision(.fractionLength(3))).keyboardType(.decimalPad)
                    TextField("Fuel use (L/100 km)", value: $fuelLitresPer100Km, format: .number.precision(.fractionLength(1))).keyboardType(.decimalPad)
                    TextField("Maintenance (CAD/km)", value: $maintenanceCostPerKm, format: .number.precision(.fractionLength(2))).keyboardType(.decimalPad)
                    Text("Adjust these values to match your driving. They are saved only on this device.").font(.footnote).foregroundStyle(.secondary)
                }
                if let advice {
                    Section(advice.recommendation) {
                        Text(advice.message)
                        LabeledContent("Pay per mile", value: advice.payPerMile, format: .currency(code: "CAD"))
                        LabeledContent("Estimated hourly rate", value: advice.hourlyRate, format: .currency(code: "CAD"))
                        LabeledContent("Fuel cost", value: advice.fuelCost, format: .currency(code: "CAD"))
                        LabeledContent("Maintenance cost", value: advice.maintenanceCost, format: .currency(code: "CAD"))
                        LabeledContent("Estimated net", value: advice.estimatedNet, format: .currency(code: "CAD"))
                    }
                }
                Section("Privacy") {
                    Text("Advice only. You choose every batch. This app does not sign in to Instacart, accept or reject batches, or upload screen content.")
                }
            }
            .navigationTitle("Batch Buddy")
            .onChange(of: photoItem) { _, item in
                guard let item else { return }
                Task { await scan(item) }
            }
        }
    }

    @MainActor
    private func scan(_ item: PhotosPickerItem) async {
        scanStatus = "Reading the selected image…"
        do {
            guard let imageData = try await item.loadTransferable(type: Data.self), let image = UIImage(data: imageData) else {
                throw ScanError.unreadableImage
            }
            let text = try await ImageTextScanner.scan(image)
            extractedText = text
            let offer = OfferTextParser.parse(text)
            if let value = offer.pay { pay = String(format: "%.2f", value) }
            if let value = offer.miles { miles = String(format: "%.1f", value) }
            if let value = offer.items { items = String(value) }
            scanStatus = "Scan complete. Check the filled values before analyzing the batch."
        } catch {
            scanStatus = "The image could not be read. Try a clearer, uncropped screenshot."
        }
    }
}

enum ScanError: Error { case unreadableImage }

enum ImageTextScanner {
    static func scan(_ image: UIImage) async throws -> String {
        guard let cgImage = image.cgImage else { throw ScanError.unreadableImage }
        return try await withCheckedThrowingContinuation { continuation in
            let request = VNRecognizeTextRequest { request, error in
                if let error { continuation.resume(throwing: error); return }
                let lines = (request.results as? [VNRecognizedTextObservation])?.compactMap { $0.topCandidates(1).first?.string } ?? []
                continuation.resume(returning: lines.joined(separator: "\n"))
            }
            request.recognitionLevel = .accurate
            request.usesLanguageCorrection = true
            DispatchQueue.global(qos: .userInitiated).async {
                do { try VNImageRequestHandler(cgImage: cgImage).perform([request]) }
                catch { continuation.resume(throwing: error) }
            }
        }
    }
}

struct ParsedOffer {
    var pay: Double?
    var miles: Double?
    var items: Int?
}

enum OfferTextParser {
    static func parse(_ text: String) -> ParsedOffer {
        let pay = first("\\$\\s*(\\d+(?:\\.\\d{1,2})?)", in: text).flatMap(Double.init)
        let miles = first("(\\d+(?:\\.\\d+)?)\\s*(?:mi|miles)\\b", in: text).flatMap(Double.init)
        let items = first("(\\d+)\\s*(?:items?|units?)\\b", in: text).flatMap(Int.init)
        return ParsedOffer(pay: pay, miles: miles, items: items)
    }

    private static func first(_ pattern: String, in text: String) -> String? {
        guard let expression = try? NSRegularExpression(pattern: pattern, options: [.caseInsensitive]), let match = expression.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)), let range = Range(match.range(at: 1), in: text) else { return nil }
        return String(text[range])
    }
}
