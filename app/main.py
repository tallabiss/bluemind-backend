from fastapi import FastAPI, Body, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from groq import Groq
from app.prompts import PromptManager

app = FastAPI(title="Bluemind.ai Forge & Cockpit")

# 1. Activation du CORS (Indispensable pour que le JS puisse parler à l'API)
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

# Initialisation du client Groq
# Assurez-vous d'avoir GROQ_API_KEY dans votre environnement Render
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
prompt_manager = PromptManager()

# --- ROUTES DE NAVIGATION ---

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/admin")
async def read_admin():
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))

# --- ROUTES ADMIN (LA FORGE) ---

@app.get("/v1/admin/prompts/{vertical}")
async def get_prompt(vertical: str):
    content = prompt_manager.get_prompt(vertical)
    return {"vertical": vertical, "content": content}

@app.post("/v1/admin/prompts/update")
async def update_prompt(payload: dict = Body(...)):
    vertical = payload.get("vertical")
    content = payload.get("content")
    if not vertical or content is None:
        raise HTTPException(status_code=400, detail="Données incomplètes")
    prompt_manager.update_prompt(vertical, content)
    return {"status": "success"}

@app.post("/v1/admin/diagnostic")
async def run_diagnostic(payload: dict = Body(...)):
    prompt_content = payload.get("system_prompt", "")
    # Logique de test : présence des balises de citation
    score = 100
    if "<antml:cite" not in prompt_content:
        score = 40
    return {
        "status": "passed" if score > 70 else "failed",
        "score": score
    }

# --- ROUTE CHAT (LE COCKPIT) ---

@app.post("/v1/chat/ask")
async def ask_ai(payload: dict = Body(...)):
    query = payload.get("query", "")
    vertical = payload.get("vertical", "world_search")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query empty")

    # Récupération et fusion des instructions
    agent_instr = prompt_manager.get_prompt(vertical)
    search_instr = prompt_manager.get_prompt("world_search")
    system_prompt = f"{agent_instr}\n\n{search_instr}"

    try:
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
        print(f"Erreur Groq: {str(e)}")
        return {"status": "error", "answer": f"L'IA est momentanément indisponible : {str(e)}"}
