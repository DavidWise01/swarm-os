import sqlite3, json, random

class Memory:
    def __init__(self, aid):
        self.id = aid
        self.mem = []
    def store(self, v, text, r):
        self.mem.append({"v":v,"t":text,"r":r})
        if len(self.mem)>256: self.mem.pop(0)
    def retrieve(self, q, k=6):
        if not self.mem: return []
        scored = [(sum((a-b)**2 for a,b in zip(q,m["v"])), m) for m in self.mem]
        scored.sort(key=lambda x:x[0])
        return [m for _,m in scored[:k]]

class Swarm:
    def __init__(self, db):
        self.db = db
        self.agents = [Memory(i) for i in range(100)]
        self.load()
    
    def load(self):
        try:
            conn = sqlite3.connect(self.db)
            for text, vec, res, aid in conn.execute("SELECT text,vector,result,agent_id FROM memories LIMIT 5000"):
                if aid<100: self.agents[aid].store(json.loads(vec), text, res)
        except: pass
    
    def encode(self, t):
        h=7
        for ch in t.lower(): h=((h*31)+ord(ch))&0x7fffffff
        return [int((h//(7**i))%3) for i in range(5)]
    
    def process(self, text, mode="recall"):
        v = self.encode(text)
        votes = []
        retrieved = []
        for a in self.agents:
            n = a.retrieve(v,3)
            retrieved.extend(n)
            votes.append(1 if sum(1 for x in n if x["r"]==1)>=2 else 0)
        
        consensus = sum(votes)/100
        
        # Store
        conn = sqlite3.connect(self.db)
        for aid in random.sample(range(100),20):
            conn.execute("INSERT INTO memories (text,vector,result,agent_id) VALUES (?,?,?,?)",
                        (text, json.dumps(v), 1 if consensus>0.5 else 0, aid))
        conn.commit()
        
        if mode=="socratic":
            # Switch sides - ask user
            q = f"You said '{text}'. What principle underlies this? How does it connect to what you know?"
            return {"answer":q, "mode":"socratic", "votes":f"{int(consensus*100)}/100"}
        
        if mode=="create":
            # Generate new
            base = v[:]
            for _ in range(5):
                imps = [random.choice(self.agents).retrieve(base,1)[0]["v"] if random.choice(self.agents).retrieve(base,1) else base for _ in range(10)]
                base = [max(set([x[i] for x in imps]), key=[x[i] for x in imps].count) for i in range(5)]
            words = [["chaos","order","coherence"],["leak","contain","preserve"],["fragment","link","integrate"],["static","shift","pulse"],["solo","pair","swarm"]]
            concept = " ".join(words[i][base[i]] for i in range(3))
            return {"answer":f"Novel: {concept}", "vector":base, "votes":f"{int(consensus*100)}/100", "mode":"create"}
        
        # Recall
        conn = sqlite3.connect(self.db)
        facts = conn.execute("SELECT subject,predicate,object FROM knowledge WHERE subject LIKE ? OR object LIKE ? LIMIT 3",
                           (f"%{text}%", f"%{text}%")).fetchall()
        if facts:
            ans = f"{facts[0][0]} {facts[0][1]} {facts[0][2]}."
        elif retrieved:
            ans = f"From memory: {retrieved[0]['t']}"
        else:
            ans = "I don't know this. Teach me: /learn subject predicate object"
        
        return {"answer":ans, "votes":f"{int(consensus*100)}/100", "mode":"recall", "consensus":consensus}
