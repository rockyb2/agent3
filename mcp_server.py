from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent_core import create_agent, chat_with_agent
from urllib.parse import quote

app = FastAPI()

# Configuration CORS pour permettre les requêtes depuis le frontend Vue.js
# En production, utilisez une variable d'environnement pour les origines autorisées
import os
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


agent = None

def get_agent():
    global agent
    if agent is None:
        print("⚙️ Initialisation de l'agent IA...")
        agent = create_agent()
    return agent

# Initialiser l'état de disponibilité de l'agent
agent_ready = False

@app.on_event("startup")
def startup_event():
    """Crée l'agent au démarrage de l'application et définit `agent_ready`."""
    global agent, agent_ready
    try:
        print("⚙️ Initialisation de l'agent IA lors du démarrage...")
        agent = create_agent()
        agent_ready = True
        print("✅ Agent initialisé avec succès")
    except Exception as e:
        agent = None
        agent_ready = False
        print(f"⚠️ Erreur lors de l'initialisation de l'agent: {e}")

# Endpoint racine pour vérifier que le serveur fonctionne
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Serveur MCP Agent IA fonctionnel",
        "agent_ready": agent_ready
    }

# Endpoint de santé pour la vérification de connexion
@app.get("/health")
def health():
    return {
        "status": "healthy" if agent_ready else "unhealthy",
        "agent_ready": agent_ready
    }

class MCPRequest(BaseModel):
    session_id: str
    message: str
    
class MCPResponse(BaseModel):
    answer: str


def _find_file_by_basename(basename: str):
    for root, dirs, files in os.walk(os.getcwd()):
        if basename in files:
            return os.path.join(root, basename)
    return None
    
@app.post("/mcp/chat")
def chat(req: MCPRequest):
    try:
        resp = chat_with_agent(req.session_id, req.message)
        response = {"answer": resp.get("content")}
        file_path = resp.get("file_path")
        if file_path:
            basename = os.path.basename(file_path)
            found = _find_file_by_basename(basename)
            if found:
                # renvoyer une URL relative que le frontend peut concaténer avec le host
                response["file_url"] = f"/mcp/download/{quote(basename)}"
                response["file_name"] = basename
            else:
                # si le fichier n'a pas été trouvé (chemin absolu, etc.), renvoyer le chemin brut
                response["file_path"] = file_path
        return response
    except Exception as e:
        return {"answer": f"Erreur agent: {str(e)}"}


@app.get("/mcp/download/{filename}")
def download_file(filename: str):
    # Sécuriser contre path traversal et rechercher le fichier dans l'espace de travail
    if os.path.sep in filename or filename.startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid filename")
    found = _find_file_by_basename(filename)
    if not found:
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return FileResponse(path=found, filename=filename, media_type='application/octet-stream')



