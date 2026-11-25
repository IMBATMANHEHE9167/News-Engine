"""The LLM layer (version 2): a language model reads each stored report's full article (Marathi or English), fills a fixed
form, and that reading DECIDES: whether the report is a real incident in Pune district, its type, whether it is a new
incident or a later development in a known case, the day the crime happened, and the facts that identify the case (the
names of victims and accused, kept only as matching keys, and a short neutral label).

Google Gemini, free tier (key in the GEMINI_API_KEY secret). Checks, so no single reading decides alone:
  1. A reader (Flash-Lite) reads every report.
  2. Where the reader and the rules disagree (incident or not, or the family of type), a SECOND reader of a different model
     reads the article on its own. Two readings that agree decide; otherwise the one the rules agree with (two of three).
  3. Only when all three differ does an expert (Flash, ~20 a day) read it.
  4. Judges: when two reports are close (same kind of crime, same area, within two days) but not certainly the same
     incident, a reader is shown both and says whether they are the same incident. Verdicts are kept (data/pairs.json).
The form is enforced by a response schema. Daily use is counted per model (resets at midnight Pacific time); on a
"limit reached" answer the model is rested until then. Progress and errors go to llmstate.json."""
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import engine as E

DATA = Path(__file__).resolve().parent.parent / 'data'
API = 'https://generativelanguage.googleapis.com/v1beta'
CFG = E.R['llm']
VERSION = CFG['version']
DEADLINE = float('inf')   # set by collect.py: no AI work starts after it, so a run always ends in time to save
TYPES = [c['id'] for c in E.CATS]
PARTS = ['morning', 'afternoon', 'evening', 'night', 'unknown']
WEAPONS = ['koyta', 'sword_or_knife', 'firearm', 'blunt_object', 'vehicle', 'fire_or_acid', 'none_or_unknown']
ACTIONS = ['arrest', 'detained', 'fir_registered', 'mcoca', 'mpda', 'externment', 'chargesheet', 'property_action', 'none']
KINDS = ['new_incident', 'development', 'not_incident']
WHY = ['none', 'outside_pune_district', 'no_specific_incident', 'suicide_or_natural_death', 'animal_attack', 'other']

SYSTEM = """You read Indian news reports (Marathi or English) about Pune district, Maharashtra, for a crime-incident database.
Accuracy matters more than anything: read the whole article, answer only from it, never guess. For each article:
- kind:
  new_incident = the article reports a specific crime, road accident or fire that happened (including the first report of
    an arrest for a recent specific crime).
  development = the article is mainly about a later stage of one specific earlier case: arrest days or weeks later,
    custody, chargesheet, court hearing, probe details, new twist, victim's family speaking, protest over that case.
  not_incident = anything else: policy, infrastructure, buildings, statistics, crime trends, features, opinion,
    advisories, awareness drives, festivals, political statements, court rulings on general matters, suicides, natural
    or accidental deaths that are not road accidents or fires, animal attacks, and ANY incident outside Pune district
    (Pune city, Pimpri-Chinchwad and Pune rural talukas only).
- not_reason: why it is not_incident; "none" otherwise.
- type: murder = intentional killing (not a road death, not attempt to murder); women = rape, molestation, dowry
  harassment, POCSO, stalking, domestic violence against women or children; kidnap; extortion (incl. ransom, sextortion,
  protection money); robbery (incl. chain or mobile snatching, dacoity, armed robbery); burglary (house, shop, temple
  break-in); drugs; cyber (online or any fraud, cheating, scams); violence (assault, attack with weapons, attempt to
  murder, gang clash, firing without death, illegal weapons seized); theft; accident (road accident only, including a
  vehicle hitting a person); fire (fire or explosion). For a development, the type of the original crime. "none" only
  if not_incident.
- incident_date: the day the crime itself happened (YYYY-MM-DD), for developments too (the day of the original crime,
  e.g. "the June 22 murder"). The article's publication date is given: resolve "yesterday", "on Monday", "last week",
  Marathi dates against it. Empty if the article does not state or clearly imply it. Never the publication date by default.
- incident_date_certain: true if the day is stated or clearly implied; false if approximate.
- victims: names of the victims exactly as given, in English letters (transliterate Marathi). Empty list if unnamed.
- accused: names of the accused or suspects, in English letters. Empty list if unnamed.
- case_label: 6 to 14 words in English that identify THIS specific case so that another report of the same case would
  get almost the same label, with NO personal names: who, what, where, e.g. "realtor pushed off Lohagad Fort by fiancee
  and her lover", "trainee police sub-inspector harassed wife for dowry, threatened with pistol".
- outcome: fatal if anyone died, injured if someone was hurt and no one died, none if no one was hurt, unknown if not stated.
- place: the most specific place where it happened, as written, in English letters, e.g. "Vetal Tekdi, Kothrud" or
  "near Dange Chowk, Wakad". Empty if not stated. Never a person's home town, residence, or the court or police station
  where the case is being heard.
- locality: the neighbourhood, village or town where it happened, in English letters. Empty if not stated.
- police_station: the police station that registered the case, in English letters, without the words "police station".
- time: 24-hour HH:MM if stated, else empty. part_of_day from the article.
- method: how it was done, at most 12 words, no names.
- victim_role: e.g. delivery worker, woman pedestrian, jeweller, senior citizen; empty if not stated.
- gang: the name of a criminal gang as the article names it (e.g. "Andekar gang"); empty if none.
- summary: one neutral English sentence, at most 30 words, with NO personal names.
- connected: other, SEPARATE incidents this one is said to be connected to (at most 2), e.g. an attack described as revenge
  for an earlier murder, a gang clash in retaliation for an earlier assault, an earlier crime by the same accused that the
  article names. Not other reports of this same incident. For each: relation (revenge = done to avenge it; retaliation =
  a counter-attack in a feud; feud = part of the same rivalry; same_accused = an earlier crime of the same accused;
  sequel = a later incident caused by it), description (6 to 14 words in English, NO personal names, e.g. "murder of a
  young man in Katraj a year earlier"), date (YYYY-MM-DD, may be approximate; empty if unknown), victims and accused of
  THAT incident (names in English letters, empty lists if unnamed). An empty list if none is mentioned."""

ITEM = {
    'type': 'OBJECT',
    'properties': {
        'id': {'type': 'STRING'},
        'kind': {'type': 'STRING', 'enum': KINDS},
        'not_reason': {'type': 'STRING', 'enum': WHY},
        'type': {'type': 'STRING', 'enum': TYPES + ['none']},
        'incident_date': {'type': 'STRING'},
        'incident_date_certain': {'type': 'BOOLEAN'},
        'victims': {'type': 'ARRAY', 'items': {'type': 'STRING'}},
        'accused': {'type': 'ARRAY', 'items': {'type': 'STRING'}},
        'case_label': {'type': 'STRING'},
        'outcome': {'type': 'STRING', 'enum': ['fatal', 'injured', 'none', 'unknown']},
        'place': {'type': 'STRING'},
        'locality': {'type': 'STRING'},
        'police_station': {'type': 'STRING'},
        'time': {'type': 'STRING'},
        'part_of_day': {'type': 'STRING', 'enum': PARTS},
        'weapon': {'type': 'STRING', 'enum': WEAPONS},
        'method': {'type': 'STRING'},
        'victim_role': {'type': 'STRING'},
        'victim_age': {'type': 'INTEGER', 'nullable': True},
        'offenders': {'type': 'INTEGER', 'nullable': True},
        'minor_involved': {'type': 'BOOLEAN'},
        'gang': {'type': 'STRING'},
        'police_action': {'type': 'ARRAY', 'items': {'type': 'STRING', 'enum': ACTIONS}},
        'summary': {'type': 'STRING'},
        'connected': {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {
            'relation': {'type': 'STRING', 'enum': ['revenge', 'retaliation', 'feud', 'same_accused', 'sequel']},
            'description': {'type': 'STRING'}, 'date': {'type': 'STRING'},
            'victims': {'type': 'ARRAY', 'items': {'type': 'STRING'}}, 'accused': {'type': 'ARRAY', 'items': {'type': 'STRING'}}},
            'required': ['relation', 'description', 'date', 'victims', 'accused']}},
    },
    'required': ['id', 'kind', 'not_reason', 'type', 'incident_date', 'incident_date_certain', 'victims', 'accused',
                 'case_label', 'outcome', 'place', 'locality', 'police_station', 'time', 'part_of_day', 'weapon', 'method',
                 'victim_role', 'minor_involved', 'gang', 'police_action', 'summary', 'connected'],
}
SCHEMA = {'type': 'ARRAY', 'items': ITEM}

JUDGE = """You compare pairs of news reports from Pune district. For each pair, decide whether both reports are about the
SAME single incident or case: the same crime event with the same victims. One may be another newspaper's version (often in
Marathi while the other is in English), or a later development of the other (arrest, custody, chargesheet, new details).
Decide on the specific facts: who the victims and accused are (their roles, ages, jobs), what exactly happened, where,
and the sums or numbers involved. The "happened" dates were read automatically and are sometimes wrong, and a report can
appear days after the crime: do not decide on dates alone. Two similar crimes of the same kind in the same area are NOT
the same incident: different victims, different sums or a different sequence of events mean different incidents.
If the facts do not clearly show it is the same incident, answer false."""
PAIR = {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {'pair': {'type': 'STRING'}, 'same': {'type': 'BOOLEAN'}},
                                   'required': ['pair', 'same']}}


class Busy(Exception):
    """The model is overloaded right now (HTTP 500/503): try again shortly or use the next model. Not counted."""


class Gone(Exception):
    """The model refuses this key (retired, or not available to new users): rest it for the day. Not counted."""


class Limit(Exception):
    """The model's allowance is used up for now."""


def pacific_day():
    return datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d')


def call(key, model, payload, timeout=150):
    req = urllib.request.Request('%s/models/%s:generateContent' % (API, model), data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json', 'x-goog-api-key': key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')[:300]
        if e.code in (500, 503, 504):
            raise Busy(body) from None
        if e.code in (403, 404):
            raise Gone(body) from None
        if e.code == 429:
            raise Limit(body) from None
        raise RuntimeError('HTTP %d %s' % (e.code, body)) from None


def answer(res):
    """The JSON text of an answer. A missing answer (blocked, cut off) is an error naming the reason."""
    try:
        return json.loads(res['candidates'][0]['content']['parts'][0]['text'])
    except (KeyError, IndexError, TypeError, ValueError):
        why = (res.get('promptFeedback') or {}).get('blockReason') or ((res.get('candidates') or [{}])[0].get('finishReason'))
        raise RuntimeError('no usable answer (%s)' % (why or 'empty')) from None


def resolve_models(key):
    """Our configured names -> the IDs this key can actually use (Google renames and retires models)."""
    req = urllib.request.Request(API + '/models?pageSize=500', headers={'x-goog-api-key': key})
    with urllib.request.urlopen(req, timeout=30) as r:
        models = json.loads(r.read().decode('utf-8')).get('models', [])
    usable = [m['name'].split('/', 1)[1] for m in models if 'generateContent' in m.get('supportedGenerationMethods', [])]
    out = {}
    for role in ('readers', 'experts'):
        out[role] = []
        for want in CFG[role]:
            exact = [u for u in usable if u == want]
            close = sorted(u for u in usable if u.startswith(want + '-') and 'tts' not in u and 'image' not in u)
            pick = (exact or [u for u in close if 'preview' not in u] or close or [None])[0]
            if pick:
                out[role].append(pick)
    return out


def read(key, model, batch):
    """One request: several articles -> {id: filled form}."""
    parts = ['ARTICLE id=%s\nPublished: %s\nHeadline: %s\nText: %s' % (rec['id'], E.day_str(E.day_of(rec['d'])), rec['t'], text[:CFG['chars']])
             for rec, text in batch]
    payload = {
        'systemInstruction': {'parts': [{'text': SYSTEM}]},
        'contents': [{'role': 'user', 'parts': [{'text': '\n\n-----\n\n'.join(parts)}]}],
        'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': SCHEMA, 'temperature': 0},
    }
    forms = answer(call(key, model, payload))
    return {f.get('id'): f for f in forms if isinstance(f, dict)}


def compact(f, model):
    """The stored form: short keys, empty fields left out. Names are kept only as matching keys (E.name_keys)."""
    kind = f.get('kind') if f.get('kind') in KINDS else 'not_incident'
    ok = kind != 'not_incident'
    out = dict(v=VERSION, m=model, ok=ok, k={'new_incident': 'n', 'development': 'd'}.get(kind, 'x'),
               why=f.get('not_reason') if not ok else '', c=f.get('type') if ok else 'none', fu=kind == 'development',
               dt=E.valid_day(f.get('incident_date', '')), dc=bool(f.get('incident_date_certain')),
               vn=E.name_keys(f.get('victims') or []), an=E.name_keys(f.get('accused') or []), cl=(f.get('case_label') or '')[:140],
               o=f.get('outcome'), pl=f.get('place', ''), lo=f.get('locality', ''), ps=f.get('police_station', ''),
               tm=f.get('time', ''), pd=f.get('part_of_day', ''), w=f.get('weapon', ''), mo=f.get('method', ''),
               vr=f.get('victim_role', ''), va=f.get('victim_age'), n=f.get('offenders'), j=bool(f.get('minor_involved')),
               g=f.get('gang', ''), act=[a for a in (f.get('police_action') or []) if a != 'none'], s=f.get('summary', ''),
               rel=[{k: v for k, v in dict(r=c.get('relation'), cl=(c.get('description') or '')[:120], dt=E.valid_day(c.get('date', '')),
                                          vn=E.name_keys(c.get('victims') or []), an=E.name_keys(c.get('accused') or [])).items() if v}
                    for c in (f.get('connected') or [])[:2] if ok and c.get('relation')])
    if out['c'] not in TYPES:
        out['c'] = 'none'
    return {k: v for k, v in out.items() if v not in ('', None, [], 'unknown', 'none_or_unknown', 'none') or k in ('ok', 'c', 'v', 'm', 'k')}


def judge(key, model, pairs):
    """One request: up to pair_batch pairs of reports -> {pair key: same incident?}."""
    def side(r):
        L = E.best_reading(r) or {}
        return 'published %s | headline: %s | summary: %s | case: %s | happened: %s | where: %s | outcome: %s' % (
            E.day_str(E.day_of(r['d'])), r['t'], L.get('s', ''), L.get('cl', ''), r.get('i', ''),
            ', '.join(x for x in (L.get('pl', ''), L.get('lo', ''), E.AREA[r['a']]['name'] if r.get('a') in E.AREA else '') if x),
            r.get('o') or L.get('o') or 'not stated')
    text = '\n\n'.join('PAIR %s\nA: %s\nB: %s' % (k, side(a), side(b)) for k, a, b in pairs)
    payload = {
        'systemInstruction': {'parts': [{'text': JUDGE}]},
        'contents': [{'role': 'user', 'parts': [{'text': text}]}],
        'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': PAIR, 'temperature': 0},
    }
    return {x.get('pair'): bool(x.get('same')) for x in answer(call(key, model, payload)) if isinstance(x, dict)}


class Session:
    """Model choice, daily allowance and pacing for one run."""

    def __init__(self):
        self.key = os.environ.get('GEMINI_API_KEY', '').strip()
        try:
            self.state = json.loads((DATA / 'llmstate.json').read_text('utf-8'))
        except (OSError, ValueError):
            self.state = {}
        today = pacific_day()
        if self.state.get('day') != today:
            self.state = dict(day=today, used={}, rested={}, errors=[], models=self.state.get('models', {}))
        self.busy = {}          # "busy" answers per model this run
        self.cool = {}          # a busy model rests until this time, then is tried again (it is not out for the run)
        self.stop = None        # why reading stopped early, kept in llmstate so a slow run explains itself
        self.started = time.time()
        self.models = self.state.get('models') or {'readers': CFG['readers'], 'experts': CFG['experts']}
        if self.key:
            try:
                self.models = resolve_models(self.key)
                self.state['models'] = self.models
            except Exception as e:
                self.error('model list: %s' % e)
        self.gap = {'readers': 60.0 / CFG['rpm']['readers'] + 0.5, 'experts': 60.0 / CFG['rpm']['experts'] + 0.5}

    def error(self, msg):
        self.state['errors'] = (self.state.get('errors', []) + [str(msg)[:160]])[-12:]

    def has(self, model, role):
        return self.state['used'].get(model, 0) < CFG['rpd'][role] and not self.state['rested'].get(model) and self.cool.get(model, 0) <= time.time()

    def take(self, role, avoid=None):
        return next((m for m in self.models.get(role, []) if m != avoid and self.has(m, role)), None)

    def pick(self, role, avoid=None):
        """A model with allowance left. If the only ones left are resting after "busy" answers, wait for the first to
        come back (within the run's time) instead of ending the run: Google's free tier is often briefly busy."""
        while True:
            m = self.take(role, avoid)
            if m:
                return m
            resting = [self.cool[x] for x in self.models.get(role, []) if x != avoid and self.cool.get(x, 0) > time.time()
                       and self.state['used'].get(x, 0) < CFG['rpd'][role] and not self.state['rested'].get(x)]
            if not resting or not self.time_left():
                self.stop = self.stop or ('out of time' if resting else 'no model left today (allowance used or retired)')
                return None
            time.sleep(min(60, max(1, min(resting) - time.time())))

    def time_left(self):
        return time.time() - self.started < CFG['run_seconds'] and time.time() < DEADLINE

    def ask(self, role, model, fn):
        """Run one request with the usual handling. Returns its result, or None (and the reason is recorded).
        self.retry is True when the failure was the model's (limit, overload, retired), not the articles'."""
        self.retry = False
        try:
            out = fn()
            self.state['used'][model] = self.state['used'].get(model, 0) + 1
            return out
        except (Limit, Gone) as e:
            self.state['rested'][model] = True
            self.retry = True
            if isinstance(e, Gone):
                self.error('%s: not available, rested for today' % model)
        except Busy:
            n = self.busy[model] = self.busy.get(model, 0) + 1
            self.cool[model] = time.time() + min(300, 30 * n)     # rest 30 s, 60 s, ... up to 5 min, then try again
            self.retry = True
        except Exception as e:
            self.state['used'][model] = self.state['used'].get(model, 0) + 1
            self.error('%s: %s' % (model, e))
        finally:
            time.sleep(self.gap[role])
        return None


def _texts(batch_recs, texts, get):
    out = []
    for r in batch_recs:
        text = texts.get(r['id'])
        if text is None:
            try:
                text = E.page_text(get(r['u']))
            except Exception:
                text = ''
            texts[r['id']] = text
        out.append((r, text or ''))
    return out


def _read_pass(S, role, field, todo, budget, texts, get, avoid_own=False):
    """Read the reports in todo into rec[field], a batch per request. Failing articles are retried alone, then left."""
    i, used = 0, 0
    size = CFG['batch'] if role == 'readers' else 4
    while i < len(todo) and used < budget and S.time_left():
        first = todo[i]
        avoid = (first.get('L') or {}).get('m') if avoid_own else None
        model = S.pick(role, avoid)
        if not model:
            break
        batch = []
        while i < len(todo) and len(batch) < size:
            r = todo[i]
            if avoid_own and (r.get('L') or {}).get('m') == model:
                break                               # a second reading must come from another model
            batch.append(r)
            i += 1
        if not batch:
            i += 1
            continue
        pairs = _texts(batch, texts, get)
        forms = S.ask(role, model, lambda: read(S.key, model, pairs))
        used += 1
        if forms is None:
            if S.retry:
                i -= len(batch)                     # the model's failure: the same articles go to the next model
                used -= 1
                continue
            # An unusable answer (often a safety block on ONE article): read each article on its own, so the others are
            # not held back; only an article that fails on its own is counted against it.
            for r, t in (pairs if len(pairs) > 1 else []):
                one = S.ask(role, model, lambda: read(S.key, model, [(r, t)]))
                used += 1
                if one and one.get(r['id']):
                    r[field] = compact(one[r['id']], model)
                    r.pop('Lx', None)
                elif not S.retry:
                    r['Lx'] = r.get('Lx', 0) + 1
            if len(pairs) == 1:
                batch[0]['Lx'] = batch[0].get('Lx', 0) + 1
            continue
        for r in batch:
            f = forms.get(r['id'])
            if f:
                r[field] = compact(f, model)
                r.pop('Lx', None)
            else:
                r['Lx'] = r.get('Lx', 0) + 1
    return used


def run(items, texts, get):
    """Bring every report's readings up to date (changes items in place). Returns the status."""
    S = Session()
    if not S.key:
        S.state['note'] = 'no GEMINI_API_KEY secret: the LLM layer is off'
        return finish(S, items)
    left = CFG['per_run']['readers']
    if not S.state.get('lx_reset'):                     # failures counted while a retired model was in use: forgive
        for r in items:
            r.pop('Lx', None)
        S.state['lx_reset'] = 1
    fresh = lambda r: r.get('Lx', 0) < 3
    newest = lambda xs: sorted(xs, key=lambda r: r['d'], reverse=True)
    # 1. Reports nobody has read yet (they are kept out of the counts until read).
    left -= _read_pass(S, 'readers', 'L', newest([r for r in items if not r.get('L') and fresh(r)]), left, texts, get)
    # 2. Second readings: the first reading and the rules disagree.
    second = newest([r for r in items if E.verdict(r) == 'second' and fresh(r)])
    left -= _read_pass(S, 'readers', 'L2', second, left, texts, get, avoid_own=True)
    # 3. Readings from an older form: read again (newest first), so every report has the case facts.
    # (capped, so the newest news, second readings and the judge keep their share of the day's free requests)
    left -= _read_pass(S, 'readers', 'L', newest([r for r in items if r.get('L') and r['L'].get('v') != VERSION and fresh(r)]),
                       min(left, CFG['per_run'].get('reread', left)), texts, get)
    # 4. Three-way splits: the expert reads.
    split = [r for r in items if E.verdict(r) == 'expert' and r.get('Xx', 0) < 2]
    for r in split:
        r['Xx'] = r.get('Xx', 0) + 1
    _read_pass(S, 'experts', 'X', split, CFG['per_run']['experts'], texts, get)
    return finish(S, items)


def run_judges(pairs, cache):
    """Ask whether close pairs are the same incident. pairs: [(key, rec_a, rec_b)]; answers go into cache {key: bool}."""
    S = Session()
    if not S.key or not pairs:
        return 0
    asked, n, k, tries = 0, CFG['pair_batch'], 0, 0
    while k < len(pairs):
        if asked >= CFG['per_run']['judges'] or not S.time_left():
            break
        model = S.pick('readers')
        if not model:
            break
        chunk = pairs[k:k + n]
        res = S.ask('readers', model, lambda: judge(S.key, model, chunk))
        asked += 1
        if res is None and S.retry and tries < 2:
            tries += 1                          # busy or at its limit: the same pairs go to the next model, not skipped
            continue
        k, tries = k + n, 0
        for key, _, _ in chunk:
            if res and key in res and cache.get(key) not in ('same', 'diff'):
                cache[key] = res[key]
    S.state['judged'] = S.state.get('judged', 0) + asked
    _save(S.state)
    return asked


def audit_judges(cache, by_id, first=()):
    """A stronger model re-judges the fast judge's riskiest verdicts, both ways: a "same" across different days, areas
    or types, and a "different" between reports that look alike (same area, same type, published within two days), since
    a "different" keeps two reports apart for good. Riskiest first, then the newest. Its answer is final ('same' or
    'diff'), never asked again."""
    S = Session()
    if not S.key:
        return 0
    def risk(k):
        a, b = (by_id.get(x) for x in k.split('|'))
        if not a or not b:
            return None
        da = E.day_of(a['d']) if not a.get('i') else (E.date.fromisoformat(a['i']) - E.date(1970, 1, 1)).days
        db = E.day_of(b['d']) if not b.get('i') else (E.date.fromisoformat(b['i']) - E.date(1970, 1, 1)).days
        if cache[k] is True:
            score = (abs(da - db) > 1) + (a.get('a') != b.get('a')) + (a.get('c') != b.get('c'))
            va, vb = (E.best_reading(a) or {}).get('vn') or [], (E.best_reading(b) or {}).get('vn') or []
            if va and vb and not E.names_meet(va, vb, set()):
                score += 5                       # a "same" between reports whose victim names differ: it now joins them
                                                 # over the name check (cases.join), so the expert re-checks it early
        else:
            score = (a.get('a') == b.get('a')) + (a.get('c') == b.get('c')) + (abs(E.day_of(a['d']) - E.day_of(b['d'])) <= 2)
            va, vb = (E.best_reading(a) or {}).get('vn') or [], (E.best_reading(b) or {}).get('vn') or []
            if va and vb and E.names_meet(va, vb, set()):
                score += 10                      # a "different" against a victim named in both: re-checked first
        return score, max(a['d'], b['d'])
    todo = sorted((k for k, v in cache.items() if v in (True, False) and risk(k)), key=risk, reverse=True)
    # Conflicting verdicts (judged "same" yet kept apart by a "different" across the same two cases) are settled first.
    lead = [k for k in dict.fromkeys(first) if cache.get(k) in (True, False) and k.split('|')[0] in by_id and k.split('|')[1] in by_id]
    todo = lead + [k for k in todo if k not in set(lead)]
    asked, n = 0, CFG['pair_batch']
    for k in range(0, len(todo), n):
        if asked >= CFG['per_run'].get('audit', 1):
            break
        model = S.pick('experts')
        if not model:
            break
        chunk = [(key, by_id[key.split('|')[0]], by_id[key.split('|')[1]]) for key in todo[k:k + n]]
        res = S.ask('experts', model, lambda: judge(S.key, model, chunk))
        asked += 1
        for key, _, _ in chunk:
            if res and key in res:
                cache[key] = 'same' if res[key] else 'diff'
    S.state['audited'] = sum(1 for v in cache.values() if v in ('same', 'diff'))
    S.state['overturned'] = sum(1 for v in cache.values() if v == 'diff')
    _save(S.state)
    return asked


def _save(state):
    (DATA / 'llmstate.json').write_text(json.dumps(state, ensure_ascii=False, indent=1), 'utf-8')


def finish(S, items):
    st = S.state
    cur = [r for r in items if (r.get('L') or {}).get('v') == VERSION]
    v = [E.verdict(r) for r in items]
    st['last_run'] = dict(busy=sum(S.busy.values()), stop=S.stop or ('out of time' if not S.time_left() else "nothing left to read, or this run's share used"))
    st.update(read=len(cur), older=sum(1 for r in items if r.get('L') and r['L'].get('v') != VERSION),
              unread=sum(1 for r in items if not r.get('L')), second=v.count('second'), expert=v.count('expert'),
              not_incident=sum(1 for x in v if isinstance(x, dict) and not x.get('ok')),
              updated=E.iso(datetime.now(timezone.utc)))
    _save(st)
    print('llm: %s' % json.dumps({k: st.get(k) for k in ('used', 'read', 'older', 'unread', 'second', 'expert', 'not_incident', 'note')}, ensure_ascii=False))
    return st


# English for Marathi headlines that no reader reads in full (situations, organised-crime searches): one plain sentence
# each, from the headline alone, kept with the report ('en') so it is asked once.
ENGLISH = """Each line is a news headline from Pune district, most in Marathi: an id, a tab, then the headline. For each, write
one plain, neutral English sentence (at most 20 words) saying what the headline reports. Keep place names; leave out the
names of victims and of minors. Do not add anything the headline does not say."""
EN_SCHEMA = {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {'id': {'type': 'STRING'}, 'en': {'type': 'STRING'}},
                                        'required': ['id', 'en']}}


def english(rows, limit=4, size=25):
    """Give rows with a Marathi headline and no English ('en') one sentence of English. Changes rows in place."""
    todo = [r for r in rows if re.search('[ऀ-ॿ]', r.get('t', '')) and not r.get('en')]
    if not todo:
        return 0
    S = Session()
    if not S.key:
        return 0
    asked = 0
    for k in range(0, len(todo), size):
        if asked >= limit:
            break
        model = S.take('readers')
        if not model:
            break
        chunk = todo[k:k + size]
        text = '\n'.join('%s\t%s' % (r['id'], r['t']) for r in chunk)
        payload = {'systemInstruction': {'parts': [{'text': ENGLISH}]}, 'contents': [{'role': 'user', 'parts': [{'text': text}]}],
                   'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': EN_SCHEMA, 'temperature': 0}}
        res = S.ask('readers', model, lambda: answer(call(S.key, model, payload)))
        asked += 1
        got = {x.get('id'): (x.get('en') or '').strip() for x in (res or []) if isinstance(x, dict)}
        for r in chunk:
            if got.get(r['id']):
                r['en'] = got[r['id']][:200]
    _save(S.state)
    return asked


# Situations (public order): the reader reads each report and says what, when and where. Its reading decides, as for
# incidents: whether it is a public-order situation in Pune district, its kind, planned or under way, the day it happens,
# the venue and the area of ours that contains it (the reader knows Pune's landmarks: "Pune RTO" is in Sangamwadi),
# and one English sentence.
SIT_VERSION = 2
SIT_AREAS = {a['name']: a['id'] for a in E.AREAS}
SITUATION = """You read Indian news reports (Marathi or English) about public-order situations in Pune district, Maharashtra:
protests, morchas, dharnas, sit-ins, bandhs, road blockades (rasta roko), strikes, hunger strikes, prohibitory orders,
unrest and clashes; disruptions of transport or public services; and emergencies. For each article, fill the form from the headline and the text (when the text is empty, decide
from the headline alone: an empty text is never a reason to say false):
- is_situation: true only for such a situation in Pune district (Pune city, Pimpri-Chinchwad, Pune rural talukas). False
  for ordinary crimes, politics without a public action, court cases, events elsewhere, and features.
- kind: unrest (clashes, stone pelting, lathi charge), order (prohibitory orders), bandh, block (road blockade), fast
  (hunger strike), strike (work stoppage), protest (any other protest, morcha, dharna, sit-in, march),
  emergency (bomb threat or hoax, evacuation, building, wall or hoarding collapse, gas leak, flooding, major fire),
  disruption (metro, train or bus breakdown or suspension, stranded commuters, road closure or traffic diversion, long
  traffic jam, water or power cut).
- status: planned if it is announced for a later day; ongoing if it is happening or continues; over if it took place.
- starts: the day it happens or starts (YYYY-MM-DD); resolve "tomorrow", "from Monday", "November 23" against the
  publication date given. Empty if not stated.
- venue: where it happens, in English letters, as specific as the article says (e.g. "outside Pune RTO").
- area: the one area from the list that contains the venue, using your knowledge of Pune's landmarks and roads (e.g.
  Pune RTO and Sangamwadi: Pune Station / Bund Garden; Collector office: Pune Station / Bund Garden; PMC headquarters:
  Shivajinagar; Alka Talkies chowk: Old city peths). "none" if no place in Pune district is named or implied.
- summary: one neutral English sentence, at most 25 words: who, what, why, when, where."""
SIT_SCHEMA = {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {
    'id': {'type': 'STRING'}, 'is_situation': {'type': 'BOOLEAN'},
    'kind': {'type': 'STRING', 'enum': [k for k, _, _ in E.SITU_KINDS]},
    'status': {'type': 'STRING', 'enum': ['planned', 'ongoing', 'over']}, 'starts': {'type': 'STRING'},
    'venue': {'type': 'STRING'}, 'area': {'type': 'STRING', 'enum': sorted(SIT_AREAS) + ['none']},
    'summary': {'type': 'STRING'}},
    'required': ['id', 'is_situation', 'kind', 'status', 'starts', 'venue', 'area', 'summary']}}


def read_situations(rows, get, limit=4, size=6):
    """Give the newest unread situation reports a reading ('S'); changes rows in place. Returns requests made."""
    todo = sorted((r for r in rows if (r.get('S') or {}).get('v') != SIT_VERSION and r.get('Sx', 0) < 3),
                  key=lambda r: r['d'], reverse=True)
    if not todo:
        return 0
    S = Session()
    if not S.key:
        return 0
    asked = 0
    for k in range(0, len(todo), size):
        if asked >= limit:
            break
        model = S.take('readers')
        if not model:
            break
        chunk, parts = todo[k:k + size], []
        for r in chunk:
            text = ''
            if 'news.google.com' not in r['u']:            # Google News links lead to a redirect page, not the article
                try:
                    text = E.page_text(get(r['u']))[:1800]
                except Exception:
                    text = ''
            parts.append('ARTICLE id=%s\nPublished: %s\nHeadline: %s\nText: %s' % (r['id'], E.day_str(E.day_of(r['d'])), r['t'], text))
        payload = {'systemInstruction': {'parts': [{'text': SITUATION}]},
                   'contents': [{'role': 'user', 'parts': [{'text': '\n\n-----\n\n'.join(parts)}]}],
                   'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': SIT_SCHEMA, 'temperature': 0}}
        res = S.ask('readers', model, lambda: answer(call(S.key, model, payload)))
        asked += 1
        got = {x.get('id'): x for x in (res or []) if isinstance(x, dict)}
        for r in chunk:
            f = got.get(r['id'])
            if not f:
                if not S.retry:
                    r['Sx'] = r.get('Sx', 0) + 1
                continue
            r.pop('Sx', None)
            r['S'] = {k: v for k, v in dict(v=SIT_VERSION, m=model, ok=bool(f.get('is_situation')), k=f.get('kind'),
                                            st=f.get('status'), w=E.valid_day(f.get('starts')), vn=(f.get('venue') or '')[:120],
                                            a=SIT_AREAS.get(f.get('area')), s=(f.get('summary') or '')[:220]).items()
                      if v not in ('', None) or k in ('ok', 'v')}
            if r['S'].get('s') and re.search('[ऀ-ॿ]', r['t']) and not r.get('en'):
                r['en'] = r['S']['s']
    _save(S.state)
    return asked


# ---- The AI gate. The word rules find most incidents, but a headline they have no word for ("held for hacking senior to
# death"), or one with a word that usually means "not an incident" ("bail"), was turned away for good and the AI never saw
# it. Now every Pune report the rules turn away on wording alone is shown to the AI, headline and opening lines, in
# batches. Its answer only opens the door: an incident let in this way is then read in full like any report, and because
# the rules said no, a second reader of another model must agree before it is counted (engine.verdict, 'tg').
TRIAGE = """You sort news items (Marathi or English, from Pune news sources and their accounts on X) for a crime and
public-safety desk covering Pune district (Pune city, Pimpri-Chinchwad, Pune rural talukas). For each item:
- incident: true if it reports a specific crime, road accident, fire or similar incident that happened in Pune district,
  or a later development of one (arrest, raid, seizure, charge sheet, court step in a Pune case). False for policy, civic
  works, schedules, awareness drives, statistics and trends, features, politics, sports, and anything outside Pune district.
- type: the incident's type (none if not an incident).
- situation: true if it reports a live or announced public situation in Pune district: a protest, bandh, strike, road
  blockade, unrest or prohibitory order; a disruption of transport or services (metro, train or bus breakdown, stranded
  commuters, road closure or diversion, long traffic jam, water or power cut); or an emergency (bomb threat, evacuation,
  building or wall collapse, gas leak, flooding, major fire).
- kind: the situation's kind (none if not a situation)."""


def triage(cands, limit=6, size=30):
    """cands: [{id, t, x, d}] -> {id: {'i': type or '', 's': kind or ''}} for the items answered (at most limit requests)."""
    S = Session()
    if not S.key or not cands:
        return {}
    kinds = [k for k, _, _ in E.SITU_KINDS]
    schema = {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {
        'id': {'type': 'STRING'}, 'incident': {'type': 'BOOLEAN'}, 'type': {'type': 'STRING', 'enum': TYPES + ['none']},
        'situation': {'type': 'BOOLEAN'}, 'kind': {'type': 'STRING', 'enum': kinds + ['none']}},
        'required': ['id', 'incident', 'type', 'situation', 'kind']}}
    out, asked = {}, 0
    for k in range(0, len(cands), size):
        if asked >= limit or not S.time_left():
            break
        model = S.pick('readers')
        if not model:
            break
        chunk = cands[k:k + size]
        parts = ['ITEM id=%s\nPublished: %s\nHeadline: %s\nOpening: %s' % (c['id'], E.day_str(E.day_of(c['d'])), c['t'], (c.get('x') or '')[:400])
                 for c in chunk]
        payload = {'systemInstruction': {'parts': [{'text': TRIAGE}]},
                   'contents': [{'role': 'user', 'parts': [{'text': '\n\n-----\n\n'.join(parts)}]}],
                   'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': schema, 'temperature': 0}}
        res = S.ask('readers', model, lambda: answer(call(S.key, model, payload)))
        asked += 1
        for f in res or []:
            if isinstance(f, dict) and f.get('id') in {c['id'] for c in chunk}:
                t = f.get('type') if f.get('incident') and f.get('type') in TYPES else ''
                s = f.get('kind') if f.get('situation') and f.get('kind') in kinds else ''
                out[f['id']] = {'i': t, 's': s}
    S.state['triaged'] = S.state.get('triaged', 0) + len(out)
    _save(S.state)
    return out
