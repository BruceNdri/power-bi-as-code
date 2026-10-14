// Valide chaque fichier JSON PBIR contre le schéma déclaré dans son "$schema" (références résolues en ligne).
// Usage : node valider.mjs <dossier .Report> [autres dossiers…] — les schémas sont téléchargés une fois puis gardés en cache.
import Ajv from 'ajv/dist/2020.js';
import Ajv7 from 'ajv';
import addFormats from 'ajv-formats';
import { readFileSync, readdirSync, statSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
const cache = new URL('./.cache-schemas/', import.meta.url).pathname; mkdirSync(cache, { recursive: true });
async function charger(uri) {
  const f = join(cache, encodeURIComponent(uri));
  if (existsSync(f)) return JSON.parse(readFileSync(f, 'utf8'));
  const r = await fetch(uri); if (!r.ok) throw new Error(`${r.status} ${uri}`);
  const t = await r.text(); writeFileSync(f, t); return JSON.parse(t);
}
const fichiers = []; const parcourir = d => { for (const n of readdirSync(d)) { const p = join(d, n); statSync(p).isDirectory() ? parcourir(p) : /\.(json|pbir|pbism|pbip)$|\.platform$/.test(n) && fichiers.push(p); } };
process.argv.slice(2).forEach(parcourir);
const compiles = new Map(); let ko = 0;
for (const f of fichiers) {
  const doc = JSON.parse(readFileSync(f, 'utf8'));
  const uri = doc.$schema; if (!uri) { console.log('SANS SCHEMA', f); continue; }
  if (!compiles.has(uri)) {
    const sch = await charger(uri);
    const A = (sch.$schema || '').includes('2020') ? Ajv : Ajv7;
    const ajv = new A({ strict: false, allErrors: true, loadSchema: charger, validateFormats: false });
    addFormats(ajv);
    compiles.set(uri, await ajv.compileAsync(sch));
  }
  const v = compiles.get(uri);
  if (!v(doc)) { ko++; console.log('ERREUR', f.replace(/.*Report\//, ''), JSON.stringify(v.errors.slice(0, 4).map(e => `${e.instancePath} ${e.message} ${JSON.stringify(e.params)}`))); }
}
console.log(`${fichiers.length} fichiers, ${ko} en erreur`);
