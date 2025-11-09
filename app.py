from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from rag_agent import rag_query

app = FastAPI()

# --- Enable CORS for Firebase (important) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify your Firebase domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/query")
async def query_endpoint(request: Request):
    data = await request.json()
    user_query = data.get("query", "")

    if not user_query:
        return {"error": "Missing query"}

    answer, sources = rag_query(user_query)
    return {
        "query": user_query,
        "answer": answer,
        "sources": sources
    }

@app.get("/")
async def root():
    return {"message": "IGDTUW RAG API is running!"}
