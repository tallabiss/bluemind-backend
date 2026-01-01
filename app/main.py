from fastapi import FastAPI, Body, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import zhipuai
from app.prompts import PromptManager

try:
    from app.core.compliance import ComplianceEngine
    compliance = ComplianceEngine()
except ImportError:
    compliance = None

app = FastAPI(title="Bluemind.ai Forge")

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialisation
client = zhipuai.ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
prompt_manager = PromptManager()

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

# --- LOGIQUE DE CHAT (EXEMPLE DE FUSION) ---

@app.post("/v1/chat/ask")
async def ask_ai(vertical: str = Body(...), query: str = Body(...)):
    # Récupération du prompt métier (ex: telco)
    agent_prompt = prompt_manager.get_prompt(vertical)
    # Récupération du protocole global de recherche
    search_protocol = prompt_manager.get_prompt("world_search")
    
    # Fusion des deux couches pour un verrouillage sémantique total
    full_system_prompt = f"{agent_prompt}\n\n{search_protocol}"
    
    # Appel à l'IA (ZhipuAI)
    # response = client.chat.completions.create(...)
    return {"status": "ready", "system_prompt_used": full_system_prompt}

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
    
    return {
        "status": "passed" if score > 70 else "failed",
        "score": max(score, 0),
        "issues": issues
    }

@app.post("/v1/enterprise/ingest")
async def ingest_data(file: UploadFile = File(...), vertical: str = Form(...)):
    return {"status": "success", "filename": file.filename, "vertical": vertical}
