const CACHE="paddyguard-shell-v2";
const shell=["/","/app.js","/farm.bundle.js","/farm.utilities.css","/media.js","/language.js","/style.css","/manifest.webmanifest","/icon-192.png","/icon-512.png"];
self.addEventListener("install",event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(shell))));
self.addEventListener("activate",event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith("paddyguard-shell-")&&k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener("fetch",event=>{
  const url=new URL(event.request.url);
  if(event.request.method==="GET"&&url.origin===self.location.origin&&shell.includes(url.pathname)){
    event.respondWith(fetch(event.request).catch(()=>caches.match(event.request)));
  }
});
