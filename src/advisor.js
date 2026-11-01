const defaults = { minimumHourlyRate:20, minimumPayPerMile:1.25, gasPricePerLitre:1.55, fuelLitresPer100Km:8.8, maintenanceCostPerKm:0.12, estimatedMinutesPerItem:1.5, averageDrivingSpeedKmh:35, fixedMinutes:12, minutesPerExtraStore:8 };
function number(value, fallback=0) { if(value===""||value===null||value===undefined)return fallback; const n=Number(value); return Number.isFinite(n)&&n>=0?n:fallback; }
function analyzeOffer(input={}) {
 const settings=Object.fromEntries(Object.entries(defaults).map(([k,v])=>[k,number(input.settings?.[k],v)]));
 const pay=number(input.pay), miles=number(input.miles), items=number(input.items), stores=Math.max(1,number(input.stores,1));
 const kilometres=miles*1.60934, driveMinutes=settings.averageDrivingSpeedKmh>0?kilometres/settings.averageDrivingSpeedKmh*60:0;
 const calculated=settings.fixedMinutes+items*settings.estimatedMinutesPerItem+driveMinutes+Math.max(0,stores-1)*settings.minutesPerExtraStore;
 const supplied=number(input.estimatedMinutes), estimatedMinutes=Math.max(1,supplied>0?supplied:calculated);
 const payPerMile=miles>0?pay/miles:0, estimatedHourlyRate=pay/estimatedMinutes*60;
 const fuelLitres=kilometres*settings.fuelLitresPer100Km/100, estimatedFuelCost=fuelLitres*settings.gasPricePerLitre;
 const estimatedMaintenanceCost=kilometres*settings.maintenanceCostPerKm, estimatedDrivingCost=estimatedFuelCost+estimatedMaintenanceCost, estimatedNet=pay-estimatedDrivingCost;
 const reasons=[], concerns=[];
 if(miles===0) concerns.push("Mileage is missing, so pay per mile cannot be assessed");
 else if(payPerMile>=settings.minimumPayPerMile) reasons.push(`${formatCurrency(payPerMile)} per mile meets your target`);
 else concerns.push(`${formatCurrency(payPerMile)} per mile is below your ${formatCurrency(settings.minimumPayPerMile)} target`);
 if(estimatedHourlyRate>=settings.minimumHourlyRate) reasons.push(`${formatCurrency(estimatedHourlyRate)} per hour meets your target`);
 else concerns.push(`${formatCurrency(estimatedHourlyRate)} per hour is below your ${formatCurrency(settings.minimumHourlyRate)} target`);
 if(items>=40) concerns.push(`${items} items may take longer than estimated`);
 if(stores>1) concerns.push(`This batch has ${stores} stores; allow extra time for multiple shops`);
 if(estimatedNet<=0) concerns.push("Estimated vehicle costs use up the batch pay");
 const score=Math.round(Math.max(0,Math.min(100,(miles>0?50:25)+(payPerMile-settings.minimumPayPerMile)*20+(estimatedHourlyRate-settings.minimumHourlyRate)*2-Math.max(0,items-35)*.8-Math.max(0,stores-1)*5)));
 const recommendation=concerns.length===0?"TAKE":reasons.length===0?"SKIP":"CONSIDER";
 const spokenAdvice=`${recommendation}. ${formatCurrency(payPerMile)} per mile, approximately ${formatCurrency(estimatedHourlyRate)} per hour, and ${formatCurrency(estimatedNet)} after estimated fuel and maintenance.`;
 return {recommendation,score,pay,miles,kilometres,items,stores,estimatedMinutes:Math.round(estimatedMinutes),driveMinutes:Math.round(driveMinutes),payPerMile,estimatedHourlyRate,estimatedFuelCost,estimatedMaintenanceCost,estimatedDrivingCost,estimatedNet,reasons,concerns,spokenAdvice};
}
function parseOfferText(text="") {
 const s=String(text).replace(/\u00a0/g," "), money=s.match(/(?:CA\$|CAD\s*|\$)\s*(\d+(?:\.\d{1,2})?)/i), miles=s.match(/(\d+(?:\.\d+)?)\s*(?:mi|miles)\b/i), km=s.match(/(\d+(?:\.\d+)?)\s*(?:km|kilomet(?:er|re)s?)\b/i), items=s.match(/(\d+)\s*(?:items?|units?)\b/i), stores=s.match(/(\d+)\s*(?:stores?|shops?)\b/i);
 return {pay:money?Number(money[1]):0,miles:miles?Number(miles[1]):km?Number(km[1])/1.60934:0,items:items?Number(items[1]):0,stores:stores?Number(stores[1]):1};
}
function formatCurrency(v){return new Intl.NumberFormat("en-CA",{style:"currency",currency:"CAD",maximumFractionDigits:2}).format(v);}
module.exports={analyzeOffer,parseOfferText,defaults};
