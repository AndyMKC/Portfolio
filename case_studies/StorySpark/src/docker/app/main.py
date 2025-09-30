from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import threading

app = FastAPI(title="StorySpark Embedding Service")

class Texts(BaseModel):
    texts: List[str]

# Lazy-loaded model to keep startup fast
_model = None
_model_lock = threading.Lock()

def get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                # change this to a smaller/local model if you want lower memory/cpu
                _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

@app.post("/embed")
def embed(req: Texts):
    model = get_model()
    try:
        vectors = model.encode(req.texts, show_progress_bar=False, convert_to_numpy=True).tolist()
        return {"embeddings": vectors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthz")
def healthz():
    return {"status": "ok"}