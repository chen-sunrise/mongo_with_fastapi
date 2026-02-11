import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "test-secret-key-should-be-at-least-32-chars")
os.environ.setdefault("MONGO_DB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB_DATABASE", "test_db")
os.environ.setdefault("MONGO_DB_USER_COLLECTION", "users")
os.environ.setdefault("MONGO_DB_ITEM_COLLECTION", "items")
