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

class GraphEditRequest(BaseModel):
    user_text_input: str
