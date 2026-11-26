// Sonda di streaming: 1 sessione + 1 richiesta chat reale al gateway distribuito. Stampa SOLO tempi e dimensioni dei chunk (mai il token).
import { createHash } from 'node:crypto';
const EP = process.env.EP, O = process.env.ORIGIN, Q = process.env.QUESTION || 'Racconta in dettaglio, in almeno quindici righe, la storia di Loki nel Marvel Cinematic Universe.';
const H = { Origin: O, 'Content-Type': 'application/json' };
const c = await (await fetch(EP + '/v1/challenge', { headers: H })).json();
let n = 0; for (;;) { const h = createHash('sha256').update(`${c.salt}.${c.ts}.${n}`).digest(); let z = 0; for (const b of h) { if (b === 0) { z += 8; continue; } z += Math.clz32(b) - 24; break; } if (z >= c.bits) break; n++; }
const s = await (await fetch(EP + '/v1/session', { method: 'POST', headers: H, body: JSON.stringify({ ...c, n: String(n) }) })).json();
const t0 = performance.now();
const r = await fetch(EP + '/v1/chat', { method: 'POST', headers: { ...H, Accept: 'text/event-stream', Authorization: 'Bearer ' + s.token }, body: JSON.stringify({ question: Q, stream: true }) });
const hd = {}; for (const k of ['content-type', 'content-encoding', 'cache-control', 'x-content-type-options', 'transfer-encoding', 'cf-cache-status', 'server']) hd[k] = r.headers.get(k);
console.log('status', r.status, JSON.stringify(hd), 'headers dopo', Math.round(performance.now() - t0), 'ms');
const rd = r.body.getReader(); const dec = new TextDecoder(); let i = 0, tot = 0, ev = 0, chars = 0, buf = '';
for (;;) { const { done, value } = await rd.read(); if (done) break; i++; tot += value.length; buf += dec.decode(value, { stream: true }); let k; let e = 0; while ((k = buf.indexOf('\n\n')) >= 0) { const f = buf.slice(0, k); buf = buf.slice(k + 2); if (f.startsWith('data:')) { e++; ev++; try { const o = JSON.parse(f.slice(5)); if (o.t) chars += o.t.length; } catch {} } } console.log(`chunk#${i} t=${Math.round(performance.now() - t0)}ms bytes=${value.length} eventi=${e} caratteri_totali=${chars}`); }
console.log('FINE chunk=' + i + ' eventi=' + ev + ' byte=' + tot + ' caratteri=' + chars + ' totale=' + Math.round(performance.now() - t0) + 'ms');
