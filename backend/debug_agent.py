import os
import sys

# Ensure backend root is in path
sys.path.append(os.getcwd())

try:
    from app.services.research import ResearchAgent

    print(f"Has select_layout: {hasattr(ResearchAgent, 'select_layout')}")
    agent = ResearchAgent()
    print(f"Instance has select_layout: {hasattr(agent, 'select_layout')}")
except Exception as e:
    print(f"Error: {e}")
