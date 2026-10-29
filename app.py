"""REST API: GET /get?keyword=... on port 7000."""
import threading

from flask import Flask, jsonify, request

from scraper import fetch_first_article
from summarizer import summarize

REGISTRATION = "FA23-BDS-039"
NEWS_SOURCE = "MIT Technology Review"

app = Flask(__name__)
browser_slots = threading.BoundedSemaphore(2)  # cap concurrent Chrome instances (RAM)


def payload(keyword, url="", summary=""):
    return {
        "registration": REGISTRATION,
        "newssource": NEWS_SOURCE,
        "keyword": keyword,
        "url": url,
        "summary": summary,
    }


@app.get("/")
def home():
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{REGISTRATION} | News Summarizer</title>
<style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:60px auto;padding:0 20px;line-height:1.6}}
code{{background:#eee;padding:2px 6px;border-radius:4px}}</style></head>
<body>
<h1>Registration Number: {REGISTRATION}</h1>
<p>News source: <strong>{NEWS_SOURCE}</strong></p>
<p>Usage: <code>/get?keyword=&lt;keyword&gt;</code></p>
<form action="/get" method="get"><input name="keyword" placeholder="e.g. quantum computing" required>
<button type="submit">Search</button></form>
</body></html>"""


@app.get("/get")
def get_summary():
    keyword = (request.args.get("keyword") or "").strip()
    if not keyword:
        body = payload("", summary="Missing required query parameter: keyword")
        return jsonify(body), 400

    with browser_slots:
        try:
            url, title, text = fetch_first_article(keyword)
        except Exception as e:  # always answer with the agreed schema
            body = payload(keyword, summary=f"Error: {e}")
            return jsonify(body), 502

    summary = summarize(text) if text else title
    return jsonify(payload(keyword, url, summary))


@app.get("/health")
def health():
    return jsonify({"status": "ok", "registration": REGISTRATION})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)
