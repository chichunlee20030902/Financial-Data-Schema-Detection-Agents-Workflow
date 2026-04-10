# config.py
ANTHROPIC_API_KEY = ""

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "schema_detection"
}

MODEL = "claude-opus-4-5"
MAX_TOKENS = 2048
MAX_REVIEW_ROUNDS = 3  # Supervisor 最多跟每個 Agent 討論幾輪
