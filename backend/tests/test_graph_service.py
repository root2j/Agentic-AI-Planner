import pytest
import os
import json
from unittest.mock import patch, MagicMock
from app.services.graph_service import build_graph
from app.models import Idea, Node, Edge, Graph
from app.storage import save_idea, load_idea
from app.config import IDEAS_DIR
from fastapi import HTTPException

@pytest.fixture(autouse=True)
def setup_teardown():
    os.makedirs(IDEAS_DIR, exist_ok=True)
    yield
    for f in os.listdir(IDEAS_DIR):
        if f.endswith(".json"):
            os.remove(os.path.join(IDEAS_DIR, f))

@pytest.mark.asyncio
async def test_build_graph():
    idea_id = "test_graph_idea"
    idea_text = "Develop a new social media platform."
    answers = {
        "What is the target audience?": "Young adults (18-30)",
        "What are the core features?": "Feed, messaging, groups, events",
        "What is the monetization strategy?": "Ads and premium subscriptions"
    }
    idea = Idea(id=idea_id, text=idea_text, answers=answers)
    save_idea(idea, IDEAS_DIR)

    graph = await build_graph(idea_id)

    assert isinstance(graph, Graph)
    assert len(graph.nodes) == 1 + len(answers) # Main idea + each answer as a node
    assert len(graph.edges) == len(answers) # Each answer linked to main idea

    # Verify main idea node
    main_idea_node = next((node for node in graph.nodes if node.id == idea_id), None)
    assert main_idea_node is not None
    assert main_idea_node.label == idea_text
    assert main_idea_node.type == "idea"

    # Verify answer nodes and edges
    for question, answer in answers.items():
        answer_node = next((node for node in graph.nodes if node.label == answer), None)
        assert answer_node is not None
        assert answer_node.type == "feature"
        assert answer_node.notes == question

        edge = next((e for e in graph.edges if e.from_node == idea_id and e.to_node == answer_node.id), None)
        assert edge is not None
        # The relation depends on the order of answers and the relation_types list in graph_service.py
        # For the first answer (idx=0), it should be "is defined by"
        # For the second answer (idx=1), it should be "depends on"
        # For the third answer (idx=2), it should be "leads to"
        expected_relations = {
            "What is the target audience?": "is defined by",
            "What are the core features?": "depends on",
            "What is the monetization strategy?": "leads to"
        }
        assert edge.relation == expected_relations[question]

    # Verify graph file was saved
    graph_file_path = os.path.join(IDEAS_DIR, f"{idea_id}_graph.json")
    assert os.path.exists(graph_file_path)
    loaded_graph_data = json.load(open(graph_file_path))
    assert loaded_graph_data["nodes"] == [node.model_dump() for node in graph.nodes]
    assert loaded_graph_data["edges"] == [edge.model_dump() for edge in graph.edges]

@pytest.mark.asyncio
async def test_build_graph_idea_not_found():
    with pytest.raises(HTTPException) as exc_info:
        await build_graph("non_existent_id")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Idea not found."

@pytest.mark.asyncio
async def test_build_graph_no_answers():
    idea_id = "test_no_answers_idea"
    idea_text = "An idea with no answers yet."
    idea = Idea(id=idea_id, text=idea_text, answers={})
    save_idea(idea, IDEAS_DIR)

    graph = await build_graph(idea_id)
    assert isinstance(graph, Graph)
    assert len(graph.nodes) == 1 # Only the main idea node
    assert len(graph.edges) == 0

    main_idea_node = next((node for node in graph.nodes if node.id == idea_id), None)
    assert main_idea_node is not None
    assert main_idea_node.label == idea_text
