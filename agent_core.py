# agent_core.py
from smolagents import ToolCallingAgent, LiteLLMModel
import os
import json
from typing import Optional
from tools import BuildWord, BuildPDF, BuildExcelPro, SendMail
from langfuse import Langfuse


langfuse = Langfuse(
    host="https://cloud.langfuse.com",
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY")
)

def create_agent():
    custom_instructions = """
RÔLE :
Tu es un assistant conversationnel professionnel et prudent.

RÈGLES STRICTES (À RESPECTER ABSOLUMENT) :
1. Tu NE DOIS JAMAIS appeler un outil pour générer un fichier ou envoyer un email sans demande EXPLICITE contenant des verbes comme : génère, crée, produis, exporte, envoie, fais-moi un fichier, etc.
2. Si la demande est vague ou ambiguë, pose une question de clarification sans appeler d'outil.
3. Par défaut, réponds UNIQUEMENT en texte clair, professionnel et concis.
4. Réponds TOUJOURS en français.
5. N'appelle les outils que si c'est strictement nécessaire et autorisé par l'utilisateur.

OBJECTIF :
Converser normalement, répondre aux questions, expliquer – sans actions automatiques.
"""

    return ToolCallingAgent(
        model=LiteLLMModel(
            model_id="mistral/mistral-large-latest",
            api_key=os.getenv("MISTRAL_API_KEY")
        ),
        tools=[
            BuildWord(),
            BuildPDF(),
            BuildExcelPro(),
            SendMail()
        ],
        max_steps=10,  # Augmente un peu si besoin
        instructions=custom_instructions
    )

KEYWORDS_FILES = [
    "génère", "crée", "produis", "exporte",
    "fichier", "pdf", "word", "excel", "envoyer", "mail"
]


def user_explicitly_requested_file(message: str) -> bool:
    msg = message.lower()
    return any(k in msg for k in KEYWORDS_FILES)


# --- Conversation helper API ---
# Fournit `chat_with_agent(session_id, message)` pour gérer l'historique par session
_agent_cache = None


def _get_agent_cached():
    global _agent_cache
    if _agent_cache is None:
        _agent_cache = create_agent()
    return _agent_cache


def _history_path(session_id: str) -> str:
    return f"history_{session_id}.json"


def _load_history(session_id: str):
    p = _history_path(session_id)
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_history(session_id: str, history):
    with open(_history_path(session_id), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def chat_with_agent(session_id: str, message: str) -> dict:
    """
    Gère l'historique par session, appelle l'agent et retourne:
      { "content": "...", "file_path": "..." }  (file_path optionnel)
    """
    history = _load_history(session_id)
    history.append({"role": "user", "content": message})

    agent = _get_agent_cached()
    # 🔒 GARDE-FOU

    with langfuse.start_as_current_observation(as_type="span", name="forlangraph") as obs:
        obs.update(input={"user": message})
        output = str(agent.run(message))
        obs.update(output={"agent": output})

    # Gestion fichier éventuel
    if "||" in output:
        text, file_path = output.split("||", 1)
        history.append({"role": "assistant", "content": text.strip()})
        _save_history(session_id, history)
        return {
            "content": text.strip(),
            "file_path": file_path.strip()
        }

    history.append({"role": "assistant", "content": output})
    _save_history(session_id, history)
    return {"content": output}
