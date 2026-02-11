"""
FastAPI backend server with REST + WebSocket support.
Handles symptom analysis, follow-up questions, and streaming LLM responses.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from models import (
    SymptomRequest,
    FollowupQuestionsRequest,
    FollowupQuestionsResponse,
    AnalysisRequest,
    AnalysisResponse,
    HealthResponse
)
from chatbot import analyze
from adaptive_questions import generate_followup_questions
from logger import get_logger
from llm import get_llm
from config import (
    HOST,
    PORT,
    DEBUG,
    ENABLE_CORS,
    ALLOWED_ORIGINS,
    RATE_LIMIT_PER_MINUTE,
    SESSION_TIMEOUT_MINUTES,
    MAX_FOLLOWUP_QUESTIONS
)

logger = get_logger(__name__)

# ============= RATE LIMITING =============
limiter = Limiter(key_func=get_remote_address)

# ============= SESSION STORAGE =============
_sessions: Dict[str, Dict] = {}
sessions_lock = asyncio.Lock()
RECEIVE_TIMEOUT = 60.0 # 60 seconds timeout for websocket receive


async def get_or_create_session(session_id: str) -> Dict:
    """Get or create a user session."""
    async with sessions_lock:
        if session_id not in _sessions:
            _sessions[session_id] = {
                "created_at": datetime.now(),
                "messages": [],
                "initial_symptoms": None,
                "followup_answers": [],
                "analysis_result": None
            }
        else:
            # Check timeout
            age = datetime.now() - _sessions[session_id]["created_at"]
            if age > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                logger.info(f"⏰ Session {session_id} expired after {SESSION_TIMEOUT_MINUTES} min")
                _sessions[session_id] = {
                    "created_at": datetime.now(),
                    "messages": [],
                    "initial_symptoms": None,
                    "followup_answers": [],
                    "analysis_result": None
                }
        
        return _sessions[session_id]


async def cleanup_expired_sessions():
    """Background task to cleanup expired sessions."""
    while True:
        await asyncio.sleep(60 * 5) # Run every 5 minutes
        async with sessions_lock:
            now = datetime.now()
            expired_ids = [
                sid for sid, data in _sessions.items()
                if now - data["created_at"] > timedelta(minutes=SESSION_TIMEOUT_MINUTES)
            ]
            for sid in expired_ids:
                del _sessions[sid]
            if expired_ids:
                logger.info(f"🧹 Cleaned up {len(expired_ids)} expired sessions")


# ============= LIFESPAN (Startup/Shutdown) =============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Carenova API starting up...")
    
    # Startup
    cleanup_task = asyncio.create_task(cleanup_expired_sessions())
    try:
        llm = get_llm()  # Test LLM connectivity
        logger.info("✅ LLM connection verified")
    except Exception as e:
        logger.warning(f"⚠️  LLM not yet available: {e}")
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    logger.info("🛑 Carenova API shutting down...")


# ============= FASTAPI APP =============
app = FastAPI(
    title="Carenova AI Health Assistant API",
    description="RAG-based medical guidance system with streaming support",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    """Handle rate limit exceedances."""
    return JSONResponse(
        status_code=429,
        content={"error": f"Rate limit exceeded: {exc.detail}"}
    )

app.state.limiter = limiter


# ============= MIDDLEWARE =============
if ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ============= ROUTES =============
@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serve index.html for static frontend."""
    if not Path("static/index.html").exists():
        return JSONResponse(
            status_code=404,
            content={"error": "Frontend not found. Run: mkdir -p static"}
        )
    return FileResponse("static/index.html")


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check for load balancers and uptime monitoring."""
    try:
        from config import FAISS_INDEX_DIR
        llm = get_llm()
        vector_db_ready = Path(FAISS_INDEX_DIR).exists()
        return HealthResponse(
            status="healthy" if vector_db_ready else "degraded",
            message="All systems operational" if vector_db_ready else "Vector database missing",
            models_loaded=True,
            vector_db_ready=vector_db_ready
        )
    except Exception as e:
        logger.warning(f"⚠️  Health check failed: {e}")
        return HealthResponse(
            status="degraded",
            message=f"Service partially unavailable: {str(e)}",
            models_loaded=False,
            vector_db_ready=False
        )


@app.post(
    "/followup-questions",
    response_model=FollowupQuestionsResponse,
    tags=["Chat"],
    summary="Generate adaptive follow-up questions",
    responses={
        200: {"description": "Questions generated successfully"},
        400: {"description": "Invalid input"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def get_followup_questions(request: FollowupQuestionsRequest):
    """
    Generate intelligent follow-up questions based on initial symptoms.
    
    These questions help differentiate between conditions.
    """
    try:
        logger.info(f"📝 Generating follow-ups for: {request.symptoms[:50]}...")
        
        questions = generate_followup_questions(request.symptoms)
        
        # Validate response
        if not isinstance(questions, list) or len(questions) == 0:
            logger.warning(f"⚠️  Invalid followup response: {questions}")
            raise ValueError("Failed to generate valid questions")
        
        # Limit questions
        questions = questions[:MAX_FOLLOWUP_QUESTIONS]
        
        logger.info(f"✅ Generated {len(questions)} questions")
        return FollowupQuestionsResponse(questions=questions)
    
    except Exception as e:
        logger.error(f"❌ Followup generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate follow-up questions"
        )


@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    tags=["Chat"],
    summary="Analyze symptoms and provide guidance",
    responses={
        200: {"description": "Analysis complete"},
        400: {"description": "Invalid input"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Analysis failed"}
    }
)
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def analyze_symptoms(request: AnalysisRequest):
    """
    Comprehensive symptom analysis using RAG.
    
    Combines initial symptoms + follow-up answers for more accurate guidance.
    """
    try:
        logger.info(f"💬 Analyzing {len(request.followup_answers)} response(s)...")
        
        # Combine all input
        combined_text = (
            request.initial_symptoms + " | "
            + " | ".join(request.followup_answers)
        )
        
        # Run analysis off the loop
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, analyze, combined_text)
        
        logger.info(f"✅ Analysis returned: {result.get('severity')}")
        return AnalysisResponse(**result)
    
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze symptoms"
        )


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat interactions.
    
    Client sends: {
        "session_id": "unique-id",
        "initial_symptoms": "...",
        "followup_answers": ["...", "..."]
    }
    
    Server streams:
    {
        "type": "thinking",
        "content": "Analyzing your symptoms..."
    },
    {
        "type": "analysis",
        "data": {...}
    }
    """
    await websocket.accept()
    logger.info(f"🔗 WebSocket connected: {websocket.client}")
    try:
        try:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=RECEIVE_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("🕒 WebSocket receive timeout")
            await websocket.close()
            return
        
        session_id = data.get("session_id", "default")
        initial_symptoms = data.get("initial_symptoms", "")
        followup_answers = data.get("followup_answers", [])
        
        # Validate input
        if not initial_symptoms or len(initial_symptoms) < 5:
            await websocket.send_json({
                "type": "error",
                "message": "Symptoms must be at least 5 characters"
            })
            await websocket.close()
            return
        
        logger.info(f"💬 Session {session_id}: Analyzing {len(followup_answers)} answers")
        
        # Get or create session
        session = await get_or_create_session(session_id)
        session["initial_symptoms"] = initial_symptoms
        session["followup_answers"] = followup_answers
        
        # Stream thinking message
        await websocket.send_json({
            "type": "thinking",
            "content": "🧠 Analyzing your symptoms..."
        })
        
        # Brief async pause for UI feedback
        await asyncio.sleep(0.3)
        
        # Run analysis off the loop
        combined_text = (
            initial_symptoms + " | " + " | ".join(followup_answers)
        )
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, analyze, combined_text)
        
        # Store in session
        session["analysis_result"] = result
        
        # Stream analysis result
        await websocket.send_json({
            "type": "analysis",
            "data": result
        })
        
        logger.info(f"✅ WebSocket analysis complete for {session_id}")
    
    except json.JSONDecodeError:
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid JSON received"
            })
        except:
            pass
    
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Server error during analysis"
            })
        except:
            pass
    
    finally:
        try:
            await websocket.close()
        except:
            pass


@app.get(
    "/api-docs",
    tags=["Documentation"],
    summary="OpenAPI specification"
)
async def get_docs():
    """Get OpenAPI schema for API documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Carenova API",
        version="1.0.0",
        description="Medical guidance system with RAG",
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# ============= ERROR HANDLERS =============
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all error handler."""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# ============= MAIN =============
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Starting Carenova API on {HOST}:{PORT}")
    logger.info(f"📖 Docs available at http://{HOST}:{PORT}/docs")
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info" if not DEBUG else "debug"
    )
