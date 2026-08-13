import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.db import init_db

if __name__ == "__main__":
    init_db()
    print("Database schema created.")
