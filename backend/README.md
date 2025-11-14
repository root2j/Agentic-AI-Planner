# Idea to Plan POC Backend Application

This document provides instructions on how to set up, run, and interact with the Idea to Plan backend application using the command-line interface (CLI).

## 1. Project Setup

1.  **Navigate to the project directory**:
    ```bash
    cd idea_to_plan_poc
    ```

2.  **Create and activate a Python virtual environment** (if you haven't already):
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your Gemini API Key**:
    Create a `.env` file in the `idea_to_plan_poc` directory (next to `.env.example`) and add your Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```
    Replace `"YOUR_GEMINI_API_KEY"` with your actual API key.

## 2. Running the Application

To start the FastAPI application, run the following command from within the `idea_to_plan_poc` directory:

```bash
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-exclude data/
```
(Note: On macOS/Linux, replace `.\venv\Scripts\python.exe` with `venv/bin/python`).

The application will run on `http://127.0.0.1:8000`.

## 3. API Endpoints (CLI Usage with `curl`)

You can interact with the API endpoints using `curl`. Ensure the FastAPI application is running before executing these commands.

### a. `POST /ideas` - Submit a New Idea

Submits a new idea text and returns a unique `idea_id`.

**Command:**
```bash
curl -X POST "http://127.0.0.1:8000/ideas?text=Develop%20a%20mobile%20app%20for%20learning%20new%20languages"
```

**Example Response:**
```json
{"idea_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"}
```
*Note down the `idea_id` from the response, as it will be used in subsequent calls.*

### b. `GET /ideas/{idea_id}/questions` - Generate Questions for an Idea

Generates a list of clarifying questions based on the submitted idea.

**Command:**
```bash
curl -X GET "http://127.0.0.1:8000/ideas/a1b2c3d4-e5f6-7890-1234-567890abcdef/questions"
```
*(Replace `a1b2c3d4-e5f6-7890-1234-567890abcdef` with your actual `idea_id`)*

**Example Response:**
```json
{"questions": ["What target languages will the app support?", "What learning methodologies will be implemented?", "How will user progress be tracked?"]}
```

### c. `POST /ideas/{idea_id}/answers` - Submit Answers to Questions

Submits answers to the generated questions.

**Command:**
```bash
curl -X POST "http://127.0.0.1:8000/ideas/a1b2c3d4-e5f6-7890-1234-567890abcdef/answers" \
     -H "Content-Type: application/json" \
     -d '{
           "What target languages will the app support?": "Spanish, French, German",
           "What learning methodologies will be implemented?": "Gamification, spaced repetition, interactive exercises",
           "How will user progress be tracked?": "Daily streaks, level system, achievement badges"
         }'
```
*(Replace `a1b2c3d4-e5f6-7890-1234-567890abcdef` with your actual `idea_id` and provide your answers)*

**Example Response:**
```json
{"status": "saved"}
```

### d. `GET /ideas/{idea_id}/graph` - Get the Idea Graph

Retrieves a graph representation of the idea and its answers.

**Command:**
```bash
curl -X GET "http://127.0.0.1:8000/ideas/a1b2c3d4-e5f6-7890-1234-567890abcdef/graph"
```
*(Replace `a1b2c3d4-e5f6-7890-1234-567890abcdef` with your actual `idea_id`)*

**Example Response:**
```json
{"nodes": [...], "edges": [...]}
```
*(The actual response will contain detailed node and edge data)*

### e. `GET /ideas/{idea_id}/plan` - Get the Generated Plan

Retrieves the detailed plan generated based on the idea, questions, and answers.

**Command:**
```bash
curl -X GET "http://127.0.0.1:8000/ideas/a1b2c3d4-e5f6-7890-1234-567890abcdef/plan"
```
*(Replace `a1b2c3d4-e5f6-7890-1234-567890abcdef` with your actual `idea_id`)*

**Example Response:**
```json
{"plan": "# Project Plan: Language Learning Mobile App\n\n## 1. Overview\n...\n"}
```
*(The actual response will contain the full markdown plan)*
