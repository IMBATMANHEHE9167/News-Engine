"""The LLM layer: a language model reads each stored report's full article (Marathi or English) and fills a fixed form.

Google Gemini, free tier (key in the GEMINI_API_KEY secret). Readers (Flash-Lite, 500 requests a day each) read every
report, up to BATCH articles per request. When a reader disagrees with the rules on whether a report is an incident or
on its type, a stronger model (Flash, about 20 a day each) reads it independently and the majority of the three decides:
neither the rules nor one model decides alone. The form is enforced by a response schema, so answers are always valid.

What the form adds: outcome, the exact place phrase (pinned with the OpenStreetMap place list), time, weapon, method,
victim role and age, offenders and whether minors were involved, gang, police action, follow-up or not, and a one-line
English summary with no personal names. Daily use is counted per model and resets at midnight Pacific time; on a "limit
reached" answer the model is rested until then. Progress and errors are written to llmstate.json."""
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
TYPES = [c['id'] for c in E.CATS]
PARTS = ['morning', 'afternoon', 'evening', 'night', 'unknown']
WEAPONS = ['koyta', 'sword_or_knife', 'firearm', 'blunt_object', 'vehicle', 'fire_or_acid', 'none_or_unknown']
ACTIONS = ['arrest', 'detained', 'fir_registered', 'mcoca', 'mpda', 'externment', 'chargesheet', 'property_action', 'none']

SYSTEM = """You read Indian news reports (Marathi or English) about Pune district, Maharashtra, for a crime-incident database.
For each article, fill the form exactly. Rules:
- is_incident: true only if the article reports a specific crime, road accident or fire that happened (or a later development
  in one: arrest, follow-up). False for features, opinion, statistics, court hearings about old cases, policy, protests,
  political statements, advisories, festivals, suicides, animal attacks, and anything outside Pune district.
- type: murder = intentional killing (not a road death, not attempt to murder); women = rape, molestation, dowry harassment,
  POCSO, stalking, domestic violence; kidnap; extortion (incl. ransom, sextortion, protection money); robbery (incl. chain or
  mobile snatching, dacoity, armed robbery); burglary (house or shop break-in); drugs; cyber (online or any fraud, cheating,
  scams); violence (assault, attack with weapons, attempt to murder, gang clash, firing without death); theft; accident (road
  accident only, including vehicle hitting a person); fire (fire or explosion). Use "none" if is_incident is false.
- outcome: fatal if anyone died, injured if someone was hurt and no one died, none if no one was hurt, unknown if not stated.
- follow_up: true if the article is mainly about a later development (arrest days later, custody, chargesheet, new twist).
- place: the most specific place where it happened, as written, in English letters (transliterate Marathi), e.g.
  "Vetal Tekdi, Kothrud" or "near Dange Chowk, Wakad". Empty if not stated. Never a person's home town or residence.
- locality: the neighbourhood, village or police station area where it happened, in English letters. Empty if not stated.
- date: the day it happened (YYYY-MM-DD) if the article states or clearly implies it, else empty. The article's own date
  is given; resolve "yesterday", weekday names and Marathi dates against it.
- time: 24-hour HH:MM if stated, else empty. part_of_day from the article.
- method: how it was done, at most 12 words, no names (e.g. "two men on a motorcycle snatched gold chain from pedestrian").
- victim_role: e.g. delivery worker, woman pedestrian, jeweller, senior citizen, IT employee, student; empty if not stated.
- gang: the name of a criminal gang or group as the article names it (e.g. "Andekar gang", "Ghaywal gang"); empty if none.
- summary: one neutral English sentence, at most 30 words, with NO personal names of victims, accused or minors.
Answer only from the article. Do not guess beyond it."""

ITEM = {
    'type': 'OBJECT',
    'properties': {
        'id': {'type': 'STRING'},
        'is_incident': {'type': 'BOOLEAN'},
        'type': {'type': 'STRING', 'enum': TYPES + ['none']},
        'outcome': {'type': 'STRING', 'enum': ['fatal', 'injured', 'none', 'unknown']},
        'follow_up': {'type': 'BOOLEAN'},
        'place': {'type': 'STRING'},
        'locality': {'type': 'STRING'},
        'date': {'type': 'STRING'},
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
    },
    'required': ['id', 'is_incident', 'type', 'outcome', 'follow_up', 'place', 'locality', 'date', 'time', 'part_of_day',
                 'weapon', 'method', 'victim_role', 'minor_involved', 'gang', 'police_action', 'summary'],
}
SCHEMA = {'type': 'ARRAY', 'items': ITEM}


class Busy(Exception):
    """The model is overloaded right now (HTTP 500/503): try again shortly or use the next model. Not counted."""


class Limit(Exception):
    """The model's allowance is used up for now."""


def pacific_day():
    return datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d')


def call(key, model, payload, timeout=120):
    req = urllib.request.Request('%s/models/%s:generateContent' % (API, model), data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json', 'x-goog-api-key': key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')[:300]
        if e.code in (500, 503):
            raise Busy(body) from None
        if e.code == 429:
            raise Limit(body) from None
        raise RuntimeError('HTTP %d %s' % (e.code, body)) from None


def resolve_models(key):
    """Our configured names -> the IDs this key can actually use (Google renames models; this keeps us working)."""
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


def read(key, model, batch, pub_days):
    """One request: up to BATCH articles -> list of filled forms."""
    parts = []
    for rec, text in batch:
        parts.append('ARTICLE id=%s\nPublished: %s\nHeadline: %s\nText: %s' % (rec['id'], pub_days[rec['id']], rec['t'], text[:CFG['chars']]))
    payload = {
        'systemInstruction': {'parts': [{'text': SYSTEM}]},
        'contents': [{'role': 'user', 'parts': [{'text': '\n\n-----\n\n'.join(parts)}]}],
        'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': SCHEMA, 'temperature': 0},
    }
    res = call(key, model, payload)
    try:
        txt = res['candidates'][0]['content']['parts'][0]['text']
        forms = json.loads(txt)
    except (KeyError, IndexError, ValueError) as e:
        raise RuntimeError('unreadable answer: %s' % str(e)[:80]) from None
    return {f.get('id'): f for f in forms if isinstance(f, dict)}


def compact(f, model):
    """The stored form: short keys, empty fields left out."""
    out = dict(v=VERSION, m=model, ok=bool(f.get('is_incident')), c=f.get('type'), o=f.get('outcome'), fu=bool(f.get('follow_up')),
               pl=f.get('place', ''), lo=f.get('locality', ''), dt=f.get('date', ''), tm=f.get('time', ''), pd=f.get('part_of_day', ''),
               w=f.get('weapon', ''), mo=f.get('method', ''), vr=f.get('victim_role', ''), va=f.get('victim_age'),
               n=f.get('offenders'), j=bool(f.get('minor_involved')), g=f.get('gang', ''), act=f.get('police_action') or [],
               s=f.get('summary', ''))
    return {k: v for k, v in out.items() if v not in ('', None, [], 'unknown', 'none_or_unknown') or k in ('ok', 'c', 'v', 'm')}


def run(items, texts, get):
    """Read the reports that have no current reading. Changes items in place; returns a status dict."""
    key = os.environ.get('GEMINI_API_KEY', '').strip()
    state = {}
    try:
        state = json.loads((DATA / 'llmstate.json').read_text('utf-8'))
    except (OSError, ValueError):
        pass
    today = pacific_day()
    if state.get('day') != today:
        state = dict(day=today, used={}, rested={}, errors=[], models=state.get('models', {}))
    status = dict(state)
    if not key:
        status['note'] = 'no GEMINI_API_KEY secret: the LLM layer is off'
        return finish(status, items)
    try:
        models = resolve_models(key)
        state['models'] = models
    except Exception as e:
        models = state.get('models') or {'readers': CFG['readers'], 'experts': CFG['experts']}
        state['errors'] = (state.get('errors', []) + ['model list: %s' % str(e)[:100]])[-10:]

    busy = {}

    def has(model, role):
        return state['used'].get(model, 0) < CFG['rpd'][role] and not state['rested'].get(model) and busy.get(model, 0) < 2

    def take(role):
        return next((m for m in models.get(role, []) if has(m, role)), None)

    def spend(model):
        state['used'][model] = state['used'].get(model, 0) + 1

    gap = {'readers': 60.0 / CFG['rpm']['readers'] + 0.5, 'experts': 60.0 / CFG['rpm']['experts'] + 0.5}
    started = time.time()

    # 1. Readers. Newest first, so today's news is read before history.
    todo = [r for r in sorted(items, key=lambda r: r['d'], reverse=True) if (r.get('L') or {}).get('v') != VERSION]
    pub = {r['id']: r['d'][:10] for r in todo}
    requests_left = CFG['per_run']['readers']
    i = 0
    while i < len(todo) and requests_left > 0 and time.time() - started < CFG['run_seconds']:
        model = take('readers')
        if not model:
            break
        batch = []
        while i < len(todo) and len(batch) < CFG['batch']:
            r = todo[i]
            i += 1
            text = texts.get(r['id'])
            if text is None:
                try:
                    text = E.page_text(get(r['u']))
                except Exception:
                    text = ''
                texts[r['id']] = text
            batch.append((r, text or ''))
        try:
            forms = read(key, model, batch, pub)
            spend(model)
            requests_left -= 1
            for r, _ in batch:
                if r['id'] in forms:
                    r['L'] = compact(forms[r['id']], model)
        except Limit:
            state['rested'][model] = True
            i -= len(batch)                          # same articles again with the next model
        except Busy:
            busy[model] = busy.get(model, 0) + 1     # overloaded: wait, retry once, then the next model; not counted
            i -= len(batch)
            time.sleep(20)
        except Exception as e:
            spend(model)
            requests_left -= 1
            state['errors'] = (state.get('errors', []) + ['%s: %s' % (model, str(e)[:120])])[-10:]
        time.sleep(gap['readers'])

    # 2. Tie-breaks. Where the reader and the rules disagree, a stronger model reads the article on its own.
    disputed = [r for r in items if (r.get('L') or {}).get('v') == VERSION and 'X' not in r and dispute(r)]
    left = CFG['per_run']['experts']
    k = 0
    while k < len(disputed) and left > 0:
        model = take('experts')
        if not model:
            break
        batch = []
        for r in disputed[k:k + CFG['batch']]:
            text = texts.get(r['id'])
            if text is None:
                try:
                    text = E.page_text(get(r['u']))
                except Exception:
                    text = ''
                texts[r['id']] = text
            batch.append((r, text or ''))
        try:
            forms = read(key, model, batch, {r['id']: r['d'][:10] for r, _ in batch})
            spend(model)
            left -= 1
            for r, _ in batch:
                f = forms.get(r['id'])
                if f:
                    r['X'] = dict(v=VERSION, m=model, ok=bool(f.get('is_incident')), c=f.get('type'))
            k += CFG['batch']
        except Limit:
            state['rested'][model] = True
        except Busy:
            busy[model] = busy.get(model, 0) + 1
            time.sleep(20)
        except Exception as e:
            spend(model)
            left -= 1
            k += CFG['batch']
            state['errors'] = (state.get('errors', []) + ['%s: %s' % (model, str(e)[:120])])[-10:]
        time.sleep(gap['experts'])

    status = dict(state)
    return finish(status, items)


def dispute(r):
    """The reader disagrees with the rules on whether this is an incident, or on its type."""
    L = r['L']
    if not L['ok']:
        return True
    return E.fam(L.get('c')) != E.fam(r.get('c')) and L.get('c') != 'none'


def finish(status, items):
    read_now = [r for r in items if (r.get('L') or {}).get('v') == VERSION]
    status.update(read=len(read_now), waiting=len(items) - len(read_now),
                  disputes=sum(1 for r in read_now if dispute(r)),
                  settled=sum(1 for r in read_now if 'X' in r), updated=E.iso(datetime.now(timezone.utc)))
    (DATA / 'llmstate.json').write_text(json.dumps(status, ensure_ascii=False, indent=1), 'utf-8')
    print('llm: %s' % json.dumps({k: status.get(k) for k in ('used', 'read', 'waiting', 'disputes', 'settled', 'note')}, ensure_ascii=False))
    return status
