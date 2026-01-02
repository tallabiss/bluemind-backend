from fastapi import FastAPI, Body, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import zhipuai
from app.prompts import PromptManager

app = FastAPI(title="Bluemind.ai Forge")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialisation
ZHIPU_KEY = os.getenv("ZHIPU_API_KEY")
client = zhipuai.ZhipuAI(api_key=ZHIPU_KEY)
prompt_manager = PromptManager()

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/admin")
async def read_admin():
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))

@app.post("/v1/chat/ask")
async def ask_ai(payload: dict = Body(...)):
    vertical = payload.get("vertical", "world_search")
    query = payload.get("query", "")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query empty")

    # 1. Fusion des prompts
    agent_instr = prompt_manager.get_prompt(vertical)
    search_instr = prompt_manager.get_prompt("world_search")
    full_prompt = f"{agent_instr}\n\n{search_instr}"
    
    if not ZHIPU_KEY:
        return {"status": "ready", "answer": "⚠️ Clé API manquante dans Render."}

    # Liste des modèles à essayer par ordre de probabilité
    models_to_try = ["glm-4-flash", "glm-4", "glm-4-0520"]
    last_error = ""

    for model_name in models_to_try:
        try:
            # 2. Appel API
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7
            )
            # Si ça marche, on renvoie la réponse immédiatement
            return {"status": "ready", "answer": response.choices[0].message.content}
        
        except Exception as e:
            last_error = str(e)
            if "1211" in last_error:
                print(f"Modèle {model_name} non trouvé, essai du suivant...")
                continue # On passe au modèle suivant
            else:
                break # Autre erreur (crédits, clé), on s'arrête

    return {"status": "error", "answer": f"L'IA n'a pas pu répondre. Erreur technique : {last_error}"}

# --- GESTION ADMIN ---
@app.get("/v1/admin/prompts/{vertical}")
async def get_prompt(vertical: str):
    return {"vertical": vertical, "content": prompt_manager.get_prompt(vertical)}

@app.post("/v1/admin/prompts/update")
async def update_prompt(payload: dict = Body(...)):
    prompt_manager.update_prompt(payload.get("vertical"), payload.get("content"))
    return {"status": "success"}
