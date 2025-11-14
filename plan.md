**AI-Powered Idea‑to‑Plan Pipeline (Python‑only Proof of Concept)**

---

# Table of Contents
1. [Project Structure](#project-structure)
2. [Configuration & Dependencies](#configuration--dependencies)
3. [Data Models](#data-models)
4. [Function Specifications](#function-specifications)
   - `ingest_idea`
   - `generate_questions`
   - `submit_answers`
   - `build_graph`
   - `generate_plan` (internal)
   - `get_plan`
5. [Prompt Templates](#prompt-templates)
6. [API Endpoints](#api-endpoints)
7. [Storage & State Management](#storage--state-management)
8. [Testing Strategy](#testing-strategy)
9. [Future Extensions](#future-extensions)

---

## Project Structure

```
idea_to_plan_poc/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app instance & route registration
│   ├── config.py             # Load environment variables (GEMINI_API_KEY, paths)
│   ├── models.py             # Pydantic schemas (Idea, Question, Answer, Graph, Plan)
│   ├── storage.py            # JSON/SQLite read-write helpers
│   ├── prompts/
│   │   ├── questions.txt     # Template for Q generation
│   │   └── plan.txt          # Template for plan generation
│   ├── services/
│   │   ├── llm_client.py     # Gemini API wrapper
│   │   ├── idea_service.py   # Business logic for ingest & answer handling
│   │   ├── graph_service.py  # Graph builder & serializer
│   │   └── plan_service.py   # Plan generator logic
├── data/
│   ├── ideas/                # idea JSON files: {idea_id}.json
│   └── plans/                # plan markdown files: {idea_id}.md
├── tests/
│   ├── test_idea.py
│   ├── test_graph.py
│   └── test_plan.py
├── requirements.txt          # Dependencies pinned
├── README.md                 # High-level overview & setup
└── .env.example              # Sample env vars file
```

---

## Configuration & Dependencies

- **Python** ≥3.10
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **httpx**: Async HTTP client for Gemini
- **Pydantic**: Data validation & serialization
- **python-dotenv**: Load `.env`
- **(Optional)** SQLite via `databases` or plain `sqlite3`

```bash
# requirements.txt
fastapi
uvicorn[standard]
httpx
pydantic
python-dotenv
```

---

## Data Models (`app/models.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Dict

class Idea(BaseModel):
    id: str
    text: str
    questions: List[str] = []
    answers: Dict[str, str] = {}

class Question(BaseModel):
    question: str

class Answer(BaseModel):
    question: str
    answer: str

class Node(BaseModel):
    id: str
    label: str
    type: str = "feature"
    priority: int = Field(default=0, ge=0, le=5)
    notes: str = ""

class Edge(BaseModel):
    from_node: str
    to_node: str
    relation: str = "depends_on"

class Graph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

class Plan(BaseModel):
    idea_id: str
    markdown: str
```

---

## Function Specifications

### 1. `ingest_idea(text: str) -> str`
- **Location**: `app/services/idea_service.py`
- **Description**: Generates a UUID, stores raw idea in JSON, returns `idea_id`.
- **Steps**:
  1. Validate input text.
  2. Create `Idea(id=UUID, text=text)`.
  3. Write JSON to `data/ideas/{id}.json`.
  4. Return `id`.

### 2. `generate_questions(idea_id: str) -> List[str]`
- **Location**: `app/services/llm_client.py` + `idea_service.py`
- **Description**: Loads idea text, calls Gemini with `questions.txt` prompt, returns list.
- **Steps**:
  1. Load idea JSON.
  2. Read `prompts/questions.txt` and format with idea text.
  3. Call Gemini API via `llm_client.send_prompt()`.
  4. Parse LLM response into list.
  5. Update `Idea.questions` and persist.

### 3. `submit_answers(idea_id: str, answers: Dict[str, str]) -> None`
- **Location**: `app/services/idea_service.py`
- **Description**: Saves question-answer mapping to idea JSON.
- **Steps**:
  1. Validate that questions exist.
  2. Merge provided answers into `Idea.answers`.
  3. Persist JSON.

### 4. `build_graph(idea_id: str) -> Graph`
- **Location**: `app/services/graph_service.py`
- **Description**: Reads idea and answers, converts into nodes & edges with heuristics.
- **Steps**:
  1. Load `Idea` object.
  2. Tokenize `Idea.text` and answers to identify features/entities.
  3. Create `Node` instances per feature, with `notes` from answers.
  4. Auto-generate `Edge` relations (`depends_on`, `uses_api`).
  5. Return `Graph` and write JSON to `data/ideas/{id}_graph.json`.

### 5. `generate_plan(graph: Graph) -> str`
- **Location**: `app/services/plan_service.py`
- **Description**: Formats `prompts/plan.txt` with graph JSON, calls Gemini, returns markdown.
- **Steps**:
  1. Serialize `Graph` to JSON string.
  2. Read `prompts/plan.txt`, embed JSON.
  3. Call `llm_client.send_prompt()`.
  4. Receive markdown string.
  5. Return plan markdown.

### 6. `get_plan(idea_id: str) -> Plan`
- **Location**: `app/services/plan_service.py`
- **Description**: Checks for existing plan file; if missing, invokes `generate_plan()`.
- **Steps**:
  1. If `data/plans/{id}.md` exists, load and return.
  2. Else, call `build_graph()` → `generate_plan()`.
  3. Save markdown to file.
  4. Return `Plan(idea_id, markdown)`.

---

## Prompt Templates (`app/prompts`)

- **questions.txt**
  ```txt
  Given the following app idea:
  {{idea_text}}
  List 5 questions that clarify its scope, users, and core features.
  ```

- **plan.txt**
  ```txt
  Here is a JSON representation of an idea graph:
  {{graph_json}}
  Please generate a step-by-step development plan, in markdown format, with clear task titles, descriptions, and order.
  ```

---

## API Endpoints (`app/main.py`)

```python
from fastapi import FastAPI, HTTPException
from app.services.idea_service import ingest_idea, generate_questions, submit_answers
from app.services.graph_service import build_graph
from app.services.plan_service import get_plan

app = FastAPI()

@app.post("/ideas")
def create_idea(text: str):
    return {"idea_id": ingest_idea(text)}

@app.get("/ideas/{idea_id}/questions")
def questions(idea_id: str):
    return {"questions": generate_questions(idea_id)}

@app.post("/ideas/{idea_id}/answers")
def answers(idea_id: str, answers: dict):
    submit_answers(idea_id, answers)
    return {"status": "saved"}

@app.get("/ideas/{idea_id}/graph")
def graph(idea_id: str):
    return build_graph(idea_id)

@app.get("/ideas/{idea_id}/plan")
def plan(idea_id: str):
    plan_obj = get_plan(idea_id)
    return {"plan": plan_obj.markdown}
```

---

## Storage & State Management

- JSON files under `data/ideas/` and `data/plans/` for persistence.
- Use file locks or atomic writes to avoid race conditions.
- Track versions via timestamped filenames or metadata inside JSON.

---

## Testing Strategy

- **Unit Tests** for each service function (mock Gemini calls).
- **Integration Tests** hitting the FastAPI endpoints (use `TestClient`).
- **Sample Test** in `tests/test_idea.py`:
  ```python
  def test_ingest_and_questions(client, monkeypatch):
      monkeypatch.setenv("GEMINI_API_KEY", "test")
      # mock LLM response
      response = client.post("/ideas", json={"text": "Test app."})
      assert response.status_code == 200
      idea_id = response.json()["idea_id"]
      # further tests...
  ```

---

## Future Extensions

- **n8n Integration**: Call these endpoints via HTTP Request nodes.
- **MCP Adapter**: Wrap responses with protocol metadata.
- **SQLite/MongoDB**: Replace JSON storage for scaling.
- **Frontend**: React/VSC Extension with Mermaid/D3 graph render.

---

*This document now details the full codebase structure, every function's role, models, prompts, endpoints, storage, and testing.*

---

## 10. Execution Steps
Below is a detailed sequence to implement and run the project from zero to first working prototype.

1. **Environment Setup**
   - Install Python 3.10+.
   - Create and activate a virtual environment:
     ```bash
     python -m venv venv
     source venv/bin/activate  # Linux/macOS
     venv\Scripts\activate    # Windows
     ```
   - Copy `.env.example` to `.env` and set your `GEMINI_API_KEY`.
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```

2. **Project Initialization**
   - Clone or create the `idea_to_plan_poc` folder following the documented structure.
   - Ensure `data/ideas` and `data/plans` directories exist (create if missing).

3. **Implement Configuration**
   - In `app/config.py`, load environment variables using `python-dotenv`:
     ```python
     from dotenv import load_dotenv
     import os

     load_dotenv()
     GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
     IDEAS_DIR = os.getenv("IDEAS_DIR", "data/ideas")
     PLANS_DIR = os.getenv("PLANS_DIR", "data/plans")
     ```

4. **Develop Data Models**
   - Copy the Pydantic models into `app/models.py` exactly as specified.
   - Run a quick sanity check by importing and instantiating each model in an interactive shell.

5. **Build Storage Helpers**
   - In `app/storage.py`, write functions to read/write JSON files by `idea_id` and plans by `idea_id`.
   - Use atomic writes (write temp file then rename) to avoid partial writes.

6. **LLM Client Wrapper**
   - In `app/services/llm_client.py`, implement `send_prompt(prompt: str) -> str` using `httpx`.
   - Handle API key, errors, timeouts, and parsing.

7. **Service Layer Implementation**
   - **Idea Service** (`idea_service.py`): implement `ingest_idea`, `generate_questions`, `submit_answers`.
   - **Graph Service** (`graph_service.py`): implement `build_graph` heuristics.
   - **Plan Service** (`plan_service.py`): implement `generate_plan`, `get_plan` logic.

8. **API Layer**
   - In `app/main.py`, define FastAPI app and declare each endpoint.
   - Start the app via Uvicorn for local testing:
     ```bash
     uvicorn app.main:app --reload
     ```

9. **Prompt Tuning**
   - Edit `app/prompts/questions.txt` and `plan.txt` to refine clarity and output format.
   - Manually test prompts by calling `llm_client.send_prompt()` in a REPL.

10. **Manual Testing**
    - Use `curl` or Postman to walk through the full workflow:
      1. `POST /ideas` → get `idea_id`.
      2. `GET /ideas/{id}/questions` → verify questions list.
      3. `POST /ideas/{id}/answers` → send dummy answers.
      4. `GET /ideas/{id}/graph` → inspect graph JSON.
      5. `GET /ideas/{id}/plan` → review generated markdown.

11. **Automated Testing**
    - Run `pytest` to execute the unit and integration tests.
    - Mock Gemini API in tests to control outputs.

12. **Iteration & Refinement**
    - Based on initial results, adjust graph heuristics and prompt templates.
    - Expand node metadata (e.g., add effort estimates).

13. **Prepare for n8n & MCP**
    - Expose your local server via ngrok (or similar) for webhook tests.
    - Create sample n8n workflow calling each endpoint in order.
    - Draft an MCP adapter layer if needed, wrapping each response in protocol headers.

---

*Follow these steps in order to go from an empty repo to a fully functional POC, then iterate and extend.*
