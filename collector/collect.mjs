// Runs on GitHub Actions every hour: read the feeds, keep the incident items, append to data/incidents.json.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { FEEDS, RULES_VERSION, extract, merge, pageText, enrich, recheck } from './engine.js';

const DATA = new URL('../data/', import.meta.url);
const UA = 'Mozilla/5.0 (compatible; FeedFetcher/1.0)';
const MAX_PAGES = 80;          // article pages read per run
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function readJson(name, fallback) {
  try { return JSON.parse(await readFile(new URL(name, DATA), 'utf8')); } catch { return fallback; }
}
async function get(url) {
  const res = await fetch(url, { headers: { 'User-Agent': UA, Accept: 'text/html, application/rss+xml, application/xml, */*' }, signal: AbortSignal.timeout(30000) });
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return res.text();
}

await mkdir(DATA, { recursive: true });
let items = await readJson('incidents.json', []);
const rejected = new Set(await readJson('rejected.json', []));   // items removed on re-check; never re-added
const sources = [];
let added = 0, changed = false;

for (const feed of FEEDS) {
  const row = { id: feed.id, name: feed.name, ok: false, found: 0, added: 0, note: '' };
  try {
    const recs = extract(feed, await get(feed.url));
    row.ok = true; row.found = recs.length; row.added = merge(items, recs, rejected);
    added += row.added;
  } catch (e) {
    row.note = String(e.message || e).slice(0, 80);
  }
  sources.push(row);
  console.log(`${feed.id.padEnd(4)} ${row.ok ? 'ok ' : 'ERR'} found=${row.found} new=${row.added} ${row.note}`);
}

// Read each article once. New items: find area and time. Items stored under older rules: re-check fully.
let read = 0, removed = 0;
for (const rec of items) {
  const old = rec.r !== RULES_VERSION;
  if (!old && (rec.e || (rec.a && rec.b))) continue;
  if (read >= MAX_PAGES) break;
  read++; changed = true;
  let text = '';
  try { text = pageText(await get(rec.u)); } catch { /* unreadable: judge on the headline */ }
  if (old) {
    if (!recheck(rec, text)) { rec.drop = 1; rejected.add(rec.id); removed++; console.log('removed: ' + rec.t.slice(0, 90)); }
  } else if (text) enrich(rec, text);
  rec.e = 1;
  await sleep(1000);
}
items = items.filter(r => !r.drop);
console.log(`articles read=${read} removed=${removed}`);

await writeFile(new URL('status.json', DATA), JSON.stringify({ updated: new Date().toISOString(), total: items.length, added, removed, rules: RULES_VERSION, sources }, null, 1));
if (added || changed) {
  await writeFile(new URL('incidents.json', DATA), '[\n' + items.map(x => JSON.stringify(x)).join(',\n') + '\n]\n');
  await writeFile(new URL('rejected.json', DATA), JSON.stringify([...rejected].slice(-5000)));
}
console.log(`total=${items.length} new=${added}`);
