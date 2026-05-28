from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3, json, os
from datetime import datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB = "swarm.db"

def init():
    c = sqlite3.connect(DB).cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS knowledge (
        id INTEGER PRIMARY KEY, subject TEXT, predicate TEXT, object TEXT,
        confidence REAL, source TEXT, vector TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY, text TEXT, vector TEXT, result INTEGER,
        agent_id INTEGER, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY, role TEXT, content TEXT, vector TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    sqlite3.connect(DB).commit()

init()

class Ask(BaseModel):
    question: str
    mode: str = "recall"

def encode(t):
    h=7
    for ch in t.lower(): h=((h*31)+ord(ch))&0x7fffffff
    return [int((h//(7**i))%3) for i in range(5)]

@app.post("/ask")
def ask(a: Ask):
    from engine import Swarm
    s = Swarm(DB)
    return s.process(a.question, a.mode)

@app.post("/learn")
def learn(s: str, p: str, o: str):
    v = json.dumps(encode(f"{s} {p} {o}"))
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO knowledge (subject,predicate,object,vector,confidence,source) VALUES (?,?,?,?,?,?)",
                 (s,p,o,v,1.0,"user"))
    conn.commit()
    return {"ok": True}

@app.get("/state")
def state():
    conn = sqlite3.connect(DB)
    m = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    k = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
    return {"agents":100, "memories":m, "knowledge":k}
