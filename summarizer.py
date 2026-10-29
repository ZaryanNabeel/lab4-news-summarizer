"""Lightweight extractive summarizer (word-frequency scoring). No model downloads needed."""
import re
from collections import Counter

STOPWORDS = set("""
a about above after again against all also am an and any are as at be because been before being below
between both but by can could did do does doing down during each few for from further had has have having
he her here hers herself him himself his how i if in into is it its itself just me more most my myself no
nor not now of off on once only or other our ours ourselves out over own same she should so some such than
that the their theirs them themselves then there these they this those through to too under until up very
was we were what when where which while who whom why will with would you your yours yourself yourselves
said says say one two new like may might must many much get got make made even still well way
""".split())


def split_sentences(text: str):
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"“'‘])", text)
    return [s.strip() for s in sentences if len(s.split()) >= 6]


def summarize(text: str, max_sentences: int = 4) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return text.strip()[:500]
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    words = [w for w in re.findall(r"[a-z']+", text.lower()) if w not in STOPWORDS and len(w) > 2]
    freq = Counter(words)
    if not freq:
        return " ".join(sentences[:max_sentences])
    top = max(freq.values())

    scores = []
    for idx, sent in enumerate(sentences):
        tokens = [w for w in re.findall(r"[a-z']+", sent.lower()) if w in freq]
        score = sum(freq[w] / top for w in tokens) / (len(tokens) ** 0.5 + 1)
        if idx < 3:  # news articles front-load the key facts
            score *= 1.25
        scores.append((score, idx))

    chosen = sorted(idx for _, idx in sorted(scores, reverse=True)[:max_sentences])
    return " ".join(sentences[i] for i in chosen)
