'use strict';
const V='kbm-2026-09-10-55648';
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(['./','./index.html','./manifest.webmanifest'])).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;const u=new URL(e.request.url);
  const isPage=u.origin===location.origin&&(u.pathname.endsWith('/')||u.pathname.endsWith('index.html'));
  if(isPage){e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(V).then(c=>c.put(e.request,cp));return r;}).catch(()=>caches.match(e.request,{ignoreSearch:true})));return;}
  e.respondWith(caches.match(e.request).then(hit=>hit||fetch(e.request).then(r=>{if(r&&(r.ok||r.type==='opaque')){const cp=r.clone();caches.open(V).then(c=>c.put(e.request,cp));}return r;})));});
