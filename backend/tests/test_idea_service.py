import pytest
import os
from unittest.mock import patch, MagicMock
from app.services.idea_service import ingest_idea, generate_questions, submit_answers
from app.models import Idea
from app.config import IDEAS_DIR
from fastapi import HTTPException

@pytest.fixture(autouse=True)
def setup_teardown():
    # Ensure IDEAS_DIR exists for testing
    os.makedirs(IDEAS_DIR, exist_ok=True)
    yield
    # Clean up any created idea files after tests
    for f in os.listdir(IDEAS_DIR):
        if f.endswith(".json"):
            os.remove(os.path.join(IDEAS_DIR, f))

@pytest.mark.asyncio
async def test_ingest_idea():
    idea_text = "A new idea for a project."
    idea_id = await ingest_idea(idea_text)
    assert isinstance(idea_id, str)
    assert len(idea_id) > 0

    # Verify the idea was saved
    idea_file_path = os.path.join(IDEAS_DIR, f"{idea_id}.json")
    assert os.path.exists(idea_file_path)
    
    # Load and check content
    loaded_idea = Idea.model_validate_json(open(idea_file_path).read())
    assert loaded_idea.id == idea_id
    assert loaded_idea.text == idea_text

@pytest.mark.asyncio
async def test_ingest_idea_empty_text():
    with pytest.raises(ValueError, match="Idea text cannot be empty."):
        await ingest_idea("")

@pytest.mark.asyncio
async def test_generate_questions():
    idea_text = "Another idea."
    idea_id = await ingest_idea(idea_text)

    mock_llm_response = "Q1: What is it?\nQ2: Why is it important?"
    with patch('app.services.llm_client.LLMClient.send_prompt', return_value=mock_llm_response) as mock_send_prompt:
        questions = await generate_questions(idea_id)
        assert questions == ["Q1: What is it?", "Q2: Why is it important?"]
        mock_send_prompt.assert_called_once()
        
        # Verify questions are saved to the idea
        loaded_idea = Idea.model_validate_json(open(os.path.join(IDEAS_DIR, f"{idea_id}.json")).read())
        assert loaded_idea.questions == questions

@pytest.mark.asyncio
async def test_generate_questions_idea_not_found():
    with pytest.raises(HTTPException) as exc_info:
        await generate_questions("non_existent_id")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Idea not found."

@pytest.mark.asyncio
async def test_submit_answers():
    idea_text = "Idea for answers."
    idea_id = await ingest_idea(idea_text)

    # First, generate questions (mocking LLM)
    mock_llm_response = "Q1: Question one?\nQ2: Question two?"
    with patch('app.services.llm_client.LLMClient.send_prompt', return_value=mock_llm_response):
        await generate_questions(idea_id)

    answers = {"Q1: Question one?": "Answer one.", "Q2: Question two?": "Answer two."}
    await submit_answers(idea_id, answers)

    # Verify answers are saved
    loaded_idea = Idea.model_validate_json(open(os.path.join(IDEAS_DIR, f"{idea_id}.json")).read())
    assert loaded_idea.answers == answers

@pytest.mark.asyncio
async def test_submit_answers_idea_not_found():
    with pytest.raises(HTTPException) as exc_info:
        await submit_answers("non_existent_id", {"Q1": "A1"})
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Idea not found."

@pytest.mark.asyncio
async def test_submit_answers_no_questions_generated():
    idea_text = "Idea without questions."
    idea_id = await ingest_idea(idea_text)

    with pytest.raises(ValueError, match="No questions generated for this idea yet. Please generate questions first."):
        await submit_answers(idea_id, {"Q1": "A1"})

@pytest.mark.asyncio
async def test_submit_answers_unknown_question():
    idea_text = "Idea with known questions."
    idea_id = await ingest_idea(idea_text)

    mock_llm_response = "Q1: Known question?"
    with patch('app.services.llm_client.LLMClient.send_prompt', return_value=mock_llm_response):
        await generate_questions(idea_id)

    with pytest.raises(ValueError, match="Answer provided for unknown question: Unknown Q"):
        await submit_answers(idea_id, {"Unknown Q": "Answer."})
