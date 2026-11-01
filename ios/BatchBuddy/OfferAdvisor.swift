import Foundation

struct OfferAdvice {
    let recommendation: String
    let payPerMile: Double
    let hourlyRate: Double
    let fuelCost: Double
    let maintenanceCost: Double
    let estimatedNet: Double
    let message: String
}

enum OfferAdvisor {
    static func analyze(pay: Double, miles: Double, items: Int, gasPricePerLitre: Double, fuelLitresPer100Km: Double, maintenanceCostPerKm: Double) -> OfferAdvice {
        let payPerMile = miles > 0 ? pay / miles : pay
        let minutes = 12 + Double(items) * 1.5
        let hourlyRate = pay / max(minutes, 1) * 60
        let kilometres = miles * 1.60934
        let fuelCost = kilometres * fuelLitresPer100Km / 100 * gasPricePerLitre
        let maintenanceCost = kilometres * maintenanceCostPerKm
        let estimatedNet = pay - fuelCost - maintenanceCost
        let recommendation = payPerMile >= 1.25 && hourlyRate >= 20 ? "TAKE" : payPerMile < 1.25 && hourlyRate < 20 ? "SKIP" : "CONSIDER"
        return OfferAdvice(recommendation: recommendation, payPerMile: payPerMile, hourlyRate: hourlyRate, fuelCost: fuelCost, maintenanceCost: maintenanceCost, estimatedNet: estimatedNet, message: "You make every acceptance decision.")
    }
}
