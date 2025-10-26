# orchestrator/phase_chain.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
import os
import os

prompt = ChatPromptTemplate.from_template("""
You are a project manager. Given a job description, break the project into logical phases.
For each phase, provide:
- phase_name
- objective
- estimated_hours
- dependencies (if any)
- deliverables
Return a JSON list of phases.

Job description:
{description}
""")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
# LCEL chain: prompt -> llm
chain = prompt | llm

def generate_project_phases(description: str):
    """Generates a list of project phases for the given description."""
    return chain.invoke({"description": description})
