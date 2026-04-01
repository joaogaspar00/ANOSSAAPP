"""
run.py — Development entry point

In production, use gunicorn:
  gunicorn "run:app" --bind 0.0.0.0:8000 --workers 2
"""
import os
from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "default"))

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=app.config.get("DEBUG", False),
    )
