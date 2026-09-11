from fastapi import FastAPI

from .api import router
from .db import init_db

app=FastAPI(title="Event-Driven Integration Platform",version="0.1.0")
app.include_router(router)
@app.get("/health")
async def root_health(): return {"status":"ok","service":"event-driven-integration-platform"}
@app.on_event("startup")
async def startup(): await init_db()
