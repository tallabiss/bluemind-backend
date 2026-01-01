from fastapi import FastAPI, Body, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import zhipuai
from app.prompts import PromptManager

# Note: Assurez-vous que ComplianceEngine est bien défini dans app/core/compliance.py
# Si vous ne l'avez pas encore, une version simplifiée est intégrée dans la route diagnostic ci-dessous.
try:
    from app.core.compliance import ComplianceEngine
    compliance = ComplianceEngine()
except ImportError:
    compliance = None

app = FastAPI(title="Bluemind.ai Forge")

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Montage des fichiers statiques (JS, CSS, Images)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialisation des gestionnaires
# Note : Récupère la clé API depuis les variables d'environnement de Render
client = zhipuai.ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
prompt_manager = PromptManager()

# --- ROUTES DE NAVIGATION ---

@app.get("/")
async def read_index():
    """Sert la page d'accueil (Cockpit)."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/admin")
async def read_admin():
    """Sert l'interface d'administration (Forge)."""
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))

# --- API DE GESTION DES PROMPTS (VERTICALES) ---

@app.get("/v1/admin/prompts/{vertical}")
async def get_prompt(vertical: str):
    """Récupère le contenu d'un fichier .txt spécifique dans app/verticals/."""
    content = prompt_manager.get_prompt(vertical)
    return {"vertical": vertical, "content": content}

@app.post("/v1/admin/prompts/update")
async def update_prompt(payload: dict = Body(...)):
    """Écrase le contenu d'un fichier .txt avec les nouvelles directives."""
    vertical = payload.get("vertical")
    content = payload.get("content")
    
    if not vertical or content is None:
        raise HTTPException(status_code=400, detail="Données manquantes (vertical ou content)")
    
    success = prompt_manager.update_prompt(vertical, content)
    return {"status": "success" if success else "error"}

# --- API DE DIAGNOSTIC ET CONFORMITÉ ---

@app.post("/v1/admin/diagnostic")
async def diagnostic(payload: dict = Body(...)):
    """
    Analyse le prompt pour vérifier s'il respecte les règles de citation Bluemind.
    """
    prompt_content = payload.get("system_prompt", "")
    
    # Logique de diagnostic
    issues = []
    score = 100
    
    if "<antml:cite" not in prompt_content:
        score -= 60
        issues.append("Absence de balises <antml:cite>. Le système de citation est obligatoire.")
    
    if "<behavior_guidelines>" not in prompt_content:
        score -= 20
        issues.append("Structure XML manquante : <behavior_guidelines> non détecté.")

    # Si le moteur de compliance externe existe, on l'utilise pour affiner
    if compliance:
        # Simulation d'un test sur une réponse type
        report = compliance.verify_response("Test de citation <antml:cite index='1'>Source</antml:cite>")
        # On peut mixer les scores ici
    
    return {
        "status": "passed" if score > 70 else "failed",
        "score": max(score, 0),
        "issues": issues
    }

# --- API D'INGESTION DE DONNÉES ---

@app.post("/v1/enterprise/ingest")
async def ingest_data(file: UploadFile = File(...), vertical: str = Form(...)):
    """
    Simule l'ingestion d'un document dans la base vectorielle d'une verticale.
    """
    # Ici, vous ajouteriez la logique de lecture PDF/Text et l'envoi vers un Vector Store
    return {
        "status": "success", 
        "filename": file.filename,
        "memory_size": "1,240 v-points", 
        "vertical": vertical
    }
