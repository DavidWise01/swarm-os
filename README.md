# Swarm OS — Full Stack

**Author:** David Wise (ROOT0)  
**License:** MIT  

100-agent swarm intelligence system. Knowledge persistence, recursive memory retrieval, three operational modes. No ML dependencies — pure Python hash encoding.

---

## What this is

A self-contained AI reasoning engine built around a swarm of 100 agents. Each agent holds a 256-slot memory. When you ask a question, all 100 agents vote based on what they remember. Consensus drives the answer.

Three modes:

| Mode | Behaviour |
|------|-----------|
| **RECALL** | Retrieve from memory + knowledge base. What do the agents already know? |
| **CREATE** | Generate novel concepts by consensus vote across random agent samples. |
| **SOCRATIC** | The swarm asks *you* a question instead. Role reversal. |

---

## Architecture

```
frontend/index.html        Browser UI — chat, mode selector, 10×10 agent lattice
backend/main.py            FastAPI server — /ask, /learn, /state
engine/swarm.py            Swarm engine — 100 Memory agents, FNV hash encoding, voting
backend/swarm.db           SQLite — knowledge + memories + conversations (auto-created)
```

### Encoding

No embeddings. No model calls. Text is encoded by a rolling FNV hash into a 5-dimensional ternary vector (values 0, 1, 2). Similarity is L2 distance in that space.

```python
def encode(text):
    h = 7
    for ch in text.lower():
        h = ((h * 31) + ord(ch)) & 0x7fffffff
    return [int((h // (7**i)) % 3) for i in range(5)]
```

### Memory

Each agent stores up to 256 entries. `retrieve(query, k=6)` returns the k nearest by L2. On each `/ask`, 20 randomly sampled agents write the new entry to persist it across sessions.

### Knowledge base

Teach the swarm explicit facts:

```
POST /learn?s=sun&p=is&o=star
```

Stored as subject/predicate/object triples. Retrieved by LIKE match on RECALL queries.

---

## Quick start

```bash
pip install -r requirements.txt
cd backend
uvicorn main:app --reload
```

Open `frontend/index.html` in your browser. Type a question and hit Enter.

### API

```
POST /ask         { "question": "...", "mode": "recall|create|socratic" }
POST /learn       ?s=subject&p=predicate&o=object
GET  /state       { agents: 100, memories: N, knowledge: N }
```

---

## Timing loop

```
ask → answer → listen → answer → ask → repeat
```

SOCRATIC mode closes the loop: the swarm asks back, you teach it, it integrates.

---

## Files

```
backend/main.py        FastAPI app, SQLite init, /ask /learn /state routes
engine/swarm.py        Memory class (256-slot ring), Swarm class (100 agents), encode()
engine/__init__.py     Package init
frontend/index.html    Dark-mode UI: chat panel, agent lattice, mode buttons
requirements.txt       fastapi, uvicorn
```
