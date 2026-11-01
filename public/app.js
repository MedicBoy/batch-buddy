const ids = ["vehicleName", "pay", "miles", "items", "stores", "minutes", "minimumPayPerMile", "minimumHourlyRate", "gasPricePerLitre", "fuelLitresPer100Km", "maintenanceCostPerKm"];
const value = (id) => document.getElementById(id).value;
const currency = (amount) => new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD" }).format(amount);
const savedSettings = JSON.parse(localStorage.getItem("batchBuddySettings") || "{}");

ids.forEach((id) => {
  if (savedSettings[id] !== undefined) document.getElementById(id).value = savedSettings[id];
  document.getElementById(id).addEventListener("change", () => localStorage.setItem("batchBuddySettings", JSON.stringify(Object.fromEntries(ids.map((settingId) => [settingId, value(settingId)])))));
});

const imageInput = document.getElementById("batchImage");
const imagePreview = document.getElementById("imagePreview");
const scanButton = document.getElementById("scanButton");
imageInput.addEventListener("change", () => {
  const [image] = imageInput.files;
  scanButton.disabled = !image;
  if (!image) return;
  imagePreview.src = URL.createObjectURL(image);
  imagePreview.hidden = false;
  document.getElementById("scanStatus").textContent = "Ready to scan this selected image.";
});

scanButton.addEventListener("click", async () => {
  const [image] = imageInput.files;
  if (!image || !window.Tesseract) return;
  scanButton.disabled = true;
  const status = document.getElementById("scanStatus");
  status.textContent = "Reading the image…";
  try {
    const { data: { text } } = await Tesseract.recognize(image, "eng", { logger: (message) => { if (message.status === "recognizing text") status.textContent = `Scanning: ${Math.round(message.progress * 100)}%`; } });
    document.getElementById("scanText").textContent = text || "No readable text found.";
    document.getElementById("scanDetails").hidden = false;
    const response = await fetch("/api/parse", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text }) });
    const offer = await response.json();
    ["pay", "miles", "items", "stores"].forEach((key) => { if (offer[key]) document.getElementById(key).value = offer[key]; });
    status.textContent = "Scan complete. Check the filled values, then analyze the batch.";
  } catch (error) {
    status.textContent = "The image could not be scanned. Try a clearer, uncropped screenshot.";
  } finally { scanButton.disabled = false; }
});

document.getElementById("parseButton").addEventListener("click", async () => {
  const response = await fetch("/api/parse", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text: value("offerText") }) });
  const offer = await response.json();
  ["pay", "miles", "items", "stores"].forEach((key) => { if (offer[key]) document.getElementById(key).value = offer[key]; });
});

document.getElementById("analyzeButton").addEventListener("click", async () => {
  const response = await fetch("/api/analyze", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ pay: value("pay"), miles: value("miles"), items: value("items"), estimatedMinutes: value("minutes"), settings: { minimumPayPerMile: value("minimumPayPerMile"), minimumHourlyRate: value("minimumHourlyRate"), gasPricePerLitre: value("gasPricePerLitre"), fuelLitresPer100Km: value("fuelLitresPer100Km"), maintenanceCostPerKm: value("maintenanceCostPerKm") } }) });
  const result = await response.json();
  const resultElement = document.getElementById("result");
  resultElement.hidden = false;
  resultElement.innerHTML = `<p class="badge ${result.recommendation.toLowerCase()}">${result.recommendation} · ${result.score}/100</p><h2>${result.spokenAdvice}</h2><div class="metrics"><p><strong>${currency(result.payPerMile)}</strong>per mile</p><p><strong>${currency(result.estimatedHourlyRate)}</strong>per hour</p><p><strong>${currency(result.estimatedNet)}</strong>estimated net</p><p><strong>${result.estimatedMinutes} min</strong>estimated time</p></div><p><b>Cost estimate:</b> ${currency(result.estimatedFuelCost)} fuel + ${currency(result.estimatedMaintenanceCost)} maintenance for ${result.kilometres.toFixed(1)} km.</p>${result.reasons.length ? `<p><b>Pros:</b> ${result.reasons.join("; ")}</p>` : ""}${result.concerns.length ? `<p><b>Watch for:</b> ${result.concerns.join("; ")}</p>` : ""}<button id="speakButton" class="secondary">Speak advice</button>`;
  document.getElementById("speakButton").addEventListener("click", () => speechSynthesis.speak(new SpeechSynthesisUtterance(result.spokenAdvice)));
});

if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(() => {}));
