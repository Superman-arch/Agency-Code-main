from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict, List
import logging
import json

from services.terminal_service import TerminalService

logger = logging.getLogger(__name__)

terminal_router = APIRouter()
terminal_service = TerminalService()

class CommandRequest(BaseModel):
    command: str
    session_id: Optional[str] = None
    working_dir: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None

class CommandResponse(BaseModel):
    success: bool
    output: str
    exit_code: int
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error: Optional[str] = None

@terminal_router.post("/execute", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """Execute a terminal command"""
    
    try:
        result = await terminal_service.execute_command(
            command=request.command,
            session_id=request.session_id or "default",
            working_dir=request.working_dir,
            env=request.env,
            timeout=request.timeout
        )
        
        return CommandResponse(**result)
        
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@terminal_router.post("/session/create")
async def create_terminal_session(session_id: Optional[str] = None):
    """Create an interactive terminal session"""
    
    try:
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        result = await terminal_service.create_interactive_session(session_id)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating terminal session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@terminal_router.delete("/session/{session_id}")
async def kill_terminal_session(session_id: str):
    """Kill a terminal session"""
    
    try:
        success = await terminal_service.kill_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session killed", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error killing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@terminal_router.get("/file-tree")
async def get_file_tree(
    path: str = ".",
    max_depth: int = 3,
    ignore_patterns: Optional[List[str]] = None
):
    """Get file tree structure"""
    
    try:
        tree = await terminal_service.get_file_tree(
            path=path,
            max_depth=max_depth,
            ignore_patterns=ignore_patterns
        )
        
        return tree
        
    except Exception as e:
        logger.error(f"Error getting file tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@terminal_router.websocket("/ws/{session_id}")
async def terminal_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for interactive terminal"""
    
    await websocket.accept()
    
    try:
        # Create terminal session
        result = await terminal_service.create_interactive_session(session_id)
        
        if not result["success"]:
            await websocket.send_json({"type": "error", "message": result.get("error")})
            await websocket.close()
            return
        
        await websocket.send_json({
            "type": "session_created",
            "session_id": session_id,
            "pid": result.get("pid")
        })
        
        # Handle terminal I/O
        while True:
            # Receive input from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "input":
                # Send input to terminal
                output = await terminal_service.send_to_session(
                    session_id=session_id,
                    input_data=message["data"]
                )
                
                if output:
                    await websocket.send_json({
                        "type": "output",
                        "data": output
                    })
            
            elif message["type"] == "resize":
                # Handle terminal resize (if needed)
                pass
            
            elif message["type"] == "kill":
                # Kill session
                await terminal_service.kill_session(session_id)
                await websocket.send_json({"type": "session_killed"})
                break
                
    except WebSocketDisconnect:
        # Clean up session on disconnect
        await terminal_service.kill_session(session_id)
        logger.info(f"Terminal WebSocket disconnected for session {session_id}")
        
    except Exception as e:
        logger.error(f"Terminal WebSocket error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()