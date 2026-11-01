import SwiftUI
import PhotosUI
import Vision
import UIKit

@main
struct BatchBuddyApp: App { var body: some Scene { WindowGroup { ContentView() } } }

struct ContentView: View {
    enum EntryField: Hashable { case pay, miles, items }
    @State private var pay = ""
    @State private var miles = ""
    @State private var items = ""
    @State private var advice: OfferAdvice?
    @State private var photoItem: PhotosPickerItem?
    @State private var scanStatus = "Choose an offer screenshot or photo. Scanning stays on this phone."
    @State private var extractedText = ""
    @FocusState private var focusedField: EntryField?
    @AppStorage("vehicleName") private var vehicleName = "2019 Hyundai Elantra Sport"
    @AppStorage("transmission") private var transmission = "DCT"
    @AppStorage("gasPricePerLitre") private var gasPricePerLitre = 1.55
    @AppStorage("fuelLitresPer100Km") private var fuelLitresPer100Km = 8.1
    @AppStorage("maintenanceCostPerKm") private var maintenanceCostPerKm = 0.12
    @AppStorage("minimumPayPerMile") private var minimumPayPerMile = 1.25
    @AppStorage("minimumHourlyRate") private var minimumHourlyRate = 20.0

    private var accent: Color { guard let advice else { return .cyan }; return advice.recommendation == "TAKE" ? .green : (advice.recommendation == "SKIP" ? .red : .orange) }

    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(colors: [Color(red: 0.02, green: 0.05, blue: 0.10), Color(red: 0.03, green: 0.13, blue: 0.16), Color(red: 0.02, green: 0.02, blue: 0.06)], startPoint: .topLeading, endPoint: .bottomTrailing).ignoresSafeArea()
                ScrollView {
                    VStack(spacing: 16) {
                        header
                        scanCard
                        offerCard
                        Button(action: analyze) { Label("Analyze batch", systemImage: "sparkles").font(.headline.weight(.bold)).frame(maxWidth: .infinity).padding(.vertical, 16) }
                            .buttonStyle(.borderedProminent).tint(.cyan).clipShape(RoundedRectangle(cornerRadius: 18))
                        if let advice { verdictCard(advice) }
                        settings
                        Label("Advice only — you stay in control. Batch Buddy does not sign in to Instacart, accept or reject batches, or send your photo anywhere.", systemImage: "lock.fill")
                            .font(.caption).foregroundStyle(.secondary).frame(maxWidth: .infinity, alignment: .leading).padding(.horizontal, 4).padding(.bottom, 10)
                    }.padding(.horizontal, 16).padding(.vertical, 12)
                }.scrollDismissesKeyboard(.interactively)
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .principal) { Text("Batch Buddy").font(.headline.weight(.bold)) }; ToolbarItemGroup(placement: .keyboard) { Spacer(); Button("Done") { focusedField = nil } } }
            .onChange(of: photoItem) { _, item in guard let item else { return }; Task { await scan(item) } }
            .onChange(of: transmission) { _, value in fuelLitresPer100Km = value == "Manual" ? 9.4 : 8.1 }
        }.preferredColorScheme(.dark)
    }

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 5) {
                Text("SMART BATCH DECISIONS").font(.caption.weight(.bold)).foregroundStyle(.cyan)
                Text("Know the numbers.\nChoose the batch.").font(.title2.weight(.bold))
                Text("Private advice built around your costs.").font(.subheadline).foregroundStyle(.secondary)
            }; Spacer()
            Image(systemName: "car.side.and.exclamationmark").font(.title2).foregroundStyle(.cyan).padding(12).background(.cyan.opacity(0.14), in: Circle())
        }.frame(maxWidth: .infinity, alignment: .leading).padding(.top, 4)
    }

    private var scanCard: some View {
        PremiumCard {
            HStack { Image(systemName: "viewfinder").font(.title3).foregroundStyle(.cyan); VStack(alignment: .leading, spacing: 2) { Text("Scan a batch").font(.headline); Text("Pick an offer image from Photos").font(.caption).foregroundStyle(.secondary) }; Spacer(); PhotosPicker(selection: $photoItem, matching: .images) { Text("Choose").font(.subheadline.weight(.semibold)) }.buttonStyle(.bordered).tint(.cyan) }
            Text(scanStatus).font(.caption).foregroundStyle(.secondary)
            if !extractedText.isEmpty { DisclosureGroup("Review scanned text") { Text(extractedText).font(.caption.monospaced()).foregroundStyle(.secondary).textSelection(.enabled).padding(.top, 6) }.font(.subheadline.weight(.semibold)) }
        }
    }

    private var offerCard: some View {
        PremiumCard {
            Text("Offer details").font(.headline)
            HStack(spacing: 10) {
                CompactField(title: "PAY", placeholder: "$0", text: $pay, keyboard: .decimalPad, field: .pay, focusedField: $focusedField)
                CompactField(title: "MILES", placeholder: "0.0", text: $miles, keyboard: .decimalPad, field: .miles, focusedField: $focusedField)
                CompactField(title: "ITEMS", placeholder: "0", text: $items, keyboard: .numberPad, field: .items, focusedField: $focusedField)
            }
            Text("Enter or confirm what was visible in the offer.").font(.caption).foregroundStyle(.secondary)
        }
    }

    private func verdictCard(_ advice: OfferAdvice) -> some View {
        PremiumCard(background: accent.opacity(0.16)) {
            HStack(alignment: .firstTextBaseline) { VStack(alignment: .leading, spacing: 2) { Text("RECOMMENDATION").font(.caption.weight(.bold)).foregroundStyle(accent); Text(advice.recommendation).font(.system(size: 42, weight: .black, design: .rounded)).foregroundStyle(accent) }; Spacer(); VStack(alignment: .trailing) { Text("FIT SCORE").font(.caption2.weight(.bold)).foregroundStyle(.secondary); Text("\(advice.score)").font(.title.weight(.bold)); Text("/ 100").font(.caption).foregroundStyle(.secondary) } }
            Text(advice.message).font(.subheadline).foregroundStyle(.white.opacity(0.88))
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 9) {
                MetricTile(title: "Net estimate", value: currency(advice.estimatedNet), tint: accent); MetricTile(title: "Pay / mile", value: currency(advice.payPerMile), tint: .cyan); MetricTile(title: "Hourly estimate", value: currency(advice.hourlyRate), tint: .purple); MetricTile(title: "Driving costs", value: currency(advice.fuelCost + advice.maintenanceCost), tint: .orange)
            }
            Text("Estimated \(advice.estimatedMinutes) min • Fuel \(currency(advice.fuelCost)) • Maintenance \(currency(advice.maintenanceCost))").font(.caption).foregroundStyle(.secondary)
        }
    }

    private var settings: some View {
        VStack(spacing: 10) {
            DisclosureGroup {
                VStack(spacing: 12) {
                    Picker("Transmission", selection: $transmission) { Text("7-speed DCT").tag("DCT"); Text("6-speed manual").tag("Manual") }.pickerStyle(.segmented)
                    HStack(spacing: 8) { SpecPill("1.6L turbo"); SpecPill("201 hp"); SpecPill("FWD") }
                    SettingRow(title: "Gas price", value: $gasPricePerLitre, suffix: "CAD/L"); SettingRow(title: "Fuel economy", value: $fuelLitresPer100Km, suffix: "L/100 km"); SettingRow(title: "Maintenance", value: $maintenanceCostPerKm, suffix: "CAD/km")
                    Text("Official combined rating: 8.1 L/100 km (DCT) or 9.4 L/100 km (manual). Edit for real-world driving.").font(.caption).foregroundStyle(.secondary)
                }.padding(.top, 12)
            } label: { HStack { Image(systemName: "car.fill").foregroundStyle(.cyan); VStack(alignment: .leading) { Text("My car & costs").font(.headline); Text(vehicleName).font(.caption).foregroundStyle(.secondary) }; Spacer() } }
            .tint(.white).padding(14).background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 18))
            DisclosureGroup {
                VStack(spacing: 12) { SettingRow(title: "Minimum pay / mile", value: $minimumPayPerMile, suffix: "CAD"); SettingRow(title: "Minimum hourly rate", value: $minimumHourlyRate, suffix: "CAD/hr") }.padding(.top, 12)
            } label: { HStack { Image(systemName: "slider.horizontal.3").foregroundStyle(.purple); VStack(alignment: .leading) { Text("Decision targets").font(.headline); Text("\(currency(minimumPayPerMile))/mile • \(currency(minimumHourlyRate))/hr").font(.caption).foregroundStyle(.secondary) }; Spacer() } }
            .tint(.white).padding(14).background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 18))
        }
    }

    private func analyze() { focusedField = nil; advice = OfferAdvisor.analyze(pay: Double(pay) ?? 0, miles: Double(miles) ?? 0, items: Int(items) ?? 0, gasPricePerLitre: gasPricePerLitre, fuelLitresPer100Km: fuelLitresPer100Km, maintenanceCostPerKm: maintenanceCostPerKm, minimumPayPerMile: minimumPayPerMile, minimumHourlyRate: minimumHourlyRate) }
    private func currency(_ value: Double) -> String { value.formatted(.currency(code: "CAD")) }
    private func scan(_ item: PhotosPickerItem) async {
        scanStatus = "Scanning on this phone…"
        guard let data = try? await item.loadTransferable(type: Data.self), let image = UIImage(data: data) else { scanStatus = "Couldn’t read that image. Try a clear screenshot."; return }
        let text = await recognizeText(in: image); extractedText = text; let offer = OfferTextParser.parse(text)
        if let value = offer.pay { pay = String(format: "%.2f", value) }; if let value = offer.miles { miles = String(format: "%.1f", value) }; if let value = offer.items { items = "\(value)" }
        scanStatus = text.isEmpty ? "No offer details found. You can enter them below." : "Scan complete. Confirm the fields, then analyze."
    }
    private func recognizeText(in image: UIImage) async -> String { await withCheckedContinuation { continuation in guard let cgImage = image.cgImage else { continuation.resume(returning: ""); return }; let request = VNRecognizeTextRequest { request, _ in let lines = (request.results as? [VNRecognizedTextObservation] ?? []).compactMap { $0.topCandidates(1).first?.string }; continuation.resume(returning: lines.joined(separator: "\n")) }; request.recognitionLevel = .accurate; request.usesLanguageCorrection = true; DispatchQueue.global(qos: .userInitiated).async { try? VNImageRequestHandler(cgImage: cgImage).perform([request]) } } }
}

private struct PremiumCard<Content: View>: View { let background: AnyShapeStyle; let content: Content; init(@ViewBuilder content: () -> Content) { background = AnyShapeStyle(Color.white.opacity(0.08)); self.content = content() }; init<S: ShapeStyle>(background: S, @ViewBuilder content: () -> Content) { self.background = AnyShapeStyle(background); self.content = content() }; var body: some View { VStack(alignment: .leading, spacing: 12) { content }.padding(16).frame(maxWidth: .infinity, alignment: .leading).background(background, in: RoundedRectangle(cornerRadius: 22, style: .continuous)).overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).stroke(.white.opacity(0.10), lineWidth: 1)) } }
private struct CompactField: View { let title: String; let placeholder: String; @Binding var text: String; let keyboard: UIKeyboardType; let field: ContentView.EntryField; var focusedField: FocusState<ContentView.EntryField?>.Binding; var body: some View { VStack(alignment: .leading, spacing: 5) { Text(title).font(.caption2.weight(.bold)).foregroundStyle(.secondary); TextField(placeholder, text: $text).font(.title3.weight(.semibold)).keyboardType(keyboard).focused(focusedField, equals: field) }.padding(10).frame(maxWidth: .infinity).background(.black.opacity(0.20), in: RoundedRectangle(cornerRadius: 13)) } }
private struct MetricTile: View { let title: String; let value: String; let tint: Color; var body: some View { VStack(alignment: .leading, spacing: 4) { Text(title.uppercased()).font(.caption2.weight(.bold)).foregroundStyle(.secondary); Text(value).font(.headline.weight(.bold)).foregroundStyle(tint) }.frame(maxWidth: .infinity, alignment: .leading).padding(10).background(.black.opacity(0.18), in: RoundedRectangle(cornerRadius: 13)) } }
private struct SpecPill: View { let text: String; init(_ text: String) { self.text = text }; var body: some View { Text(text).font(.caption.weight(.semibold)).padding(.horizontal, 9).padding(.vertical, 5).background(.cyan.opacity(0.14), in: Capsule()).foregroundStyle(.cyan) } }
private struct SettingRow: View { let title: String; @Binding var value: Double; let suffix: String; var body: some View { HStack { Text(title).font(.subheadline); Spacer(); TextField("0", value: $value, format: .number).keyboardType(.decimalPad).multilineTextAlignment(.trailing).frame(width: 76).font(.subheadline.weight(.semibold)); Text(suffix).font(.caption).foregroundStyle(.secondary).frame(width: 62, alignment: .leading) } } }
private struct OfferValues { var pay: Double?; var miles: Double?; var items: Int? }
private enum OfferTextParser { static func parse(_ text: String) -> OfferValues { let lower = text.lowercased(); return OfferValues(pay: first(#"\$\s*(\d+(?:\.\d{1,2})?)"#, in: lower), miles: first(#"(\d+(?:\.\d+)?)\s*(?:mi|miles)\b"#, in: lower), items: firstInt(#"(\d+)\s*(?:items?|units?)\b"#, in: lower)) }; private static func first(_ pattern: String, in text: String) -> Double? { guard let regex = try? NSRegularExpression(pattern: pattern), let match = regex.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)), let range = Range(match.range(at: 1), in: text) else { return nil }; return Double(text[range]) }; private static func firstInt(_ pattern: String, in text: String) -> Int? { guard let regex = try? NSRegularExpression(pattern: pattern), let match = regex.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)), let range = Range(match.range(at: 1), in: text) else { return nil }; return Int(text[range]) } }
