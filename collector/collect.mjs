// Runs on GitHub Actions every hour: read the feeds, keep the incident items, append to data/incidents.json.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { FEEDS, extract, merge, pageText, enrich } from './engine.js';

const DATA = new URL('../data/', import.meta.url);
const UA = 'Mozilla/5.0 (compatible; FeedFetcher/1.0)';
const MAX_PAGES = 60;          // article pages read per run, to find area and time
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
const items = await readJson('incidents.json', []);
const sources = [];
let added = 0;

for (const feed of FEEDS) {
  const row = { id: feed.id, name: feed.name, ok: false, found: 0, added: 0, note: '' };
  try {
    const recs = extract(feed, await get(feed.url));
    row.ok = true; row.found = recs.length; row.added = merge(items, recs);
    added += row.added;
  } catch (e) {
    row.note = String(e.message || e).slice(0, 80);
  }
  sources.push(row);
  console.log(`${feed.id.padEnd(4)} ${row.ok ? 'ok ' : 'ERR'} found=${row.found} new=${row.added} ${row.note}`);
}

// Read each article once (newest first) where the feed did not give an area or a time.
let read = 0, placed = 0;
for (const rec of items) {
  if (read >= MAX_PAGES) break;
  if (rec.e || (rec.a && rec.b)) continue;
  rec.e = 1; read++;
  const had = rec.a;
  try { enrich(rec, pageText(await get(rec.u))); } catch { /* leave as is */ }
  if (!had && rec.a) placed++;
  await sleep(1200);
}
console.log(`articles read=${read} newly placed=${placed}`);

await writeFile(new URL('status.json', DATA), JSON.stringify({ updated: new Date().toISOString(), total: items.length, added, sources }, null, 1));
if (added || read) await writeFile(new URL('incidents.json', DATA), '[\n' + items.map(x => JSON.stringify(x)).join(',\n') + '\n]\n');
console.log(`total=${items.length} new=${added}`);
