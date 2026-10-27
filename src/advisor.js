const defaults = { minimumHourlyRate: 20, minimumPayPerMile: 1.25, costPerMile: 0.25, estimatedMinutesPerItem: 1.5, fixedMinutes: 12 };

function number(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
}

function analyzeOffer(input) {
  const settings = { ...defaults, ...(input.settings || {}) };
  const pay = number(input.pay);
  const miles = number(input.miles);
  const items = number(input.items);
  const estimatedMinutes = Math.max(1, number(input.estimatedMinutes, items * settings.estimatedMinutesPerItem + settings.fixedMinutes));
  const payPerMile = miles === 0 ? pay : pay / miles;
  const estimatedHourlyRate = pay / estimatedMinutes * 60;
  const estimatedDrivingCost = miles * number(settings.costPerMile);
  const estimatedNet = pay - estimatedDrivingCost;
  const reasons = [];
  const concerns = [];

  if (payPerMile >= settings.minimumPayPerMile) reasons.push(`${formatCurrency(payPerMile)} per mile meets your target`);
  else concerns.push(`${formatCurrency(payPerMile)} per mile is below your ${formatCurrency(settings.minimumPayPerMile)} target`);
  if (estimatedHourlyRate >= settings.minimumHourlyRate) reasons.push(`${formatCurrency(estimatedHourlyRate)} per hour meets your target`);
  else concerns.push(`${formatCurrency(estimatedHourlyRate)} per hour is below your ${formatCurrency(settings.minimumHourlyRate)} target`);
  if (items >= 40) concerns.push(`${items} items may take longer than the estimate`);

  const score = Math.round(Math.max(0, Math.min(100, 50 + (payPerMile - settings.minimumPayPerMile) * 20 + (estimatedHourlyRate - settings.minimumHourlyRate) * 2 - Math.max(0, items - 35) * 0.8)));
  const recommendation = concerns.length === 0 ? "TAKE" : reasons.length === 0 ? "SKIP" : "CONSIDER";
  const spokenAdvice = recommendation === "TAKE" ? `Take looks reasonable: about ${formatCurrency(payPerMile)} per mile and ${formatCurrency(estimatedHourlyRate)} per hour.` : recommendation === "SKIP" ? `Skip: it is estimated at ${formatCurrency(payPerMile)} per mile and ${formatCurrency(estimatedHourlyRate)} per hour, below your targets.` : `Consider: ${reasons[0] || "some metrics are favorable"}, but ${concerns[0] || "check the details"}.`;

  return { recommendation, score, pay, miles, items, estimatedMinutes: Math.round(estimatedMinutes), payPerMile, estimatedHourlyRate, estimatedDrivingCost, estimatedNet, reasons, concerns, spokenAdvice };
}

function parseOfferText(text = "") {
  const amounts = [...text.matchAll(/\$\s*(\d+(?:\.\d{1,2})?)/g)].map((match) => Number(match[1]));
  const miles = text.match(/(\d+(?:\.\d+)?)\s*(?:mi|miles)\b/i);
  const items = text.match(/(\d+)\s*items?\b/i);
  return { pay: amounts[0] || 0, miles: miles ? Number(miles[1]) : 0, items: items ? Number(items[1]) : 0 };
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD", maximumFractionDigits: 2 }).format(value);
}

module.exports = { analyzeOffer, parseOfferText };
