import json
import os
from app.models import Plan, Graph
from app.storage import save_plan_markdown, load_plan_markdown
from app.config import PLANS_DIR
from app.services.llm_client import LLMClient
from app.services.graph_service import build_graph, build_graph_with_llm, load_graph


async def generate_plan(graph: Graph) -> str:
    """Formats prompts/plan.txt with graph JSON, calls Gemini, returns markdown."""
    prompt_template_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "plan.txt")
    with open(prompt_template_path, "r") as f:
        prompt_template = f.read()

    graph_json = json.dumps(graph.model_dump(), indent=2)
    prompt = prompt_template.replace("{{graph_json}}", graph_json)
    
    llm_client = LLMClient() # Instantiate LLMClient inside the function
    llm_response = await llm_client.send_prompt(prompt)
    return llm_response

async def get_plan(idea_id: str) -> Plan:
    """Checks for existing plan file; if missing, invokes generate_plan()."""
    existing_plan_markdown = load_plan_markdown(idea_id, PLANS_DIR)
    if existing_plan_markdown:
        return Plan(idea_id=idea_id, markdown=existing_plan_markdown)
    
    graph = await load_graph(idea_id)
    if not graph:
        graph = await build_graph_with_llm(idea_id)
    
    plan_markdown = await generate_plan(graph)
    
    plan = Plan(idea_id=idea_id, markdown=plan_markdown)
    save_plan_markdown(plan, PLANS_DIR)
    return plan
