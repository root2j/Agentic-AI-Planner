import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.idea_service import ingest_idea, generate_questions, submit_answers
from app.services.graph_service import build_graph_with_llm, edit_graph_with_llm
from app.services.plan_service import get_plan
from unittest.mock import patch, MagicMock
from app.models import GraphEditRequest

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_services():
    with patch('app.main.ingest_idea') as mock_ingest_idea, \
         patch('app.main.generate_questions') as mock_generate_questions, \
         patch('app.main.submit_answers') as mock_submit_answers, \
         patch('app.main.build_graph_with_llm') as mock_build_graph_with_llm, \
         patch('app.main.edit_graph_with_llm') as mock_edit_graph_with_llm, \
         patch('app.main.get_plan') as mock_get_plan:
        yield mock_ingest_idea, mock_generate_questions, mock_submit_answers, mock_build_graph_with_llm, mock_edit_graph_with_llm, mock_get_plan

@pytest.mark.asyncio
async def test_create_idea(mock_services):
    mock_ingest_idea, _, _, _, _, _ = mock_services
    mock_ingest_idea.return_value = "test_idea_id"
    response = client.post("/ideas", params={"text": "Test idea"})
    assert response.status_code == 200
    assert response.json() == {"idea_id": "test_idea_id"}
    mock_ingest_idea.assert_called_once_with("Test idea")

@pytest.mark.asyncio
async def test_get_questions(mock_services):
    _, mock_generate_questions, _, _, _, _ = mock_services
    mock_generate_questions.return_value = ["Q1", "Q2"]
    response = client.get("/ideas/test_idea_id/questions")
    assert response.status_code == 200
    assert response.json() == {"questions": ["Q1", "Q2"]}
    mock_generate_questions.assert_called_once_with("test_idea_id")

@pytest.mark.asyncio
async def test_submit_answers(mock_services):
    _, _, mock_submit_answers, _, _, _ = mock_services
    answers = {"Q1": "A1", "Q2": "A2"}
    response = client.post("/ideas/test_idea_id/answers", json=answers)
    assert response.status_code == 200
    assert response.json() == {"status": "saved"}
    mock_submit_answers.assert_called_once_with("test_idea_id", answers)

@pytest.mark.asyncio
async def test_get_graph(mock_services):
    _, _, _, mock_build_graph_with_llm, _, _ = mock_services
    mock_build_graph_with_llm.return_value = {"nodes": [], "edges": []}
    response = client.get("/ideas/test_idea_id/graph")
    assert response.status_code == 200
    assert response.json() == {"nodes": [], "edges": []}
    mock_build_graph_with_llm.assert_called_once_with("test_idea_id")

@pytest.mark.asyncio
async def test_edit_graph(mock_services):
    _, _, _, _, mock_edit_graph_with_llm, _ = mock_services
    mock_edit_graph_with_llm.return_value = {"nodes": [{"id": "1", "label": "Edited Node"}], "edges": []}
    edit_request = GraphEditRequest(user_text_input="Edit node 1")
    response = client.post("/ideas/test_idea_id/graph/edit", json=edit_request.model_dump())
    assert response.status_code == 200
    assert response.json() == {"nodes": [{"id": "1", "label": "Edited Node"}], "edges": []}
    mock_edit_graph_with_llm.assert_called_once_with("test_idea_id", "Edit node 1")

@pytest.mark.asyncio
async def test_get_plan(mock_services):
    _, _, _, _, _, mock_get_plan = mock_services
    mock_plan_obj = MagicMock()
    mock_plan_obj.markdown = "# Test Plan"
    mock_get_plan.return_value = mock_plan_obj
    response = client.get("/ideas/test_idea_id/plan")
    assert response.status_code == 200
    assert response.json() == {"plan": "# Test Plan"}
    mock_get_plan.assert_called_once_with("test_idea_id")
