from fastapi import FastAPI, Body, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import zhipuai
from app.prompts import PromptManager

app = FastAPI(title="Bluemind.ai Forge")

# 1. Configuration CORS pour autoriser les requêtes du navigateur
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialisation de l'IA
ZHIPU_KEY = os.getenv("ZHIPU_API_KEY")
client = zhipuai.ZhipuAI(api_key=ZHIPU_KEY)
prompt_manager = PromptManager()

# --- ROUTES DE NAVIGATION ---

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/admin")
async def read_admin():
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))

# --- API DE GESTION DES PROMPTS (FORGE) ---

@app.get("/v1/admin/prompts/{vertical}")
async def get_prompt(vertical: str):
    content = prompt_manager.get_prompt(vertical)
    return {"vertical": vertical, "content": content}

@app.post("/v1/admin/prompts/update")
async def update_prompt(payload: dict = Body(...)):
    vertical = payload.get("vertical")
    content = payload.get("content")
    if not vertical or content is None:
        raise HTTPException(status_code=400, detail="Données manquantes")
    prompt_manager.update_prompt(vertical, content)
    return {"status": "success"}

# --- API DE CHAT (COCKPIT) ---

@app.post("/v1/chat/ask")
async def ask_ai(payload: dict = Body(...)):
    vertical = payload.get("vertical", "world_search")
    query = payload.get("query", "")
    
    if not query:
        raise HTTPException(status_code=400, detail="La question est vide")

    # 1. Chargement et fusion des instructions de la Forge
    agent_instr = prompt_manager.get_prompt(vertical)
    search_instr = prompt_manager.get_prompt("world_search")
    full_prompt = f"{agent_instr}\n\n{search_instr}"
    
    # 2. Vérification de la clé API
    if not ZHIPU_KEY or "votre" in ZHIPU_KEY:
        return {
            "status": "ready", 
            "answer": "⚠️ Mode Démo : La clé ZHIPU_API_KEY n'est pas configurée dans les variables d'environnement."
        }

    try:
        # 3. Appel API avec le modèle GLM-4-FLASH (Plus stable et rapide)
        response = client.chat.completions.create(
            model="glm-4-flash", 
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            top_p=0.9
        )
        
        # Extraction de la réponse
        answer = response.choices[0].message.content
        return {"status": "ready", "answer": answer}

    except Exception as e:
        # Renvoie l'erreur précise pour le débug
        error_msg = str(e)
        print(f"Erreur API Zhipu: {error_msg}")
        return {
            "status": "error", 
            "answer": f"Erreur IA ({type(e).__name__}) : {error_msg}"
        }

# --- API DE DIAGNOSTIC ---

@app.post("/v1/admin/diagnostic")
async def diagnostic(payload: dict = Body(...)):
    prompt_content = payload.get("system_prompt", "")
    score = 100
    issues = []
    if "<antml:cite" not in prompt_content:
        score -= 60
        issues.append("Absence de protocole de citation <antml:cite>.")
    
    return {
        "status": "passed" if score > 70 else "failed",
        "score": max(score, 0),
        "issues": issues
    }
