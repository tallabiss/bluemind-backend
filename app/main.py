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

# Montage des fichiers statiques
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

# --- GESTION DES PROMPTS (FORGE) ---

@app.get("/v1/admin/prompts/{vertical}")
async def get_prompt(vertical: str):
    content = prompt_manager.get_prompt(vertical)
    return {"vertical": vertical, "content": content}

@app.post("/v1/admin/prompts/update")
async def update_prompt(payload: dict = Body(...)):
    vertical = payload.get("vertical")
    content = payload.get("content")
    prompt_manager.update_prompt(vertical, content)
    return {"status": "success"}

# --- LOGIQUE DE CHAT (COCKPIT) ---

@app.post("/v1/chat/ask")
async def ask_ai(payload: dict = Body(...)):
    vertical = payload.get("vertical", "world_search")
    query = payload.get("query", "")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query empty")

    # 1. Fusion des instructions
    agent_instr = prompt_manager.get_prompt(vertical)
    search_instr = prompt_manager.get_prompt("world_search")
    full_prompt = f"{agent_instr}\n\n{search_instr}"
    
    # 2. Vérification Clé API
    if not ZHIPU_KEY or "votre" in ZHIPU_KEY:
        return {"status": "ready", "answer": "⚠️ Mode Démo : Configurez ZHIPU_API_KEY pour activer l'IA."}

    try:
        # 3. Appel API
        response = client.chat.completions.create(
            model="glm-4",
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.7
        )
        return {"status": "ready", "answer": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "answer": f"Erreur IA : {str(e)}"}

# --- DIAGNOSTIC & INGESTION ---

@app.post("/v1/admin/diagnostic")
async def diagnostic(payload: dict = Body(...)):
    prompt_content = payload.get("system_prompt", "")
    score = 100
    issues = []
    if "<antml:cite" not in prompt_content: score -= 60; issues.append("Citations manquantes")
    return {"status": "passed" if score > 70 else "failed", "score": score, "issues": issues}

@app.post("/v1/enterprise/ingest")
async def ingest_data(file: UploadFile = File(...), vertical: str = Form(...)):
    return {"status": "success", "filename": file.filename}
