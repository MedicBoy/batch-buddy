const CACHE="batch-buddy-v2";
const CORE=["/","/index.html","/styles.css","/app.js","/manifest.webmanifest"];
self.addEventListener("install",e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE))));
self.addEventListener("activate",e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener("fetch",e=>{const u=new URL(e.request.url);if(e.request.method!=="GET"||u.origin!==self.location.origin||u.pathname.startsWith("/api/"))return;e.respondWith(caches.match(e.request).then(c=>c||fetch(e.request)));});
