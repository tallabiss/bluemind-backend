from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import zhipuai
import os
from app.core.compliance import ComplianceEngine

app = FastAPI(title="Bluemind.ai Forge")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialisation
client = zhipuai.ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
compliance = ComplianceEngine()

class ChatRequest(BaseModel):
    query: str
    system_prompt: str

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.post("/v1/chat")
async def chat_endpoint(request: ChatRequest):
    # 1. Sécurisation du prompt système (Hard-Lock)
    secured_prompt = compliance.force_xml_structure(request.system_prompt)
    
    # 2. Appel à GLM-4.5 (ou version actuelle)
    response = client.chat.completions.create(
        model="glm-4", # Remplace par glm-4.5 dès dispo
        messages=[
            {"role": "system", "content": secured_prompt},
            {"role": "user", "content": request.query}
        ],
        temperature=0.1 # Rigueur maximale
    )
    
    answer = response.choices[0].message.content
    
    # 3. Scoring de conformité au runtime
    report = compliance.verify_response(answer)
    
    return {
        "answer": answer,
        "compliance": report
    }

@app.post("/v1/enterprise/ingest")
async def ingest_data(file: UploadFile = File(...), vertical: str = Form(...)):
    # Simulation de l'ingestion JEPA
    # Ici tu ajouterais ton code de Vectorisation (Qdrant/Pinecone)
    return {"status": "success", "memory_size": "1,240 vecteurs", "vertical": vertical}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
