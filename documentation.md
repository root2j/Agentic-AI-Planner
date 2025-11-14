# Agantic AI Planner Documentation

## Overview

Agantic AI Planner is a Python-based proof-of-concept (POC) for an AI-powered pipeline that transforms raw ideas into actionable project plans. It leverages FastAPI, Gemini LLM, and a modular service architecture to automate the process from idea ingestion to plan generation.

## Features

- Submit raw ideas and receive clarifying questions.
- Answer questions to refine the idea scope.
- Automatic graph construction of features and dependencies.
- AI-generated, step-by-step project plans in markdown.
- RESTful API for integration and automation.
- Minimal frontend (static HTML) for demonstration.

## Project Structure

```
backend/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   ├── storage.py
│   ├── prompts/
│   │   ├── questions.txt
│   │   └── plan.txt
│   ├── services/
│   │   ├── llm_client.py
│   │   ├── idea_service.py
│   │   ├── graph_service.py
│   │   └── plan_service.py
├── data/
│   ├── ideas/
│   └── plans/
├── tests/
├── requirements.txt
├── README.md
├── .env.example
frontend/
└── index.html
plan.md
documentation.md
```

## Setup Instructions

See `backend/README.md` for detailed backend setup, environment variables, and running instructions.

**Quick Start:**
1. Install Python 3.10+ and create a virtual environment.
2. Install dependencies:  
   `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set your `GEMINI_API_KEY`.
4. Start the backend:  
   `uvicorn app.main:app --reload`
5. Access the API at `http://127.0.0.1:8000`.

## API Usage

Interact with the backend using `curl`, Postman, or any HTTP client.

- **POST /ideas**: Submit a new idea.
- **GET /ideas/{idea_id}/questions**: Get clarifying questions.
- **POST /ideas/{idea_id}/answers**: Submit answers.
- **GET /ideas/{idea_id}/graph**: Retrieve the idea graph.
- **GET /ideas/{idea_id}/plan**: Get the generated plan.

See `backend/README.md` for example requests and responses.

## Backend Details

- **Models**: Defined in `app/models.py` using Pydantic.
- **Services**: Business logic in `app/services/`.
- **Prompts**: LLM prompt templates in `app/prompts/`.
- **Storage**: JSON files in `data/ideas/` and `data/plans/`.

## Frontend

A minimal static HTML file is provided in `frontend/index.html`. No interactive frontend is included in this POC.

## Testing

- Unit and integration tests are in `backend/tests/`.
- Run tests with:
  ```
  pytest
  ```
- Gemini API calls are mocked in tests.

## Contributing & Future Work

- Extend storage to use SQLite or MongoDB.
- Build a full-featured frontend (React, VSCode extension, etc.).
- Integrate with n8n or MCP for workflow automation.
- Improve graph heuristics and prompt templates.

## References

- `plan.md`: In-depth architecture, models, and execution steps.
- `backend/README.md`: Backend setup and API usage.
