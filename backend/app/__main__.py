"""`python -m app` — run the API on HOST:PORT (default 127.0.0.1:3001, as expected by the frontend)."""
import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT)
