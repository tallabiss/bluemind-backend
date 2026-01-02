from fastapi import FastAPI, Body, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import zhipuai
from app.prompts import PromptManager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Client Zhipu
client = zhipuai.ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
prompt_manager = PromptManager()

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.post("/v1/chat/ask")
async def ask_ai(payload: dict = Body(...)):
    query = payload.get("query", "")
    vertical = payload.get("vertical", "world_search")
    
    # Fusion des instructions
    system_prompt = f"{prompt_manager.get_prompt(vertical)}\n\n{prompt_manager.get_prompt('world_search')}"

    try:
        # TEST CRUCIAL : On force 'glm-4-flash' qui est le modèle gratuit universel
        response = client.chat.completions.create(
            model="glm-4-flash", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            stream=False
        )
        return {"status": "ready", "answer": response.choices[0].message.content}
    except Exception as e:
        # On affiche l'erreur réelle dans le terminal pour débugger
        print(f"DEBUG ERROR: {str(e)}")
        return {"status": "error", "answer": f"L'API refuse l'accès : {str(e)}"}
