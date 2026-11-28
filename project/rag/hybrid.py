"""Fuse BM25 word ranking and cosine similarity over multilingual crop concepts."""
from collections import Counter
from functools import lru_cache
import hashlib
from math import log, sqrt
from pathlib import Path
import re
import sqlite3

INDEX = Path(__file__).resolve().parents[1] / "data/manuals/pages.sqlite"
CONCEPTS = [
    ("brown spot","brown spots","brown lesions","oval spots","பழுப்பு","දුඹුරු"),
    ("sheath rot","sheath discoloration","enclosed panicle","உறை அழுகல்","කොපු කුණුවීම"),
    ("fertilizer","fertiliser","urea","nutrient","nitrogen","உரம்","පොහොර"),
    ("rainfed","rain-fed","மானாவாரி","වර්ෂාපෝෂිත"),
    ("irrigated","irrigation","பாசன","වාරි"),
]
# Short paraphrases of official publications, retained with section attribution.
CARDS = [
    ("RRDI · Brown Spot", "Symptoms", "Brown spots with a dark rim and a lighter centre can occur on rice leaves. Examine the shape and the affected plant part; a spot alone is insufficient for a diagnosis.", "https://doa.gov.lk/rrdi_ricediseases_brownspot/"),
    ("RRDI · Sheath Rot", "Symptoms", "Sheath rot can affect the uppermost sheath around the young panicle. Check whether the panicle has emerged fully and which part of the plant is discoloured.", "https://doa.gov.lk/rrdi_ricediseases_sheathrot/"),
    ("RRDI · Fertilizer recommendations", "Growing conditions", "Select the fertilizer schedule for the growing zone, variety duration and water supply. RRDI lists different tables for irrigated and rainfed paddy.", "https://doa.gov.lk/rrdi_fertilizerrecomendation/"),
]
def words(text):
    return re.findall(r"[^\W_]+", text.casefold())

def concepts(text):
    text = text.casefold()
    return [int(any(term in text for term in group)) for group in CONCEPTS]

def corpus():
    docs = list(CARDS)
    if INDEX.is_file():
        with sqlite3.connect(INDEX.as_uri()+"?mode=ro", uri=True) as db:
            for title,page,body in db.execute("SELECT title,page,body FROM pages"):
                # The Sinhala RRDI PDF uses a legacy font. Quarantine pages until Unicode OCR is checked.
                if title=="Fertilizer recommendation for paddy cultivation" and sum(0xD80<=ord(c)<=0xDFF for c in body)<40:
                    continue
                body=" ".join(body.split())
                docs.extend((title,f"Page {page}",body[i:i+900],"") for i in range(0,len(body),800) if len(body[i:i+900])>50)
    return docs

def collection_name(docs):
    return "paddy-"+hashlib.sha256(repr(docs).encode()).hexdigest()[:16]

@lru_cache(maxsize=1)
def collection(name):
    import chromadb
    from chromadb.config import Settings
    client=chromadb.PersistentClient(path=str(INDEX.parent/"chroma"),settings=Settings(anonymized_telemetry=False))
    return client.get_collection(name)

def build_dense():
    import chromadb
    from chromadb.config import Settings
    docs=corpus()
    client=chromadb.PersistentClient(path=str(INDEX.parent/"chroma"),settings=Settings(anonymized_telemetry=False))
    name=collection_name(docs)
    coll=client.get_or_create_collection(name,metadata={"hnsw:space":"cosine"})
    coll.upsert(ids=[str(i) for i in range(len(docs))],documents=[title+" "+section+" "+body for title,section,body,_ in docs])
    (INDEX.parent/"dense-index.txt").write_text(name)
    print(f"Indexed {len(docs)} passages in ChromaDB")

def search(query):
    docs=corpus()
    bags = [Counter(words(title+" "+body)) for title,_,body,_ in docs]
    avg = sum(map(lambda bag:sum(bag.values()),bags))/len(bags)
    df = Counter(word for bag in bags for word in bag)
    q = set(words(query))-set("i my can the should what of in to on and is a do how rice paddy field".split())
    vector = concepts(query)
    lexical, semantic = [], []
    for i, ((title,_,body,_),bag) in enumerate(zip(docs,bags)):
        score = sum(log(1+(len(docs)-df[t]+.5)/(df[t]+.5))*bag[t]*2.2/
                    (bag[t]+1.2*(.25+.75*sum(bag.values())/avg)) for t in q if bag[t])
        if score: lexical.append((score,i))
        v = concepts(title+" "+body)
        cosine = sum(a*b for a,b in zip(vector,v))/sqrt(max(1,sum(vector)*sum(v)))
        if cosine: semantic.append((cosine+sum(a*b for a,b in zip(vector,concepts(title))),i))
    fused = Counter()
    rankings=[lexical,semantic]
    marker=INDEX.parent/"dense-index.txt"
    name=collection_name(docs)
    if marker.exists() and marker.read_text()==name and (lexical or semantic or len(q)>=2):
        expanded=query+" "+" ".join(group[0] for group,present in zip(CONCEPTS,vector) if present)
        hits=collection(name).query(query_texts=[expanded],n_results=min(8,len(docs)),include=["distances"])
        rankings.append([(1-dist,int(i)) for i,dist in zip(hits["ids"][0],hits["distances"][0]) if dist<0.65])
    for scores in rankings:
        for rank,(_,i) in enumerate(sorted(scores,reverse=True)[:8],1):
            fused[i] += 1/(60+rank)
    return [dict(title=docs[i][0],section=docs[i][1],passage=docs[i][2],url=docs[i][3]) for i,_ in fused.most_common(3)]


if __name__=="__main__":
    build_dense()
