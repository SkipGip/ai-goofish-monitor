"""Local-only Windows entrypoint; import app before configuring server logging."""
from src.app import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18080)
