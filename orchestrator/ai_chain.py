from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
import os

format_instructions = (
    "Return a strict JSON object with keys: job_type (string), materials_cost (number), "
    "labor_hours (number), tools_needed (array of strings), total_cost (number), "
    "explanation (string). Do not include markdown fences or any extra text."
)

prompt = ChatPromptTemplate.from_template(
    """
You are an expert estimator for small business jobs.
Analyze the project description carefully and provide your best estimate.

Project description:
{description}

Follow this format strictly:
{format_instructions}
"""
)

# You can swap Ollama for other providers easily.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
# Build LCEL chain: prompt -> llm (returns a JSON string per instructions)
chain = prompt | llm

def generate_structured_estimate(description: str):
    """Generates structured output for an estimate request."""
    return chain.invoke({
        "description": description,
        "format_instructions": format_instructions
    })
