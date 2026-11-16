// Runs on GitHub Actions every hour: read the feeds and newspaper indexes, keep the incident items,
// append to data/incidents.json. Also works backwards through Sakal's archive a few days per run.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { FEEDS, RULES_VERSION, extract, finish, merge, pageText, recheck, hashId } from './engine.js';

const DATA = new URL('../data/', import.meta.url);
const UA = 'Mozilla/5.0 (compatible; FeedFetcher/1.0)';
const MAX_PAGES = 260;           // article pages read per run for new items and re-checks
const BACKFILL_DAYS = 4;         // archive days read per run
const BACKFILL_PAGES = 90;       // article pages read per run for the archive
const BACKFILL_SPAN = 180;       // how far back the archive read goes, in days
const sleep = ms => new Promise(r => setTimeout(r, ms));
const IST = 19800000;
const istDate = t => new Date(t + IST).toISOString().slice(0, 10);

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
const rejected = new Set(await readJson('rejected.json', []));   // looked at and ruled out; never fetched or added again
const known = () => new Set(items.map(x => x.id));
const sources = [];
let added = 0, changed = false, pages = 0;

// Candidates from an index without headlines: read each page once, keep it only if it passes every check.
async function readCandidates(feed, cands, budget, fallbackDate) {
  const have = known();
  let kept = 0, fails = 0;
  for (const c of cands) {
    const id = hashId(c.link);
    if (have.has(id) || rejected.has(id)) continue;
    if (budget.left <= 0) break;
    budget.left--; changed = true;
    let rec = null, failed = false;
    try { rec = finish(feed, c, await get(c.link), fallbackDate); } catch { failed = true; }
    if (rec) kept += merge(items, [rec], rejected);
    else if (!failed) rejected.add(id);          // unreadable pages are retried next run
    else if (++fails >= 3) break;                // the site is refusing us right now: stop asking
    await sleep(600);
  }
  return kept;
}

const now = Date.now();
const budget = { left: MAX_PAGES };
for (const feed of FEEDS) {
  const row = { id: feed.id, name: feed.name, ok: false, found: 0, added: 0, note: '' };
  const urls = feed.daily ? [istDate(now), istDate(now - 864e5)].map(d => feed.url.replace('{date}', d)) : [feed.url];
  for (const url of urls) {
    try {
      const res = extract(feed, await get(url));
      row.ok = true; row.found += res.length;
      row.added += feed.kind === 'urlmap' ? await readCandidates(feed, res, budget, new Date(now)) : merge(items, res, rejected);
    } catch (e) {
      if (!row.ok) row.note = String(e.message || e).slice(0, 80);
    }
  }
  added += row.added;
  sources.push(row);
  console.log(`${feed.id.padEnd(4)} ${row.ok ? 'ok ' : 'ERR'} found=${row.found} new=${row.added} ${row.note}`);
}

// Every record is judged once with its full article text: type, place, the day and time it happened, and whether it is
// a fresh incident or a follow-up. Records judged under older rules are judged again.
let removed = 0;
for (const rec of items) {
  if (rec.e && rec.r === RULES_VERSION) continue;
  if (budget.left <= 0) break;
  budget.left--; changed = true;
  let text = '';
  try { text = pageText(await get(rec.u)); } catch { /* unreadable */ }
  // A page that cannot be read right now is not evidence against the record: try again on later runs,
  // and only after three failures judge on the headline alone.
  if (!text && (rec.x = (rec.x || 0) + 1) < 3) { await sleep(300); continue; }
  delete rec.x;
  if (!recheck(rec, text)) { rec.drop = 1; rejected.add(rec.id); removed++; console.log('removed: ' + rec.t.slice(0, 90)); }
  rec.e = 1;
  await sleep(600);
}
items = items.filter(r => !r.drop);

// History: walk back through Sakal's daily archive, a few days per run, until BACKFILL_SPAN days are covered.
const sakal = FEEDS.find(f => f.id === 'skl');
const bf = await readJson('backfill.json', null) || { next: istDate(now - 2 * 864e5), stop: istDate(now - BACKFILL_SPAN * 864e5), days: 0, kept: 0, note: '' };
if (sakal && bf.next >= bf.stop) {
  const bb = { left: BACKFILL_PAGES };
  for (let i = 0; i < BACKFILL_DAYS && bf.next >= bf.stop && bb.left > 0; i++) {
    const day = bf.next;
    try {
      const cands = extract(sakal, await get(sakal.url.replace('{date}', day)));
      const before = bb.left;
      bf.kept += await readCandidates(sakal, cands, bb, new Date(day + 'T12:00:00+05:30'));
      if (bb.left <= 0 && before > 0 && cands.length > before) break;      // day not finished: resume it next run
      bf.note = '';
    } catch (e) {
      bf.note = day + ': ' + String(e.message || e).slice(0, 60);
      if (/HTTP 4(03|29)/.test(bf.note)) break;                            // blocked or rate-limited: try again next run
    }
    bf.days++;
    bf.next = istDate(new Date(day + 'T12:00:00+05:30').getTime() - 864e5);
    changed = true;
  }
  await writeFile(new URL('backfill.json', DATA), JSON.stringify(bf, null, 1));
  console.log(`backfill next=${bf.next} days=${bf.days} kept=${bf.kept} ${bf.note}`);
}

await writeFile(new URL('status.json', DATA), JSON.stringify({ updated: new Date().toISOString(), total: items.length, added, removed, rules: RULES_VERSION,
  history: { reachedBack: bf.next, target: bf.stop, kept: bf.kept, note: bf.note }, sources }, null, 1));
if (added || changed) {
  await writeFile(new URL('incidents.json', DATA), '[\n' + items.map(x => JSON.stringify(x)).join(',\n') + '\n]\n');
  await writeFile(new URL('rejected.json', DATA), JSON.stringify([...rejected].slice(-20000)));
}
console.log(`total=${items.length} new=${added} removed=${removed}`);
