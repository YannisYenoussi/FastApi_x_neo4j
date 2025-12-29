from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from pyvis.network import Network
import os
import tempfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Lire depuis les variables d’environnement (Render)
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise RuntimeError("Missing Neo4j env vars: NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_query(query: str, params=None):
    with driver.session() as session:
        result = session.run(query, params or {})
        return [r.data() for r in result]

@app.on_event("shutdown")
def shutdown_event():
    driver.close()

@app.get("/")
def root():
    return {"status": "API is running"}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/vis", response_class=HTMLResponse)
def vis_graph():
    try:
        query = """
        MATCH (a:Person)-[:KNOWS]->(b:Person)
        RETURN a.name AS source, b.name AS target
        LIMIT 50
        """
        rows = run_query(query)

        net = Network(
            height="750px",
            width="100%",
            bgcolor="#0b0b0b",
            font_color="white",
            directed=True
        )

        for row in rows:
            s = row.get("source")
            t = row.get("target")
            if not s or not t:
                continue
            net.add_node(s, label=s)
            net.add_node(t, label=t)
            net.add_edge(s, t)

        # ✅ Générer du HTML sans dépendre d’un fichier “fixe”
        with tempfile.NamedTemporaryFile(delete=True, suffix=".html") as f:
            net.save_graph(f.name)
            f.seek(0)
            html = f.read().decode("utf-8", errors="ignore")

        return HTMLResponse(content=html)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
