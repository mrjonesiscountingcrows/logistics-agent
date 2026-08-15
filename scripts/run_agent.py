import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent.loop import run_loop

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_agent.py <route_id>")
        sys.exit(1)
    run_loop(int(sys.argv[1]))