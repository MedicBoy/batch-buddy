import XCTest
final class OfferAdvisorTests: XCTestCase {
    func testStrongOfferClearsBothTargets() {
        let advice = OfferAdvisor.analyze(OfferInput(
            payCAD: 32,
            kilometres: 20,
            itemCount: 10,
            gasPricePerLitreCAD: 1.55,
            fuelLitresPer100Km: 9.4,
            maintenanceCostPerKmCAD: 0.12,
            minimumPayPerKilometreCAD: 0.78,
            minimumHourlyRateCAD: 20
        ))

        XCTAssertEqual(advice.recommendation, "TAKE")
        XCTAssertEqual(advice.payPerKilometre, 1.6, accuracy: 0.001)
        XCTAssertGreaterThan(advice.estimatedNet, 0)
        XCTAssertGreaterThanOrEqual(advice.score, 0)
        XCTAssertLessThanOrEqual(advice.score, 100)
    }

    func testWeakOfferMissesBothTargets() {
        let advice = OfferAdvisor.analyze(OfferInput(
            payCAD: 8,
            kilometres: 20,
            itemCount: 30,
            gasPricePerLitreCAD: 1.55,
            fuelLitresPer100Km: 9.4,
            maintenanceCostPerKmCAD: 0.12,
            minimumPayPerKilometreCAD: 0.78,
            minimumHourlyRateCAD: 20
        ))

        XCTAssertEqual(advice.recommendation, "SKIP")
    }

    func testInvalidNegativeAndNonFiniteCostsAreClamped() {
        let advice = OfferAdvisor.analyze(
            pay: 20,
            kilometres: 10,
            items: -5,
            gasPricePerLitre: .nan,
            fuelLitresPer100Km: -9,
            maintenanceCostPerKm: .infinity,
            minimumPayPerKilometre: 0.5,
            minimumHourlyRate: 10
        )

        XCTAssertEqual(advice.estimatedMinutes, 12)
        XCTAssertEqual(advice.fuelCost, 0, accuracy: 0.001)
        XCTAssertEqual(advice.maintenanceCost, 0, accuracy: 0.001)
        XCTAssertEqual(advice.estimatedNet, 20, accuracy: 0.001)
    }

    func testZeroDistanceUsesPayAsPayPerKilometreFallback() {
        let advice = OfferAdvisor.analyze(
            pay: 15,
            kilometres: 0,
            items: 5,
            gasPricePerLitre: 1.55,
            fuelLitresPer100Km: 9.4,
            maintenanceCostPerKm: 0.12,
            minimumPayPerKilometre: 0.78,
            minimumHourlyRate: 20
        )

        XCTAssertEqual(advice.payPerKilometre, 15, accuracy: 0.001)
        XCTAssertEqual(advice.fuelCost, 0, accuracy: 0.001)
        XCTAssertEqual(advice.maintenanceCost, 0, accuracy: 0.001)
    }
}
