from google.adk.agents import LlmAgent

from .prompts import INSTRUCCIONES_ANALISTA
from .tools import get_retail_data

agente_analista = LlmAgent(
    name="analista_bd_agent",
    model="gemini-2.5-flash",
    instruction=INSTRUCCIONES_ANALISTA,
    tools=[get_retail_data]
)

