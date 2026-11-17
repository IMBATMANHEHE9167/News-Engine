"""Machine reading (optional: without these libraries the engine works exactly as before).

Meaning-fingerprints of headlines from one multilingual model (Marathi and English alike), used to join reports that
tell the same story; and a second opinion on incident type, trained each run on the rule-judged reports. The second
opinion never changes a type: where it confidently disagrees with the rules, the report is flagged for checking."""
import os

MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
_model = None


def embed(rows):
    """{report id: unit vector} for rows with 'id' and 't' (headline), or None when the model is unavailable."""
    global _model
    try:
        import numpy as np
        from fastembed import TextEmbedding
        if _model is None:
            _model = TextEmbedding(MODEL, cache_dir=os.path.expanduser('~/.cache/fastembed'))
        out = {}
        for r, v in zip(rows, _model.embed([r['t'] for r in rows], batch_size=64)):
            v = np.asarray(v, dtype=float)
            out[r['id']] = (v / (np.linalg.norm(v) or 1.0)).tolist()
        return out
    except Exception as e:
        print('machine reading unavailable: %s' % str(e)[:120])
        return None


def second_opinion(rows, vec, min_conf=0.8):
    """Reports whose type a model trained on all the others confidently reads differently: {id: {...}}."""
    try:
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_predict
        rows = [r for r in rows if r['id'] in vec]
        y = np.array([r['c'] for r in rows])
        if len(rows) < 200 or min(np.unique(y, return_counts=True)[1]) < 5:
            return {}
        X = np.array([vec[r['id']] for r in rows])
        # Each report is judged by a model that never saw it (5-fold), so it cannot simply echo the rules back.
        P = cross_val_predict(LogisticRegression(max_iter=2000, C=4.0, class_weight='balanced'), X, y, cv=5, method='predict_proba')
        classes = sorted(set(y))
        out = {}
        for r, p in zip(rows, P):
            k = int(p.argmax())
            if classes[k] != r['c'] and p[k] >= min_conf:
                out[r['id']] = dict(id=r['id'], t=r['t'], u=r['u'], rule=r['c'], model=classes[k], conf=round(float(p[k]), 2))
        return out
    except Exception as e:
        print('second opinion unavailable: %s' % str(e)[:120])
        return {}
