import Foundation

struct OfferAdvice {
    let recommendation: String
    let score: Int
    let payPerMile: Double
    let hourlyRate: Double
    let fuelCost: Double
    let maintenanceCost: Double
    let estimatedNet: Double
    let estimatedMinutes: Int
    let message: String
}

enum OfferAdvisor {
    static func analyze(pay: Double, miles: Double, items: Int, gasPricePerLitre: Double, fuelLitresPer100Km: Double, maintenanceCostPerKm: Double, minimumPayPerMile: Double, minimumHourlyRate: Double) -> OfferAdvice {
        let safePay = max(pay, 0), safeMiles = max(miles, 0)
        let payPerMile = safeMiles > 0 ? safePay / safeMiles : safePay
        let minutes = 12 + Double(max(items, 0)) * 1.5
        let hourlyRate = safePay / max(minutes, 1) * 60
        let kilometres = safeMiles * 1.60934
        let fuelCost = kilometres * max(fuelLitresPer100Km, 0) / 100 * max(gasPricePerLitre, 0)
        let maintenanceCost = kilometres * max(maintenanceCostPerKm, 0)
        let estimatedNet = safePay - fuelCost - maintenanceCost
        let clearsMileage = payPerMile >= minimumPayPerMile
        let clearsHourly = hourlyRate >= minimumHourlyRate
        let recommendation = clearsMileage && clearsHourly ? "TAKE" : (!clearsMileage && !clearsHourly ? "SKIP" : "CONSIDER")
        let score = min(100, max(0, Int((payPerMile / max(minimumPayPerMile, 0.01) * 45) + (hourlyRate / max(minimumHourlyRate, 0.01) * 55))))
        let message: String
        switch recommendation {
        case "TAKE": message = "Clears both of your targets. Review the route and order details before you decide."
        case "SKIP": message = "Misses both targets. Waiting for a stronger offer may protect your time and vehicle costs."
        default: message = "Clears one target but not the other. Check the store, route, and item mix before you decide."
        }
        return OfferAdvice(recommendation: recommendation, score: score, payPerMile: payPerMile, hourlyRate: hourlyRate, fuelCost: fuelCost, maintenanceCost: maintenanceCost, estimatedNet: estimatedNet, estimatedMinutes: Int(minutes.rounded()), message: message)
    }
}
