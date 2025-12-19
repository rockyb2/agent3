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
        max_steps=5
    )


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
    output = agent.run(message)

    # Support pour outils qui renvoient "texte||chemin_du_fichier"
    if "||" in output:
        text, file_path = [p.strip() for p in output.split("||", 1)]
        history.append({"role": "assistant", "content": text})
        _save_history(session_id, history)
        return {"content": text, "file_path": file_path}

    history.append({"role": "assistant", "content": output})
    _save_history(session_id, history)
    return {"content": output}
