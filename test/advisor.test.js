const test = require("node:test");
const assert = require("node:assert/strict");
const { analyzeOffer, parseOfferText } = require("../src/advisor");

test("recommends take for an offer meeting both targets", () => {
  const result = analyzeOffer({ pay: 30, miles: 10, items: 10 });
  assert.equal(result.recommendation, "TAKE");
  assert.equal(result.payPerMile, 3);
});

test("recommends skip for an offer missing both targets", () => {
  const result = analyzeOffer({ pay: 8, miles: 12, items: 20 });
  assert.equal(result.recommendation, "SKIP");
});

test("parses a pasted offer summary", () => {
  assert.deepEqual(parseOfferText("$24.50 batch, 7.2 miles, 18 items"), { pay: 24.5, miles: 7.2, items: 18 });
});
