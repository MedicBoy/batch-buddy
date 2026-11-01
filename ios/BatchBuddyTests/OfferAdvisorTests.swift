import Foundation

@main
enum OfferAdvisorTests {
    static func main() {
        testStrongOffer()
        testWeakOffer()
        testInvalidInputs()
        testZeroDistance()
        print("PASS: 4 Batch Buddy advisor tests")
    }

    static func testStrongOffer() {
        let a = OfferAdvisor.analyze(OfferInput(payCAD: 32, kilometres: 20, itemCount: 10, gasPricePerLitreCAD: 1.55, fuelLitresPer100Km: 9.4, maintenanceCostPerKmCAD: 0.12, minimumPayPerKilometreCAD: 0.78, minimumHourlyRateCAD: 20))
        expect(a.recommendation == "TAKE", "strong offer should be TAKE")
        expect(abs(a.payPerKilometre - 1.6) < 0.001, "pay per km")
        expect(a.estimatedNet > 0 && (0...100).contains(a.score), "net and score bounds")
    }

    static func testWeakOffer() {
        let a = OfferAdvisor.analyze(OfferInput(payCAD: 8, kilometres: 20, itemCount: 30, gasPricePerLitreCAD: 1.55, fuelLitresPer100Km: 9.4, maintenanceCostPerKmCAD: 0.12, minimumPayPerKilometreCAD: 0.78, minimumHourlyRateCAD: 20))
        expect(a.recommendation == "SKIP", "weak offer should be SKIP")
    }

    static func testInvalidInputs() {
        let a = OfferAdvisor.analyze(pay: 20, kilometres: 10, items: -5, gasPricePerLitre: .nan, fuelLitresPer100Km: -9, maintenanceCostPerKm: .infinity, minimumPayPerKilometre: 0.5, minimumHourlyRate: 10)
        expect(a.estimatedMinutes == 12, "negative items clamp to zero")
        expect(a.fuelCost == 0 && a.maintenanceCost == 0 && a.estimatedNet == 20, "invalid costs clamp safely")
    }

    static func testZeroDistance() {
        let a = OfferAdvisor.analyze(pay: 15, kilometres: 0, items: 5, gasPricePerLitre: 1.55, fuelLitresPer100Km: 9.4, maintenanceCostPerKm: 0.12, minimumPayPerKilometre: 0.78, minimumHourlyRate: 20)
        expect(a.payPerKilometre == 15 && a.fuelCost == 0 && a.maintenanceCost == 0, "zero-distance fallback")
    }

    static func expect(_ condition: Bool, _ message: String) {
        guard condition else { fputs("FAIL: \(message)\\n", stderr); exit(1) }
    }
}
