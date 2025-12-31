from fastapi import FastAPI
from app.api.endpoints import router

app = FastAPI(
    title="Bluemind.ai Backend",
    description="World Model-based Intelligence System (JEPA Architecture)",
    version="0.1.0"
)

app.include_router(router, prefix="/v1")

@app.get("/")
async def health():
    return {"status": "operational", "engine": "JEPA-V1", "mode": "latent-inference"}