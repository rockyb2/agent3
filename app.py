from smolagents import CodeAgent,LiteLLMModel,Tool , DuckDuckGoSearchTool
import gradio as gr
import os
from tools import BuildWord,BuildPDF, BuildExcelPro,SendMail

import json
import os

HISTORY_FILE = "history.json"

def load_history_local():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history_local(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)



history_memory = load_history_local()



# class RagTool(Tool):
#     name = "RagTool"
#     description = "Fait une recherche RAG sur la base de connaissance."
#     inputs = {
#         "query": {"type": "string", "description": "Question à poser à la base de documents"}
#     }
#     output_type = "string"

#     def forward(self, query: str):
#         # Charger l'index déjà stocké
#         index = loadIndex()
        
#         query_engine = index.as_query_engine()
#         response = query_engine.query(query)
#         return str(response)

# NOTE: This local `buildAgent()` helper is used by the Gradio UI in `app.py`.
# For production / server usage prefer `agent_core.chat_with_agent(session_id, message)`
def buildAgent():
    agent = CodeAgent(
        model= LiteLLMModel(
            model_id= "mistral/mistral-large-latest",
            api_key=os.getenv("MISTRAL_API_KEY")
        ),
        tools=[DuckDuckGoSearchTool(),BuildWord(),BuildPDF(), BuildExcelPro(),SendMail()],
        max_steps = 5
    )
    
    return agent


agent = buildAgent()


# function for chat with agent
def chatwithAgent(message, history):
    # Ajouter message utilisateur
    history_memory.append({"role": "user", "content": message})
    
    # Obtenir réponse agent
    output = agent.run(message)

    # Si l'agent fournit un fichier (séparateur "||"), renvoyer un dict compatible Gradio
    if "||" in output:
        text, file_path = output.split("||")
        text = text.strip()
        file_path = file_path.strip()

        # Enregistrer la réponse (texte) dans l'historique
        history_memory.append({"role": "assistant", "content": text})
        save_history_local(history_memory)

        try:
            f = open(file_path, "rb")
            return {"content": text, "files": [{"name": os.path.basename(file_path), "data": f}]}
        except Exception as e:
            return f"{text} (fichier généré: {file_path}, mais impossible de l'attacher: {e})"

    # Pas de fichier : renvoyer simplement le texte
    history_memory.append({"role": "assistant", "content": output})
    save_history_local(history_memory)
    return output




# gr.ChatInterface(
#     fn=chatwithAgent,
#     description= "Agent IA assistant qui génère (pdf,excel et word)",
#     title= "Agent2",
# ).launch()
