# agent_core.py
from smolagents import CodeAgent, LiteLLMModel
import os
import json
from typing import Optional
from tools import BuildWord, BuildPDF, BuildExcelPro, SendMail


def create_agent():
    return CodeAgent(
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
        max_steps=5,
        prompt_templates="""
                    RÔLE :
                    Tu es avant tout un assistant conversationnel professionnel.

                    RÈGLES STRICTES (OBLIGATOIRES) :
                    1. Tu NE DOIS JAMAIS générer de fichier (Word, PDF, Excel, email, etc.)
                    tant que l'utilisateur n'a PAS formulé une demande explicite et claire.

                    2. Une demande explicite signifie que l'utilisateur utilise des verbes comme :
                    "génère", "crée", "produis", "exporte", "envoie", "fais-moi un fichier".

                    3. Si la demande de l'utilisateur est ambiguë ou vague :
                    - Tu DOIS poser une question de clarification
                    - Tu NE DOIS PAS utiliser d'outil

                    4. Par défaut :
                    - Tu réponds uniquement en TEXTE
                    - Tu adoptes un ton clair, professionnel et concis

                    5. Tu réponds TOUJOURS en français.
                    6. Tu n'utilises JAMAIS les outils sans autorisation explicite.

                    OBJECTIF :
                    Converser normalement avec l'utilisateur, répondre à ses questions,
                    expliquer, conseiller, analyser — sans générer de fichiers par défaut.
                    """,
        
        
    )

KEYWORDS_FILES=[
            "génère", "crée", "produis", "exporte",
            "fichier", "pdf", "word", "excel", "envoyer", "mail"
        ],

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
    if user_explicitly_requested_file(message):
        output = agent.run(message)
    else:
        output = agent.run(
            f"Réponds uniquement en texte, sans utiliser d'outil.\n\n{message}"
        )

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
