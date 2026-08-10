import logging
import time
import uuid
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .agent import MockAgent
from .logging_config import configure_logging
from .security import enforce_rate_limit, require_api_key
from .settings import get_settings

configure_logging()
logger = logging.getLogger("cloud_ai_agent")
START_TIME = time.time()
agent = MockAgent()
app = FastAPI(title="Cloud AI Agent Starter", version=get_settings().app_version)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="User question")


class AskResponse(BaseModel):
    request_id: str
    answer: str
    citations: list[str]
    latency_ms: int
    tokens_estimated: int


@app.middleware("http")
async def add_request_id_and_log(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start = time.time()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", extra={"request_id": request_id, "path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": request_id})
    latency_ms = int((time.time() - start) * 1000)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "latency_ms": latency_ms,
            "status_code": response.status_code,
            "client": request.client.host if request.client else "unknown",
        },
    )
    return response


@app.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME),
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/ready")
def ready():
    settings = get_settings()
    checks = {
        "api_key_configured": bool(settings.app_api_key),
        "mock_agent_loaded": agent is not None,
        "port_from_env": settings.port > 0,
    }
    status = "ready" if all(checks.values()) else "not_ready"
    return {"status": status, "checks": checks}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, request: Request, api_key: str = Depends(require_api_key)):
    settings = get_settings()
    enforce_rate_limit(request, api_key)
    if len(payload.question) > settings.max_question_chars:
        raise HTTPException(status_code=413, detail="Question too long. Cost guard rejected this request.")

    start = time.time()
    result = agent.answer(payload.question)
    latency_ms = int((time.time() - start) * 1000)
    return AskResponse(
        request_id=request.state.request_id,
        answer=result.answer,
        citations=result.citations,
        latency_ms=latency_ms,
        tokens_estimated=result.tokens_estimated,
    )
