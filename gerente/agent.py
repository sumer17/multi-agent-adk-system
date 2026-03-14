from google.adk.agents import LlmAgent





root_agent = LlmAgent(
    name="retail_insight_agent",
    model="gemini-2.5-flash", 
    instruction="responde consulta de manera general"
)