from fastapi import FastAPI, Body, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import zhipuai
from app.core.compliance import ComplianceEngine
from app.prompts import PromptManager

app = FastAPI(title="Bluemind.ai Forge")

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialisation
client = zhipuai.ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
compliance = ComplianceEngine()
prompt_manager = PromptManager()

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/admin")
async def read_admin():
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))

@app.get("/v1/admin/prompts/{vertical}")
async def get_prompt(vertical: str):
    return {"content": prompt_manager.get_prompt(vertical)}

@app.post("/v1/admin/prompts/update")
async def update_prompt(payload: dict = Body(...)):
    prompt_manager.update_prompt(payload['vertical'], payload['content'])
    return {"status": "success"}

@app.post("/v1/admin/diagnostic")
async def diagnostic(payload: dict = Body(...)):
    # Test de conformité (simulation de réponse)
    test_text = "La 5G est active. <antml:cite index='1'>Source</antml:cite>"
    report = compliance.verify_response(test_text)
    return {"status": "passed" if report["score"] > 80 else "failed", "score": report["score"], "issues": report["issues"]}

@app.post("/v1/enterprise/ingest")
async def ingest_data(file: UploadFile = File(...), vertical: str = Form(...)):
    return {"status": "success", "memory_size": "1,240", "vertical": vertical}
