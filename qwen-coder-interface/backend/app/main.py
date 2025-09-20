from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import logging
from typing import Dict, List
import json
import os
from datetime import datetime

from routes.chat import chat_router
from routes.terminal import terminal_router
from routes.files import files_router
from services.model_service import ModelService
from services.terminal_service import TerminalService
from services.session_manager import SessionManager
from utils.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = Settings()

# Create FastAPI app
app = FastAPI(
    title="Qwen Coder Interface",
    description="Web interface for Qwen2.5-Coder with terminal access",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
model_service = ModelService()
terminal_service = TerminalService()
session_manager = SessionManager()

# Store active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}

# Include routers
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(terminal_router, prefix="/api/terminal", tags=["terminal"])
app.include_router(files_router, prefix="/api/files", tags=["files"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Qwen Coder Interface...")
    try:
        # Initialize model service
        await model_service.initialize()
        logger.info("Model service initialized successfully")
        
        # Initialize terminal service
        await terminal_service.initialize()
        logger.info("Terminal service initialized successfully")
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Qwen Coder Interface...")
    await model_service.cleanup()
    await terminal_service.cleanup()
    await session_manager.cleanup()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Qwen Coder Interface",
        "version": "1.0.0",
        "status": "running",
        "model": "Qwen2.5-Coder-7B-Instruct",
        "features": ["chat", "terminal", "file_operations"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "model": model_service.is_ready(),
            "terminal": terminal_service.is_ready(),
            "sessions": session_manager.active_sessions_count()
        }
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Main WebSocket endpoint for real-time communication"""
    await websocket.accept()
    
    # Register connection
    if session_id not in active_connections:
        active_connections[session_id] = []
    active_connections[session_id].append(websocket)
    
    # Create or get session
    session = await session_manager.get_or_create_session(session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Route message based on type
            response = await handle_websocket_message(message, session_id, session)
            
            # Send response
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        # Remove connection
        active_connections[session_id].remove(websocket)
        if not active_connections[session_id]:
            del active_connections[session_id]
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        await websocket.close()

async def handle_websocket_message(message: dict, session_id: str, session: dict) -> dict:
    """Handle incoming WebSocket messages"""
    msg_type = message.get("type")
    
    try:
        if msg_type == "chat":
            # Handle chat message
            response = await model_service.generate_response(
                prompt=message.get("content"),
                context=session.get("context", []),
                stream=True
            )
            return {"type": "chat_response", "content": response}
            
        elif msg_type == "terminal":
            # Handle terminal command
            command = message.get("command")
            result = await terminal_service.execute_command(
                command=command,
                session_id=session_id,
                working_dir=message.get("working_dir", os.getcwd())
            )
            return {"type": "terminal_output", "output": result}
            
        elif msg_type == "code_complete":
            # Handle code completion request
            code = message.get("code")
            position = message.get("position")
            suggestions = await model_service.get_code_completions(code, position)
            return {"type": "code_suggestions", "suggestions": suggestions}
            
        elif msg_type == "file_operation":
            # Handle file operations
            operation = message.get("operation")
            path = message.get("path")
            content = message.get("content")
            
            if operation == "read":
                with open(path, 'r') as f:
                    file_content = f.read()
                return {"type": "file_content", "path": path, "content": file_content}
            elif operation == "write":
                with open(path, 'w') as f:
                    f.write(content)
                return {"type": "file_saved", "path": path, "success": True}
                
        else:
            return {"type": "error", "message": f"Unknown message type: {msg_type}"}
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        return {"type": "error", "message": str(e)}

async def broadcast_to_session(session_id: str, message: dict):
    """Broadcast message to all connections in a session"""
    if session_id in active_connections:
        for connection in active_connections[session_id]:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove dead connections
                active_connections[session_id].remove(connection)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)