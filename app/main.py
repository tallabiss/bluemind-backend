from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Import du router de votre API
from app.api.endpoints import router

app = FastAPI(title="Bluemind.ai Engine")

# 1. Montage des fichiers statiques (CSS, JS, Images)
# Vérifiez que le dossier 'static' existe bien à la racine
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Inclusion des routes de l'API
app.include_router(router, prefix="/v1")

# 3. Route pour l'interface UTILISATEUR (Cockpit)
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

# 4. Route pour l'interface ADMIN (Forge)
@app.get("/admin")
async def read_admin():
    return FileResponse('static/admin.html')
