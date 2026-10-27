const ids = ["pay", "miles", "items", "minutes", "minimumPayPerMile", "minimumHourlyRate", "costPerMile"];
const value = (id) => document.getElementById(id).value;
const currency = (amount) => new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD" }).format(amount);

document.getElementById("parseButton").addEventListener("click", async () => {
  const response = await fetch("/api/parse", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text: value("offerText") }) });
  const offer = await response.json();
  ["pay", "miles", "items"].forEach((key) => { if (offer[key]) document.getElementById(key).value = offer[key]; });
});

document.getElementById("analyzeButton").addEventListener("click", async () => {
  const response = await fetch("/api/analyze", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ pay: value("pay"), miles: value("miles"), items: value("items"), estimatedMinutes: value("minutes"), settings: { minimumPayPerMile: value("minimumPayPerMile"), minimumHourlyRate: value("minimumHourlyRate"), costPerMile: value("costPerMile") } }) });
  const result = await response.json();
  const resultElement = document.getElementById("result");
  resultElement.hidden = false;
  resultElement.innerHTML = `<p class="badge ${result.recommendation.toLowerCase()}">${result.recommendation} · ${result.score}/100</p><h2>${result.spokenAdvice}</h2><div class="metrics"><p><strong>${currency(result.payPerMile)}</strong>per mile</p><p><strong>${currency(result.estimatedHourlyRate)}</strong>per hour</p><p><strong>${currency(result.estimatedNet)}</strong>estimated net</p><p><strong>${result.estimatedMinutes} min</strong>estimated time</p></div>${result.reasons.length ? `<p><b>Pros:</b> ${result.reasons.join("; ")}</p>` : ""}${result.concerns.length ? `<p><b>Watch for:</b> ${result.concerns.join("; ")}</p>` : ""}<button id="speakButton" class="secondary">Speak advice</button>`;
  document.getElementById("speakButton").addEventListener("click", () => speechSynthesis.speak(new SpeechSynthesisUtterance(result.spokenAdvice)));
});
