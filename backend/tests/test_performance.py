import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.idea_service import ingest_idea
from app.models import GraphEditRequest
from unittest.mock import patch, MagicMock
import asyncio

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_data():
    # This fixture will run once for the module
    # Ingest an idea to be used across performance tests
    with patch('app.main.ingest_idea') as mock_ingest_idea:
        mock_ingest_idea.return_value = "perf_test_idea_id"
        response = client.post("/ideas", params={"text": "Performance test idea"})
        assert response.status_code == 200
        assert response.json() == {"idea_id": "perf_test_idea_id"}
    
    # Mock other services for subsequent calls to avoid actual LLM calls during performance tests
    with patch('app.main.generate_questions') as mock_generate_questions, \
         patch('app.main.submit_answers') as mock_submit_answers, \
         patch('app.main.build_graph_with_llm') as mock_build_graph_with_llm, \
         patch('app.main.edit_graph_with_llm') as mock_edit_graph_with_llm, \
         patch('app.main.get_plan') as mock_get_plan:
        
        mock_generate_questions.return_value = ["Q1", "Q2"]
        mock_submit_answers.return_value = None
        mock_build_graph_with_llm.return_value = {"nodes": [], "edges": []}
        mock_edit_graph_with_llm.return_value = {"nodes": [{"id": "1", "label": "Edited Node"}], "edges": []}
        mock_plan_obj = MagicMock()
        mock_plan_obj.markdown = "# Performance Test Plan"
        mock_get_plan.return_value = mock_plan_obj
        
        # Simulate a call to generate questions and answers to set up the idea state
        client.get("/ideas/perf_test_idea_id/questions")
        client.post("/ideas/perf_test_idea_id/answers", json={"Q1": "A1", "Q2": "A2"})
        client.get("/ideas/perf_test_idea_id/graph") # Build graph once
        client.get("/ideas/perf_test_idea_id/plan") # Generate plan once
        
        yield # This allows the tests to run
        
        # Teardown (if necessary, though for performance tests, usually not critical)

@pytest.mark.benchmark(group="api_performance")
@pytest.mark.asyncio
async def test_create_idea_performance(benchmark):
    @benchmark
    async def _():
        response = client.post("/ideas", params={"text": "Another test idea"})
        assert response.status_code == 200
        return response

@pytest.mark.benchmark(group="api_performance")
@pytest.mark.asyncio
async def test_get_questions_performance(benchmark, setup_test_data):
    @benchmark
    async def _():
        response = client.get("/ideas/perf_test_idea_id/questions")
        assert response.status_code == 200
        return response

@pytest.mark.benchmark(group="api_performance")
@pytest.mark.asyncio
async def test_submit_answers_performance(benchmark, setup_test_data):
    answers = {"Q1": "A1", "Q2": "A2"}
    @benchmark
    async def _():
        response = client.post("/ideas/perf_test_idea_id/answers", json=answers)
        assert response.status_code == 200
        return response

@pytest.mark.benchmark(group="api_performance")
@pytest.mark.asyncio
async def test_get_graph_performance(benchmark, setup_test_data):
    @benchmark
    async def _():
        response = client.get("/ideas/perf_test_idea_id/graph")
        assert response.status_code == 200
        return response

@pytest.mark.benchmark(group="api_performance")
@pytest.mark.asyncio
async def test_edit_graph_performance(benchmark, setup_test_data):
    edit_request = GraphEditRequest(user_text_input="Edit node 1 for performance")
    @benchmark
    async def _():
        response = client.post("/ideas/perf_test_idea_id/graph/edit", json=edit_request.model_dump())
        assert response.status_code == 200
        return response

@pytest.mark.benchmark(group="api_performance")
@pytest.mark.asyncio
async def test_get_plan_performance(benchmark, setup_test_data):
    @benchmark
    async def _():
        response = client.get("/ideas/perf_test_idea_id/plan")
        assert response.status_code == 200
        return response
