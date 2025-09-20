from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging

from services.model_service import ModelService
from services.session_manager import SessionManager

logger = logging.getLogger(__name__)

chat_router = APIRouter()

# Initialize services (these will be injected from main app)
model_service = ModelService()
session_manager = SessionManager()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[List[Dict]] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tokens_used: Optional[int] = None

class CodeAnalysisRequest(BaseModel):
    code: str
    analysis_type: str = "review"  # review, explain, optimize, debug
    session_id: Optional[str] = None

class CodeCompletionRequest(BaseModel):
    code: str
    position: Dict[str, int]  # line and column
    num_suggestions: Optional[int] = 3

@chat_router.post("/generate", response_model=ChatResponse)
async def generate_response(request: ChatRequest):
    """Generate a response from the model"""
    
    try:
        # Get or create session
        session = await session_manager.get_or_create_session(request.session_id)
        session_id = session["id"]
        
        # Add user message to context
        await session_manager.add_to_context(
            session_id=session_id,
            role="user",
            content=request.message
        )
        
        # Get full context
        context = request.context or await session_manager.get_context(session_id)
        
        # Generate response
        response = await model_service.generate_response(
            prompt=request.message,
            context=context,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            stream=False
        )
        
        # Add assistant response to context
        await session_manager.add_to_context(
            session_id=session_id,
            role="assistant",
            content=response
        )
        
        return ChatResponse(
            response=response,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/analyze-code")
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code for improvements or issues"""
    
    try:
        # Get or create session
        session = await session_manager.get_or_create_session(request.session_id)
        session_id = session["id"]
        
        # Perform analysis
        analysis = await model_service.analyze_code(
            code=request.code,
            analysis_type=request.analysis_type
        )
        
        # Add to context
        await session_manager.add_to_context(
            session_id=session_id,
            role="user",
            content=f"Analyze this code ({request.analysis_type}):\n```\n{request.code}\n```"
        )
        
        await session_manager.add_to_context(
            session_id=session_id,
            role="assistant",
            content=analysis["analysis"]
        )
        
        return {
            "analysis": analysis,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error analyzing code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/complete")
async def get_code_completion(request: CodeCompletionRequest):
    """Get code completion suggestions"""
    
    try:
        suggestions = await model_service.get_code_completions(
            code=request.code,
            position=request.position,
            num_suggestions=request.num_suggestions
        )
        
        return {
            "suggestions": suggestions,
            "position": request.position
        }
        
    except Exception as e:
        logger.error(f"Error getting completions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/sessions/{session_id}/context")
async def get_session_context(session_id: str, limit: Optional[int] = None):
    """Get conversation context for a session"""
    
    try:
        context = await session_manager.get_context(session_id, limit)
        
        return {
            "session_id": session_id,
            "context": context,
            "count": len(context)
        }
        
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a session"""
    
    try:
        success = await session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session cleared", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))