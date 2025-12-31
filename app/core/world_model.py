import numpy as np
from app.core.memory import EpisodicMemory

class WorldModel:
    def __init__(self, latent_dim: int = 512):
        self.latent_dim = latent_dim
        self.memory = EpisodicMemory(latent_dim)

    async def predict_next_state(self, current_latent: np.ndarray, action: str):
        noise = np.random.normal(0, 0.01, self.latent_dim)
        return current_latent + noise

    async def predict_and_verify(self, current_latent: np.ndarray, action: str):
        predicted = await self.predict_next_state(current_latent, action)
        past = await self.memory.retrieve_similar(current_latent)
        uncertainty = 1.0
        if past:
            dist = np.linalg.norm(predicted - past[0]["outcome"])
            uncertainty = float(dist / np.linalg.norm(predicted))
        return {"predicted_state": predicted, "uncertainty": uncertainty}