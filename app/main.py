from fastapi import FastAPI, Body, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from groq import Groq  # Importez la bibliothèque Groq
from app.prompts import PromptManager

app = FastAPI()

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialisation du client Groq (Remplace Zhipu)
# N'oubliez pas d'ajouter GROQ_API_KEY dans vos variables Render
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
prompt_manager = PromptManager()

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.post("/v1/chat/ask")
async def ask_ai(payload: dict = Body(...)):
    query = payload.get("query", "")
    vertical = payload.get("vertical", "world_search")
    
    # Récupération des prompts de votre Forge
    system_prompt = f"{prompt_manager.get_prompt(vertical)}\n\n{prompt_manager.get_prompt('world_search')}"

    try:
        # Appel à Groq (Modèle Llama 3.3 très performant)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        
        answer = chat_completion.choices[0].message.content
        return {"status": "ready", "answer": answer}
    
    except Exception as e:
        return {"status": "error", "answer": f"Erreur Groq : {str(e)}"}
