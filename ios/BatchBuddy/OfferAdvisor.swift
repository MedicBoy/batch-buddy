import Foundation

/// A normalized offer input shared by manual entry, OCR review, and future approved interfaces.
/// All distance values are kilometres and all money values are Canadian dollars.
struct OfferInput {
    let payCAD: Double
    let kilometres: Double
    let itemCount: Int
    let gasPricePerLitreCAD: Double
    let fuelLitresPer100Km: Double
    let maintenanceCostPerKmCAD: Double
    let minimumPayPerKilometreCAD: Double
    let minimumHourlyRateCAD: Double
}

struct OfferAdvice {
    let recommendation: String
    let score: Int
    let payPerKilometre: Double
    let hourlyRate: Double
    let fuelCost: Double
    let maintenanceCost: Double
    let estimatedNet: Double
    let estimatedMinutes: Int
    let message: String
}

enum OfferAdvisor {
    /// Pure calculation entry point. It has no dependency on SwiftUI, storage, or screen capture.
    static func analyze(_ input: OfferInput) -> OfferAdvice {
        analyze(
            pay: input.payCAD,
            kilometres: input.kilometres,
            items: input.itemCount,
            gasPricePerLitre: input.gasPricePerLitreCAD,
            fuelLitresPer100Km: input.fuelLitresPer100Km,
            maintenanceCostPerKm: input.maintenanceCostPerKmCAD,
            minimumPayPerKilometre: input.minimumPayPerKilometreCAD,
            minimumHourlyRate: input.minimumHourlyRateCAD
        )
    }

    /// Compatibility entry point used by the existing iPhone screen.
    static func analyze(pay: Double, kilometres: Double, items: Int, gasPricePerLitre: Double, fuelLitresPer100Km: Double, maintenanceCostPerKm: Double, minimumPayPerKilometre: Double, minimumHourlyRate: Double) -> OfferAdvice {
        let safePay = finiteNonnegative(pay)
        let safeKilometres = finiteNonnegative(kilometres)
        let safeItems = max(items, 0)
        let payPerKilometre = safeKilometres > 0 ? safePay / safeKilometres : safePay
        let minutes = 12.0 + Double(safeItems) * 1.5
        let hourlyRate = safePay / max(minutes, 1) * 60
        let fuelCost = safeKilometres * finiteNonnegative(fuelLitresPer100Km) / 100 * finiteNonnegative(gasPricePerLitre)
        let maintenanceCost = safeKilometres * finiteNonnegative(maintenanceCostPerKm)
        let estimatedNet = safePay - fuelCost - maintenanceCost
        let mileageTarget = finiteNonnegative(minimumPayPerKilometre)
        let hourlyTarget = finiteNonnegative(minimumHourlyRate)
        let clearsMileage = payPerKilometre >= mileageTarget
        let clearsHourly = hourlyRate >= hourlyTarget
        let recommendation = clearsMileage && clearsHourly ? "TAKE" : (!clearsMileage && !clearsHourly ? "SKIP" : "CONSIDER")
        let score = min(100, max(0, Int((payPerKilometre / max(mileageTarget, 0.01) * 45) + (hourlyRate / max(hourlyTarget, 0.01) * 55))))
        let message: String
        switch recommendation {
        case "TAKE": message = "Clears both of your targets. Review the route and order details before you decide."
        case "SKIP": message = "Misses both targets. Waiting for a stronger offer may protect your time and vehicle costs."
        default: message = "Clears one target but not the other. Check the store, route, and item mix before you decide."
        }
        return OfferAdvice(recommendation: recommendation, score: score, payPerKilometre: payPerKilometre, hourlyRate: hourlyRate, fuelCost: fuelCost, maintenanceCost: maintenanceCost, estimatedNet: estimatedNet, estimatedMinutes: Int(minutes.rounded()), message: message)
    }

    private static func finiteNonnegative(_ value: Double) -> Double {
        value.isFinite ? max(value, 0) : 0
    }
}
