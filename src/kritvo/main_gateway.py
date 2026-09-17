"""WhatsApp gateway process: webhooks and the Flow data endpoint (TASK-013, LLD 6).

Run locally: uv run uvicorn kritvo.main_gateway:app --port 8001 --reload
"""

from fastapi import FastAPI

from kritvo.core.app_factory import build_app


def create_app() -> FastAPI:
    # No CORS: only Meta calls this process. Webhook routes arrive in TASK-013.
    return build_app("Kritvo WhatsApp Gateway", enable_cors=False)


app = create_app()
