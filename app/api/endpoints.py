from fastapi import APIRouter
from pydantic import BaseModel
from app.core.world_model import WorldModel
from app.core.encoders import MultiModalEncoder

router = APIRouter()
wm = WorldModel()
encoder = MultiModalEncoder()

class Query(BaseModel):
    input: str
    context: str = "default"

@router.post("/search")
async def world_search(query: Query):
    latent = await encoder.encode(query.input)
    return {"latent_id": hash(latent.tobytes()), "status": "simulated"}

@router.post("/enterprise/simulate")
async def simulate(query: Query):
    latent = await encoder.encode(query.input)
    res = await wm.predict_and_verify(latent, "analyze")
    return {"uncertainty": res["uncertainty"], "recommendation": "neutral"}