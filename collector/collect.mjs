// Runs on GitHub Actions every hour: read the feeds and newspaper indexes, keep the incident items,
// append to data/incidents.json. Also works backwards through Sakal's archive a few days per run.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { FEEDS, RULES_VERSION, extract, extractItems, finish, merge, pageText, parseFeed, parseSitemap, recheck, hashId } from './engine.js';

const DATA = new URL('../data/', import.meta.url);
const UA = 'Mozilla/5.0 (compatible; FeedFetcher/1.0)';
const MAX_PAGES = 260;           // article pages read per run for new items and re-checks
const BACKFILL_DAYS = 4;         // archive days read per run
const BACKFILL_PAGES = 90;       // article pages read per run for the archive
const BACKFILL_SPAN = 180;       // how far back the archive read goes, in days
const HISTORY_FROM = '2026-05-19';   // the city papers' history is read back to this day (same start as Sakal)
const ARCHIVE_PAGES = 200;       // article pages read per run from the city papers' monthly indexes
const FEED_PAGES_PER_RUN = 25;   // feed pages (10 stories each) read per run, per paged source
const RUN_LIMIT = 22 * 60e3;     // stop starting new history work after this long
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

// History from the city papers, back to HISTORY_FROM. Pune City is the engine's focus, so these go before Sakal.
//   paged   = a WordPress feed read page by page (?paged=N); headlines and summaries are in the feed.
//   monthly = a paper's monthly article index (addresses only); each likely candidate page is read once.
const bf = await readJson('backfill.json', null) || { next: istDate(now - 2 * 864e5), stop: istDate(now - BACKFILL_SPAN * 864e5), days: 0, kept: 0, note: '' };
const MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'];
const ym = (y, mName) => y * 100 + MONTHS.indexOf(mName.toLowerCase()) + 1;
const FROM_YM = +HISTORY_FROM.slice(0, 4) * 100 + +HISTORY_FROM.slice(5, 7);
const ARCHIVES = [
  { id: 'toi', kind: 'monthly', index: 'https://timesofindia.indiatimes.com/staticsitemap/toi/category/city/sitemap-index.xml',
    file: /\/city\/(\d{4})-([a-z]+)-\d+\.xml$/i, order: m => ym(+m[1], m[2]), path: /timesofindia\.indiatimes\.com\/city\/pune\//i },
  { id: 'ht', kind: 'monthly', index: 'https://www.hindustantimes.com/sitemap/index.xml',
    file: /\/sitemap\/([a-z]+)-(\d{4})\.xml$/i, order: m => ym(+m[2], m[1]), path: /hindustantimes\.com\/cities\/pune-news\//i },
  { id: 'ptm', kind: 'paged', url: p => `https://punemirror.com/feed/?paged=${p}` },
  { id: 'pkn', kind: 'paged', url: p => `https://www.punekarnews.in/feed/?paged=${p}` },
  { id: 'pcl', kind: 'paged', url: p => `https://punecitylive.in/feed/?paged=${p}` },
];
bf.src = bf.src || {};
const ab = { left: ARCHIVE_PAGES };
for (const A of ARCHIVES) {
  const st = bf.src[A.id] = bf.src[A.id] || { done: false, kept: 0, note: '' };
  if (st.done || Date.now() - now > RUN_LIMIT) continue;
  const feed = FEEDS.find(f => f.id === A.id);
  try {
    if (A.kind === 'paged') {
      // Pages shift as new stories appear, so a page may be read twice; known items are skipped.
      st.page = st.page || 1;
      for (let i = 0; i < FEED_PAGES_PER_RUN && !st.done; i++) {
        const list = parseFeed(await get(A.url(st.page)));
        if (!list.length) { st.done = true; break; }
        st.kept += merge(items, extractItems(feed, list.filter(x => istDate(x.date.getTime()) >= HISTORY_FROM)), rejected);
        st.reached = istDate(Math.min(...list.map(x => x.date.getTime())));
        if (st.reached < HISTORY_FROM) st.done = true; else st.page++;
        changed = true;
        await sleep(800);
      }
    } else {
      if (!st.files) {
        // Oldest month first is not needed; newest first fills the recent past soonest.
        st.files = [...(await get(A.index)).matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1].trim())
          .map(u => ({ u, m: u.match(A.file) })).filter(x => x.m && A.order(x.m) >= FROM_YM && A.order(x.m) <= +istDate(now).slice(0, 7).replace('-', ''))
          .sort((p, q) => A.order(q.m) - A.order(p.m)).map(x => x.u);
        st.i = 0;
      }
      while (st.i < st.files.length && ab.left > 0 && Date.now() - now < RUN_LIMIT) {
        const pseudo = { ...feed, kind: 'urlmap', path: A.path };
        const all = parseSitemap(await get(st.files[st.i])).filter(x => A.path.test(x.link));
        const cands = extractItems(pseudo, all).filter(c => !c.date || istDate(c.date.getTime()) >= HISTORY_FROM);
        const have = known();
        const open = cands.filter(c => !have.has(hashId(c.link)) && !rejected.has(hashId(c.link)));
        if (open.length) st.kept += await readCandidates(pseudo, open, ab, new Date(now));
        const still = open.filter(c => !known().has(hashId(c.link)) && !rejected.has(hashId(c.link))).length;
        if (still) break;                                   // budget used up or the site refused: same file next run
        st.i++; changed = true;
      }
      if (st.i >= st.files.length) st.done = true;
      st.reached = st.files[Math.min(st.i, st.files.length - 1)]?.match(A.file)?.slice(1).join(' ') || '';
    }
    st.note = '';
  } catch (e) {
    st.note = String(e.message || e).slice(0, 60);
  }
  console.log(`history ${A.id} ${st.done ? 'done' : 'at ' + (st.reached || '?')} kept=${st.kept} ${st.note}`);
}

// History: walk back through Sakal's daily archive, a few days per run, until BACKFILL_SPAN days are covered.
const sakal = FEEDS.find(f => f.id === 'skl');
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
  console.log(`backfill next=${bf.next} days=${bf.days} kept=${bf.kept} ${bf.note}`);
}
await writeFile(new URL('backfill.json', DATA), JSON.stringify(bf, null, 1));

const archives = Object.fromEntries(Object.entries(bf.src).map(([id, s]) => [id, { done: s.done, reached: s.reached || '', kept: s.kept, note: s.note }]));
await writeFile(new URL('status.json', DATA), JSON.stringify({ updated: new Date().toISOString(), total: items.length, added, removed, rules: RULES_VERSION,
  history: { reachedBack: bf.next, target: bf.stop, kept: bf.kept, note: bf.note, from: HISTORY_FROM, archives }, sources }, null, 1));
if (added || changed) {
  await writeFile(new URL('incidents.json', DATA), '[\n' + items.map(x => JSON.stringify(x)).join(',\n') + '\n]\n');
  await writeFile(new URL('rejected.json', DATA), JSON.stringify([...rejected].slice(-20000)));
}
console.log(`total=${items.length} new=${added} removed=${removed}`);
