"""Meaning fingerprints (optional: without these libraries the case builder compares by names and figures only).

One multilingual model (Marathi and English alike) turns each report's AI case label and summary into a vector; reports
whose vectors are close are candidates for the same case (cases.py), and the AI judge decides."""
import os

MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
_model = None


def embed(rows):
    """{report id: unit vector} for rows with 'id' and 't' (the text to compare), or None when the model is unavailable."""
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
        print('meaning fingerprints unavailable: %s' % str(e)[:120])
        return None
