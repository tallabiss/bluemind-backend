from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Importez votre router API
from app.api.endpoints import router

app = FastAPI()

# IMPORTANT : On définit les routes API d'abord
app.include_router(router, prefix="/v1")

# Servir les fichiers statiques (CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Route PRIORITAIRE pour l'interface graphique
@app.get("/")
async def read_index():
    # Vérifie que le fichier existe pour éviter une erreur 500
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html not found in static folder"}
    @app.get("/admin", include_in_schema=False)
async def read_admin():
    return FileResponse('static/admin.html')
