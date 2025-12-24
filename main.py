from fastapi import FastAPI, HTTPException
from neo4j import GraphDatabase

app = FastAPI()

# 🔐 Credentials Neo4j Aura (en dur pour l’instant)
NEO4J_URI = "neo4j+s://d20e068a.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "eVU2YQ9HTVpgfIbCNmBZoFDup3KxZGphq0Yd2GyZ5qQ"

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

def run_query(query: str, parameters: dict | None = None):
    try:
        with driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"status": "API is running"}

@app.get("/people")
def get_people():
    query = """
    MATCH (p:Person)
    RETURN p.name AS name
    ORDER BY name
    """
    return run_query(query)

@app.get("/knows")
def get_knows():
    query = """
    MATCH (a:Person)-[:KNOWS]->(b:Person)
    RETURN a.name AS source, b.name AS target
    """
    return run_query(query)
