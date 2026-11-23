"""Per-agent opt-in class/skill profiles and provenance-aware adaptive memory.

This is a persistent MEMORY interface, not automatic weight fine-tuning or AGI.
User-controlled memory observations are never silently promoted into model weights.
"""
from __future__ import annotations
from datetime import datetime,timezone
from threading import RLock
import sqlite3
from hyper_registry import SKILLS,CLASSES

def validate_agent(a):
    if not isinstance(a,str) or len(a)!=8 or not a.startswith('AG-') or not a[3:].isdigit() or not 1<=int(a[3:])<=10000:
        raise ValueError('Unknown agent ID')

class AgentProfiles:
    def __init__(self,path):
        self.lock=RLock()
        self.db=sqlite3.connect(str(path),check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS agents(id TEXT PRIMARY KEY, class_id TEXT, updated TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS agent_skills(agent TEXT NOT NULL, skill TEXT NOT NULL, created TEXT NOT NULL, PRIMARY KEY(agent,skill))')
        self.db.execute('CREATE TABLE IF NOT EXISTS agent_memory(seq INTEGER PRIMARY KEY AUTOINCREMENT, agent TEXT NOT NULL, source TEXT NOT NULL, evidence TEXT NOT NULL, confidence REAL NOT NULL, created TEXT NOT NULL)')
        self.db.commit()
    def profile(self,agent):
        validate_agent(agent)
        with self.lock:
            row=self.db.execute('SELECT class_id FROM agents WHERE id=?',(agent,)).fetchone()
            skills=[s[0] for s in self.db.execute('SELECT skill FROM agent_skills WHERE agent=? ORDER BY skill',(agent,)).fetchall()]
            mem=self.db.execute('SELECT COUNT(*) FROM agent_memory WHERE agent=?',(agent,)).fetchone()[0]
        return {'agent':agent,'class':row[0] if row else None,'skills':skills,'memory_entries':mem,
            'weights':'see weight bank status; profiles do not imply training'}
    def choose(self,agent,class_id,skills):
        validate_agent(agent)
        if class_id is not None and class_id not in CLASSES:raise ValueError('Unknown class')
        if not isinstance(skills,list) or len(skills)>50 or len(set(skills))!=len(skills) or any(s not in SKILLS for s in skills):
            raise ValueError('Select at most 50 distinct skills from SK0001..SK1500')
        now=datetime.now(timezone.utc).isoformat()
        with self.lock:
            self.db.execute('INSERT OR REPLACE INTO agents(id,class_id,updated) VALUES(?,?,?)',(agent,class_id,now))
            self.db.execute('DELETE FROM agent_skills WHERE agent=?',(agent,))
            self.db.executemany('INSERT INTO agent_skills(agent,skill,created) VALUES(?,?,?)',[(agent,s,now) for s in skills]);self.db.commit()
        return self.profile(agent)
    def remember(self,agent,source,evidence,confidence):
        validate_agent(agent)
        if not isinstance(source,str) or not 1<=len(source)<=100:raise ValueError('Source must be 1..100 characters')
        if not isinstance(evidence,str) or not 1<=len(evidence)<=5000:raise ValueError('Evidence must be 1..5000 characters')
        if not isinstance(confidence,(float,int)) or isinstance(confidence,bool) or not 0<=confidence<=1:raise ValueError('Confidence must be 0..1')
        now=datetime.now(timezone.utc).isoformat()
        with self.lock:
            self.db.execute('INSERT INTO agent_memory(agent,source,evidence,confidence,created) VALUES(?,?,?,?,?)',(agent,source,evidence,float(confidence),now));self.db.commit()
        return {'stored':True,'agent':agent,'source':source,'weight_update':False,'certified_fact':False}
    def close(self):self.db.close()
