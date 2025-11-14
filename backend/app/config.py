from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IDEAS_DIR = os.getenv("IDEAS_DIR", "data/ideas")
PLANS_DIR = os.getenv("PLANS_DIR", "data/plans")
