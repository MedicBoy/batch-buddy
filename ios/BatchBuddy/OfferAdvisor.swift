import Foundation

struct OfferAdvice {
    let recommendation: String
    let payPerMile: Double
    let hourlyRate: Double
    let message: String
}

enum OfferAdvisor {
    static func analyze(pay: Double, miles: Double, items: Int) -> OfferAdvice {
        let payPerMile = miles > 0 ? pay / miles : pay
        let minutes = 12 + Double(items) * 1.5
        let hourlyRate = pay / max(minutes, 1) * 60
        let recommendation = payPerMile >= 1.25 && hourlyRate >= 20 ? "TAKE" : payPerMile < 1.25 && hourlyRate < 20 ? "SKIP" : "CONSIDER"
        return OfferAdvice(recommendation: recommendation, payPerMile: payPerMile, hourlyRate: hourlyRate, message: "You make every acceptance decision.")
    }
}
