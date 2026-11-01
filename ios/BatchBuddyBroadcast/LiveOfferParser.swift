import Foundation

struct LiveOfferSnapshot: Sendable {
    let payCAD: Double
    let kilometres: Double
    let itemCount: Int?
    let isAmbiguous: Bool
    let reason: String
    var fingerprint: String {
        "\(payCAD.rounded(toPlaces: 2))|\(kilometres.rounded(toPlaces: 1))|\(itemCount.map { String($0) } ?? "?")"
    }
}

enum LiveOfferParser {
    static func parse(_ text: String) -> LiveOfferSnapshot? {
        let normalized = text.replacingOccurrences(of: ",", with: ".")
        let lower = normalized.lowercased()
        guard lower.contains("instacart") || lower.contains("shop") || lower.contains("batch") || lower.contains("items") else {
            return nil
        }

        let payValues = allMatches(#"\$\s*(\d+(?:\.\d{1,2})?)"#, in: normalized).compactMap(Double.init)
        let kilometreValues = allMatches(#"(\d+(?:\.\d+)?)\s*(?:km|kilomet(?:re|er)s?)\b"#, in: lower).compactMap(Double.init)
        let mileValues = allMatches(#"(\d+(?:\.\d+)?)\s*(?:mi|miles?)\b"#, in: lower).compactMap(Double.init)
        let itemValues = allMatches(#"(\d+)\s*(?:items?|units?)\b"#, in: lower).compactMap(Int.init)

        guard payValues.count == 1, kilometreValues.count + mileValues.count == 1 else {
            return nil
        }

        let distance = kilometreValues.first ?? (mileValues.first.map { $0 * 1.60934 } ?? 0)
        guard payValues[0] > 0, distance > 0 else { return nil }

        let isAmbiguous = itemValues.count > 1
        return LiveOfferSnapshot(
            payCAD: payValues[0],
            kilometres: distance,
            itemCount: itemValues.count == 1 ? itemValues[0] : nil,
            isAmbiguous: isAmbiguous,
            reason: isAmbiguous ? "More than one item count is visible. Open a single offer to review it." : ""
        )
    }

    private static func allMatches(_ pattern: String, in text: String) -> [String] {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return [] }
        let range = NSRange(text.startIndex..., in: text)
        return regex.matches(in: text, range: range).compactMap {
            guard let matchRange = Range($0.range(at: 1), in: text) else { return nil }
            return String(text[matchRange])
        }
    }
}

private extension Double {
    func rounded(toPlaces places: Int) -> String {
        String(format: "%.*f", places, self)
    }
}
