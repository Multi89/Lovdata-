import os
import re
import sqlite3
from pathlib import Path

def db_path():
    return Path(os.getenv("LOVDATA_DB_PATH", "data/lovdata.sqlite3"))

def connect():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE IF NOT EXISTS documents (doc_id TEXT PRIMARY KEY, title TEXT NOT NULL, text TEXT NOT NULL, source TEXT NOT NULL)")
    return con

def status():
    with connect() as con:
        count = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    return {"status": "ok", "indexed_documents": count, "pro_configured": bool(os.getenv("LOVDATA_PRO_GATEWAY_URL") and os.getenv("LOVDATA_PRO_GATEWAY_TOKEN")), "warning": "Indeksen kan være utdatert. Kontroller alltid originalkilden."}

def search(query, limit=10):
    if not query.strip(): return []
    tokens = re.findall(r"\w+", query.lower())[:8]
    if not tokens: return []
    with connect() as con:
        rows = con.execute("SELECT doc_id,title,text,source FROM documents WHERE " + " OR ".join(["lower(title || ' ' || text) LIKE ?"]*len(tokens)) + " LIMIT ?", [f"%{t}%" for t in tokens]+[min(max(limit,1),50)]).fetchall()
    return [dict(doc_id=r['doc_id'],title=r['title'],source=r['source'],url='https://lovdata.no/dokument/' + r['doc_id'].lstrip('/'),excerpt=r['text'][:550]) for r in rows]

def fetch(doc_id):
    with connect() as con:
        row = con.execute('SELECT * FROM documents WHERE doc_id=?',(doc_id,)).fetchone()
    if not row: return None
    return {**dict(row), 'url':'https://lovdata.no/dokument/' + doc_id.lstrip('/'), 'truncated':False}

def find_in_document(doc_id, phrase):
    doc=fetch(doc_id)
    if not doc or not phrase.strip(): return []
    hits=[]
    for m in list(re.finditer(re.escape(phrase),doc['text'],re.I))[:30]:
        hits.append({'offset':m.start(),'context':doc['text'][max(0,m.start()-120):m.end()+120]})
    return hits
