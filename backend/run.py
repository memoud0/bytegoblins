# run.py
from dotenv import load_dotenv

# 1. Load env vars first
load_dotenv()

# 2. THEN import app, so config.py sees the env vars
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
