"""Engine-test only: the pacing numbers a live run sees now (one free model-list call, no AI requests)."""
import json
import sys
sys.path.insert(0, 'collector')
import llm
S = llm.Session()
st = S.state
print('day', st.get('day'), 'hours_to_reset', round(llm.hours_to_reset(), 2))
print('models', S.models)
for m in S.models.get('readers', []):
    print(' ', m, 'limit', S.limit(m, 'readers'), 'used', st['used'].get(m, 0), 'rested', st['rested'].get(m), 'has', S.has(m, 'readers'))
print('caps', st.get('caps'))
print('pace readers', S.pace('readers'), 'pace experts', S.pace('experts'), 'waiting', st.get('waiting'))
C = llm.CFG
print('keep', min(C['per_run']['judges'], -(-st.get('waiting', 0) // C['pair_batch']), S.pace('readers') // 2))
items = [json.loads(l.rstrip(',\n')) for l in open('data/incidents.json', encoding='utf-8') if l.startswith('{')]
un = [r for r in items if not r.get('L')]
print('unread', len(un), 'Lx>=3', sum(1 for r in un if r.get('Lx', 0) >= 3))
for r in sorted(un, key=lambda r: r['d'], reverse=True)[:12]:
    print('  ', r['d'][:16], r.get('Lx'), r['t'][:70])
