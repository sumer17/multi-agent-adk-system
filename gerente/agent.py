from google.adk.agents import LlmAgent

from .prompts import INSTRUCCIONES_GERENTE
from .tools import llamar_analista_bd, csv_report_generator



root_agent = LlmAgent(
    name="retail_insight_agent",
    model="gemini-2.5-flash", 
    instruction=INSTRUCCIONES_GERENTE,
    tools=[llamar_analista_bd, csv_report_generator]
)