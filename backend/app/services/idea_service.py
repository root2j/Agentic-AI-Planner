import uuid
import os
from typing import List, Dict
from app.models import Idea
from app.storage import save_idea, load_idea
from app.config import IDEAS_DIR
from fastapi import HTTPException
from app.services.llm_client import LLMClient # Keep import at top

async def ingest_idea(text: str) -> str:
    """Generates a UUID, stores raw idea in JSON, returns idea_id."""
    if not text:
        raise ValueError("Idea text cannot be empty.")
    idea_id = str(uuid.uuid4())
    idea = Idea(id=idea_id, text=text)
    save_idea(idea, IDEAS_DIR)
    return idea_id

async def generate_questions(idea_id: str) -> List[str]:
    """Loads idea text, calls Gemini with questions.txt prompt, returns list."""
    idea = load_idea(idea_id, IDEAS_DIR)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found.")

    prompt_template_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "questions.txt")
    with open(prompt_template_path, "r") as f:
        prompt_template = f.read()

    prompt = prompt_template.replace("{{idea_text}}", idea.text)
    llm_client = LLMClient() # Instantiate LLMClient inside the function
    llm_response = await llm_client.send_prompt(prompt)

    # Assuming LLM response is a newline-separated list of questions
    # Extract only the question text, ignoring markdown and clarifications
    raw_questions = [q.strip() for q in llm_response.split('\n') if q.strip()]
    questions = []
    for q in raw_questions:
        # Simple heuristic to extract the main question part
        if q.startswith(('1.', '2.', '3.', '4.', '5.')):
            # Remove numbering and any leading markdown like '**Question:**'
            clean_q = q.split('**Question:**')[-1].strip()
            clean_q = clean_q.split('*Clarifies:')[0].strip()
            clean_q = clean_q.replace('*', '').strip()
            if clean_q:
                questions.append(clean_q)
        elif q.startswith('*   **Question:**'):
            clean_q = q.split('**Question:**')[-1].strip()
            clean_q = clean_q.split('*Clarifies:')[0].strip()
            clean_q = clean_q.replace('*', '').strip()
            if clean_q:
                questions.append(clean_q)
        elif q.endswith('?'): # Catch any simple questions
            questions.append(q.replace('*', '').strip())

    idea.questions = questions
    save_idea(idea, IDEAS_DIR)
    return questions

async def submit_answers(idea_id: str, answers: Dict[str, str]) -> None:
    """Saves question-answer mapping to idea JSON."""
    idea = load_idea(idea_id, IDEAS_DIR)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found.")

    if not idea.questions:
        raise ValueError("No questions generated for this idea yet. Please generate questions first.")

    # Validate that provided answers correspond to generated questions
    for q in answers.keys():
        if q not in idea.questions:
            raise ValueError(f"Answer provided for unknown question: {q}")

    idea.answers.update(answers)
    save_idea(idea, IDEAS_DIR)
