import json
import os
import uuid
from typing import List
from app.models import Idea, Node, Edge, Graph
from app.storage import load_idea
from app.config import IDEAS_DIR
from fastapi import HTTPException
from app.services.llm_client import LLMClient

import asyncio

async def build_graph_with_llm(idea_id: str) -> Graph:
    """Builds a graph using the LLM for dynamic, context-aware relations."""
    idea = load_idea(idea_id, IDEAS_DIR)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found.")

    # Prepare Q&A pairs for the prompt
    qa_pairs = ""
    for q, a in idea.answers.items():
        qa_pairs += f"{q}: {a}\n"

    # Render prompt
    with open(os.path.join(os.path.dirname(__file__), "../prompts/graph.txt"), "r") as f:
        prompt_template = f.read()
    prompt = (
        prompt_template
        .replace("{{idea_text}}", idea.text)
        .replace("{{qa_pairs}}", qa_pairs.strip())
    )

    # Call LLM
    llm = LLMClient()
    llm_response = await llm.send_prompt(prompt)

    # Parse JSON from LLM response
    import json
    try:
        graph_data = json.loads(llm_response)
        nodes = [Node(**n) for n in graph_data["nodes"]]
        edges = [Edge(**e) for e in graph_data["edges"]]
        graph = Graph(nodes=nodes, edges=edges)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM graph: {e}\nRaw LLM response: {llm_response}"
        )

    # Optionally save the graph to a JSON file
    graph_file_path = os.path.join(IDEAS_DIR, f"{idea_id}_graph.json")
    with open(graph_file_path, "w") as f:
        json.dump(graph.model_dump(), f, indent=4)

    return graph

async def build_graph(idea_id: str) -> Graph:
    """Reads idea and answers, converts into nodes & edges with heuristics."""
    idea = load_idea(idea_id, IDEAS_DIR)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found.")

    nodes: List[Node] = []
    edges: List[Edge] = []

    # Heuristic 1: Create a node for the main idea
    nodes.append(Node(id=idea.id, label=idea.text, type="idea", priority=5, notes="Main idea"))

    # Heuristic 2: Create nodes for each answer and link them to the main idea
    relation_types = [
        "is defined by",
        "depends on",
        "leads to",
        "is a part of",
        "has feature"
    ]
    for idx, (question, answer) in enumerate(idea.answers.items()):
        # Simple tokenization/entity extraction (can be improved with NLP)
        # For now, let's just create a node for each answer
        node_id = str(uuid.uuid5(uuid.NAMESPACE_URL, answer))
        nodes.append(Node(id=node_id, label=answer, type="feature", notes=question))
        relation = relation_types[idx % len(relation_types)]
        edges.append(Edge(from_node=idea.id, to_node=node_id, relation=relation))

    # Heuristic 3: More advanced graph building would involve NLP to identify relationships
    # between different answers/features, e.g., "depends_on", "uses_api", etc.
    # For this POC, we'll keep it simple.

    graph = Graph(nodes=nodes, edges=edges)

    # Optionally save the graph to a JSON file
    graph_file_path = os.path.join(IDEAS_DIR, f"{idea_id}_graph.json")
    with open(graph_file_path, "w") as f:
        json.dump(graph.model_dump(), f, indent=4)

    return graph
