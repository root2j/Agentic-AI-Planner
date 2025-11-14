from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.services.idea_service import ingest_idea, generate_questions, submit_answers
from app.services.graph_service import build_graph
from app.services.plan_service import get_plan

app = FastAPI()

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ideas")
async def create_idea(text: str = Query(...)):
    return {"idea_id": await ingest_idea(text)}

@app.get("/ideas/{idea_id}/questions")
async def questions(idea_id: str):
    return {"questions": await generate_questions(idea_id)}

@app.post("/ideas/{idea_id}/answers")
async def answers(idea_id: str, answers: dict):
    await submit_answers(idea_id, answers)
    return {"status": "saved"}

from app.services.graph_service import build_graph_with_llm

@app.get("/ideas/{idea_id}/graph")
async def graph(idea_id: str):
    return await build_graph_with_llm(idea_id)

@app.get("/ideas/{idea_id}/plan")
async def plan(idea_id: str):
    plan_obj = await get_plan(idea_id)
    return {"plan": plan_obj.markdown}
