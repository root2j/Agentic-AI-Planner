import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.idea_service import ingest_idea
from app.models import GraphEditRequest, Idea
from app.storage import save_idea
from app.config import IDEAS_DIR
from unittest.mock import patch, MagicMock
import pytest_asyncio # Import pytest_asyncio
from app.services.llm_client import LLMClient # Import LLMClient to check API key status
from app.services.graph_service import build_graph_with_llm # Import to ensure graph is built

client = TestClient(app)

@pytest_asyncio.fixture(scope="module", autouse=True) # Use pytest_asyncio.fixture
async def setup_test_data():
    # Ensure LLMClient is initialized and check API key status
    llm_client_instance = LLMClient() # This will trigger the print statement in LLMClient.__init__
    
    # This fixture will run once for the module
    # Directly save an idea to be used across performance tests
    idea_id = "perf_test_idea_id"
    idea_text = "Performance test idea"
    idea = Idea(id=idea_id, text=idea_text, answers={"Q1": "A1", "Q2": "A2"})
    save_idea(idea, IDEAS_DIR)

    # Ensure graph is built for edit_graph_performance test
    await build_graph_with_llm(idea_id)
    
    # Mock idea_service calls to isolate performance of graph and plan services
    with patch('app.main.generate_questions') as mock_generate_questions, \
         patch('app.main.submit_answers') as mock_submit_answers:
        
        mock_generate_questions.return_value = ["Q1", "Q2"]
        mock_submit_answers.return_value = None
        
        yield # This allows the tests to run
        
        # Teardown (if necessary, though for performance tests, usually not critical)

@pytest.mark.benchmark(group="api_performance")
def test_create_idea_performance(benchmark):
    response = benchmark(lambda: client.post("/ideas", params={"text": "Another test idea"}))
    assert response.status_code == 200
    return response

@pytest.mark.benchmark(group="api_performance")
def test_get_questions_performance(benchmark, setup_test_data):
    response = benchmark(lambda: client.get("/ideas/perf_test_idea_id/questions"))
    assert response.status_code == 200
    return response

@pytest.mark.benchmark(group="api_performance")
def test_submit_answers_performance(benchmark, setup_test_data):
    answers = {"Q1": "A1", "Q2": "A2"}
    response = benchmark(lambda: client.post("/ideas/perf_test_idea_id/answers", json=answers))
    assert response.status_code == 200
    return response

@pytest.mark.benchmark(group="api_performance")
def test_get_graph_performance(benchmark, setup_test_data):
    response = benchmark(lambda: client.get("/ideas/perf_test_idea_id/graph"))
    assert response.status_code == 200
    return response

@pytest.mark.benchmark(group="api_performance")
def test_edit_graph_performance(benchmark, setup_test_data):
    edit_request = GraphEditRequest(user_text_input="Edit node 1 for performance")
    response = benchmark(lambda: client.post("/ideas/perf_test_idea_id/graph/edit", json=edit_request.model_dump()))
    assert response.status_code == 200
    return response

@pytest.mark.benchmark(group="api_performance")
def test_get_plan_performance(benchmark, setup_test_data):
    response = benchmark(lambda: client.get("/ideas/perf_test_idea_id/plan"))
    assert response.status_code == 200
    return response
