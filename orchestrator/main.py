# main.py
from fastapi import FastAPI
from .router import router

app = FastAPI(title="AI Orchestrator")
app.include_router(router, prefix="/orchestrate")

@app.get("/")
def root():
    return {"status": "orchestrator running"}
