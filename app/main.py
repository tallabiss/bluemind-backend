from fastapi import FastAPI, Body, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import zhipuai
from app.prompts import PromptManager

app = FastAPI(title="Bluemind.ai Forge")

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialisation des services
# Note: Assurez-vous que ZHIPU_API_KEY est définie dans vos variables d'environnement
client = zhipuai.ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
prompt_manager = PromptManager()

# --- ROUTES DE NAVIGATION ---

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/admin")
async def read_admin():
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))

# --- API DE GESTION DES PROMPTS ---

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

# --- API DE CHAT (L'INTELLIGENCE FUSIONNÉE) ---

@app.post("/v1/chat/ask")
async def ask_ai(payload: dict = Body(...)):
    vertical = payload.get("vertical", "world_search")
    query = payload.get("query", "")
    
    # 1. Chargement des deux couches de prompt depuis la Forge
    agent_prompt = prompt_manager.get_prompt(vertical)
    search_protocol = prompt_manager.get_prompt("world_search")
    
    # 2. Fusion : Expertise métier + Protocole de citation global
    full_system_prompt = f"{agent_prompt}\n\n{search_protocol}"
    
    try:
        # 3. Appel à l'IA avec le prompt fusionné
        response = client.chat.completions.create(
            model="glm-4", # Modèle haute performance de ZhipuAI
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            top_p=0.9
        )
        
        return {
            "status": "ready",
            "answer": response.choices[0].message.content,
            "vertical_used": vertical
        }
    except Exception as e:
        print(f"Erreur API: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'appel à l'IA")

# --- API DE DIAGNOSTIC ---

@app.post("/v1/admin/diagnostic")
async def diagnostic(payload: dict = Body(...)):
    prompt_content = payload.get("system_prompt", "")
    issues = []
    score = 100
    if "<antml:cite" not in prompt_content:
        score -= 60
        issues.append("Absence de balises <antml:cite>.")
    if "<behavior_guidelines>" not in prompt_content:
        score -= 20
        issues.append("Structure <behavior_guidelines> manquante.")
    
    return {"status": "passed" if score > 70 else "failed", "score": max(score, 0), "issues": issues}
