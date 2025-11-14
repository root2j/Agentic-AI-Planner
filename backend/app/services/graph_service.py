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
        nodes = [Node(**n) for n in graph_data.get("nodes", [])]
        edges = [Edge(**e) for e in graph_data.get("edges", [])]
        graph = Graph(nodes=nodes, edges=edges)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM graph: {e}\nRaw LLM response: {llm_response}"
        )
    
    # Save the generated graph to a JSON file
    graph_file_path = os.path.join(IDEAS_DIR, f"{idea_id}_graph.json")
    os.makedirs(os.path.dirname(graph_file_path), exist_ok=True)
    with open(graph_file_path, "w") as f:
        json.dump(graph.model_dump(), f, indent=4)
    print(f"Graph saved to: {graph_file_path}") # Debugging line

    return graph

async def edit_graph_with_llm(idea_id: str, user_text_input: str) -> Graph:
    """Edits an existing graph using the LLM based on user text input."""
    graph_file_path = os.path.join(IDEAS_DIR, f"{idea_id}_graph.json")
    if not os.path.exists(graph_file_path):
        raise HTTPException(status_code=404, detail="Graph not found for this idea.")

    with open(graph_file_path, "r") as f:
        existing_graph_data = json.load(f)
    
    # Render prompt for editing
    with open(os.path.join(os.path.dirname(__file__), "../prompts/edit_graph.txt"), "r") as f:
        prompt_template = f.read()
    prompt = (
        prompt_template
        .replace("{{existing_graph}}", json.dumps(existing_graph_data, indent=2))
        .replace("{{user_text_input}}", user_text_input)
    )

    # Call LLM
    llm = LLMClient()
    llm_response = await llm.send_prompt(prompt)

    # Parse JSON from LLM response
    try:
        updated_graph_data = json.loads(llm_response)
        nodes = [Node(**n) for n in updated_graph_data.get("nodes", [])]
        edges = [Edge(**e) for e in updated_graph_data.get("edges", [])]
        graph = Graph(nodes=nodes, edges=edges)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response for graph edit: {e}\nRaw LLM response: {llm_response}"
        )

    # Save the updated graph to a JSON file
    with open(graph_file_path, "w") as f:
        json.dump(graph.model_dump(), f, indent=4)

    return graph

async def load_graph(idea_id: str) -> Graph | None:
    """Loads an existing graph from a JSON file."""
    graph_file_path = os.path.join(IDEAS_DIR, f"{idea_id}_graph.json")
    if os.path.exists(graph_file_path):
        try:
            with open(graph_file_path, "r") as f:
                graph_data = json.load(f)
            nodes = [Node(**n) for n in graph_data.get("nodes", [])]
            edges = [Edge(**e) for e in graph_data.get("edges", [])]
            return Graph(nodes=nodes, edges=edges)
        except Exception as e:
            print(f"Error loading graph for idea_id {idea_id}: {e}")
            return None
    return None

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
