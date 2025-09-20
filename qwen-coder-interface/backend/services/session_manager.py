import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json
import uuid
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manage user sessions and conversation history"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.cleanup_interval = 3600  # Clean up every hour
        self.session_timeout = 86400  # 24 hours
        self._cleanup_task = None
        
    async def get_or_create_session(self, session_id: Optional[str] = None) -> Dict:
        """Get existing session or create new one"""
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "id": session_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "context": [],
                "files": [],
                "working_directory": ".",
                "settings": {}
            }
            logger.info(f"Created new session: {session_id}")
        else:
            # Update last activity
            self.sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
        
        return self.sessions[session_id]
    
    async def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session data"""
        
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].update(updates)
        self.sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
        
        return True
    
    async def add_to_context(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add message to session context"""
        
        if session_id not in self.sessions:
            await self.get_or_create_session(session_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            message["metadata"] = metadata
        
        self.sessions[session_id]["context"].append(message)
        self.sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
        
        # Limit context size to prevent memory issues
        max_context_size = 50
        if len(self.sessions[session_id]["context"]) > max_context_size:
            self.sessions[session_id]["context"] = \
                self.sessions[session_id]["context"][-max_context_size:]
    
    async def get_context(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get session context"""
        
        if session_id not in self.sessions:
            return []
        
        context = self.sessions[session_id]["context"]
        
        if limit:
            return context[-limit:]
        
        return context
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        
        return False
    
    def active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
    
    async def cleanup_old_sessions(self):
        """Clean up expired sessions"""
        
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            last_activity = datetime.fromisoformat(session["last_activity"])
            
            if (current_time - last_activity).total_seconds() > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def start_cleanup_task(self):
        """Start background cleanup task"""
        
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval)
                    await self.cleanup_old_sessions()
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def cleanup(self):
        """Cleanup resources"""
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.sessions.clear()
        logger.info("Session manager cleaned up")