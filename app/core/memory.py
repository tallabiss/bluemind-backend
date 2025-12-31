import numpy as np
from typing import List, Dict
from datetime import datetime

class EpisodicMemory:
    def __init__(self, latent_dim: int = 512, capacity: int = 1000):
        self.capacity = capacity
        self.buffer: List[Dict] = []

    async def store(self, latent_state: np.ndarray, action: str, outcome: np.ndarray):
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
        self.buffer.append({
            "state": latent_state,
            "action": action,
            "outcome": outcome,
            "timestamp": datetime.utcnow()
        })

    async def retrieve_similar(self, current_latent: np.ndarray, top_k: int = 3):
        if not self.buffer: return []
        # Simulation de recherche par produit scalaire
        sims = [(np.dot(current_latent, m["state"]), m) for m in self.buffer]
        sims.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in sims[:top_k]]