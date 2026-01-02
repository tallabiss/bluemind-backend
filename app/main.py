from fastapi import FastAPI, Body, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import zhipuai
from app.prompts import PromptManager

app = FastAPI(title="Bluemind.ai Forge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/v1/chat/ask")
async def ask_ai(payload: dict = Body(...)):
    vertical = payload.get("vertical", "world_search")
    query = payload.get("query", "")
    
    # Fusion des prompts de la Forge
    agent_instr = prompt_manager.get_prompt(vertical)
    search_instr = prompt_manager.get_prompt("world_search")
    full_prompt = f"{agent_instr}\n\n{search_instr}"
    
    try:
        # Utilisation de GLM-4-Flash (Le modèle avec le plus gros quota gratuit)
        response = client.chat.completions.create(
            model="glm-4-flash", 
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": query}
            ]
        )
        return {"status": "ready", "answer": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "answer": f"Erreur : {str(e)}"}

# Routes Admin Simplifiées
@app.get("/v1/admin/prompts/{vertical}")
async def get_prompt(vertical: str):
    return {"content": prompt_manager.get_prompt(vertical)}

@app.post("/v1/admin/prompts/update")
async def update_prompt(payload: dict = Body(...)):
    prompt_manager.update_prompt(payload.get("vertical"), payload.get("content"))
    return {"status": "success"}
