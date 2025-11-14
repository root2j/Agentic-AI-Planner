import json
import os
import uuid
from typing import Union
from app.models import Idea, Plan

def _get_file_path(directory: str, idea_id: str, suffix: str = "") -> str:
    """Helper to construct file paths."""
    return os.path.join(directory, f"{idea_id}{suffix}.json")

def save_idea(idea: Idea, directory: str):
    """Saves an Idea object to a JSON file."""
    os.makedirs(directory, exist_ok=True)
    file_path = _get_file_path(directory, idea.id)
    with open(file_path, "w") as f:
        json.dump(idea.model_dump(), f, indent=4)

def load_idea(idea_id: str, directory: str) -> Union[Idea, None]:
    """Loads an Idea object from a JSON file."""
    file_path = _get_file_path(directory, idea_id)
    if not os.path.exists(file_path):
        print(f"DEBUG: Idea file not found at {file_path}")
        return None
    print(f"DEBUG: Loading idea from {file_path}")
    with open(file_path, "r") as f:
        data = json.load(f)
    return Idea(**data)

def save_plan_markdown(plan: Plan, directory: str):
    """Saves a Plan object's markdown content to a .md file."""
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"{plan.idea_id}.md")
    with open(file_path, "w") as f:
        f.write(plan.markdown)

def load_plan_markdown(idea_id: str, directory: str) -> Union[str, None]:
    """Loads plan markdown content from a .md file."""
    file_path = os.path.join(directory, f"{idea_id}.md")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r") as f:
        return f.read()
