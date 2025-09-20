import asyncio
import subprocess
import os
import re
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
import shlex
import signal
import sys
from pathlib import Path

from utils.config import Settings

logger = logging.getLogger(__name__)

class TerminalService:
    """Service for managing terminal command execution"""
    
    def __init__(self):
        self.settings = Settings()
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self._ready = False
        
    async def initialize(self):
        """Initialize terminal service"""
        self._ready = True
        logger.info("Terminal service initialized")
    
    def is_ready(self) -> bool:
        """Check if service is ready"""
        return self._ready
    
    def _validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """Validate command for security"""
        
        # Check for forbidden patterns
        for pattern in self.settings.terminal_forbidden_patterns:
            if pattern in command:
                return False, f"Command contains forbidden pattern: {pattern}"
        
        # Extract base command
        try:
            parts = shlex.split(command)
            if not parts:
                return False, "Empty command"
            
            base_command = parts[0]
            
            # Check if command is in allowed list
            if self.settings.terminal_allowed_commands:
                # Check if base command or any parent command is allowed
                if base_command not in self.settings.terminal_allowed_commands:
                    # Check for commands with paths (e.g., /usr/bin/python)
                    command_name = os.path.basename(base_command)
                    if command_name not in self.settings.terminal_allowed_commands:
                        return False, f"Command '{base_command}' is not allowed"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid command format: {e}"
    
    async def execute_command(
        self,
        command: str,
        session_id: str,
        working_dir: str = None,
        env: Dict[str, str] = None,
        timeout: int = None
    ) -> Dict:
        """Execute a terminal command"""
        
        # Validate command
        is_valid, error_msg = self._validate_command(command)
        if not is_valid:
            return {
                "success": False,
                "error": error_msg,
                "output": "",
                "exit_code": -1
            }
        
        # Set working directory
        if working_dir and os.path.exists(working_dir):
            cwd = working_dir
        else:
            cwd = os.getcwd()
        
        # Prepare environment
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)
        
        # Set timeout
        timeout = timeout or self.settings.terminal_timeout
        
        try:
            # Run command asynchronously
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=cmd_env
            )
            
            # Store process for potential cancellation
            process_id = f"{session_id}_{datetime.now().timestamp()}"
            self.active_processes[process_id] = process
            
            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                # Decode output
                stdout_text = stdout.decode('utf-8', errors='replace')
                stderr_text = stderr.decode('utf-8', errors='replace')
                
                # Truncate if too long
                if len(stdout_text) > self.settings.terminal_max_output:
                    stdout_text = stdout_text[:self.settings.terminal_max_output] + "\n... [output truncated]"
                if len(stderr_text) > self.settings.terminal_max_output:
                    stderr_text = stderr_text[:self.settings.terminal_max_output] + "\n... [output truncated]"
                
                # Combine output
                output = stdout_text
                if stderr_text:
                    output += f"\n[stderr]:\n{stderr_text}"
                
                return {
                    "success": process.returncode == 0,
                    "output": output,
                    "exit_code": process.returncode,
                    "stdout": stdout_text,
                    "stderr": stderr_text
                }
                
            except asyncio.TimeoutError:
                # Kill process on timeout
                process.kill()
                await process.communicate()
                
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "output": "",
                    "exit_code": -1
                }
            finally:
                # Remove from active processes
                if process_id in self.active_processes:
                    del self.active_processes[process_id]
                
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "exit_code": -1
            }
    
    async def create_interactive_session(
        self,
        session_id: str,
        shell: str = "/bin/bash"
    ) -> Dict:
        """Create an interactive terminal session"""
        
        try:
            # Create a new process with PTY
            process = await asyncio.create_subprocess_exec(
                shell,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Store process
            self.active_processes[session_id] = process
            
            return {
                "success": True,
                "session_id": session_id,
                "pid": process.pid
            }
            
        except Exception as e:
            logger.error(f"Error creating interactive session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_to_session(
        self,
        session_id: str,
        input_data: str
    ) -> Optional[str]:
        """Send input to an interactive session"""
        
        if session_id not in self.active_processes:
            return None
        
        process = self.active_processes[session_id]
        
        try:
            # Send input
            process.stdin.write(input_data.encode())
            await process.stdin.drain()
            
            # Read output (non-blocking)
            output = await asyncio.wait_for(
                process.stdout.read(4096),
                timeout=0.1
            )
            
            return output.decode('utf-8', errors='replace')
            
        except asyncio.TimeoutError:
            return ""
        except Exception as e:
            logger.error(f"Error sending to session: {e}")
            return None
    
    async def kill_session(self, session_id: str) -> bool:
        """Kill an interactive session"""
        
        if session_id not in self.active_processes:
            return False
        
        process = self.active_processes[session_id]
        
        try:
            process.kill()
            await process.communicate()
            del self.active_processes[session_id]
            return True
        except Exception as e:
            logger.error(f"Error killing session: {e}")
            return False
    
    async def get_file_tree(
        self,
        path: str = ".",
        max_depth: int = 3,
        ignore_patterns: list = None
    ) -> Dict:
        """Get file tree structure"""
        
        ignore_patterns = ignore_patterns or [
            "__pycache__", ".git", "node_modules", ".venv", "venv"
        ]
        
        def should_ignore(name: str) -> bool:
            for pattern in ignore_patterns:
                if pattern in name:
                    return True
            return False
        
        def build_tree(current_path: Path, depth: int = 0) -> Dict:
            if depth >= max_depth:
                return None
            
            result = {
                "name": current_path.name,
                "path": str(current_path),
                "type": "directory" if current_path.is_dir() else "file"
            }
            
            if current_path.is_dir():
                children = []
                try:
                    for item in sorted(current_path.iterdir()):
                        if not should_ignore(item.name):
                            child = build_tree(item, depth + 1)
                            if child:
                                children.append(child)
                    result["children"] = children
                except PermissionError:
                    result["children"] = []
                    result["error"] = "Permission denied"
            else:
                # Add file info
                try:
                    stat = current_path.stat()
                    result["size"] = stat.st_size
                    result["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                except:
                    pass
            
            return result
        
        try:
            root_path = Path(path).resolve()
            if not root_path.exists():
                return {"error": "Path does not exist"}
            
            return build_tree(root_path)
            
        except Exception as e:
            logger.error(f"Error getting file tree: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        # Kill all active processes
        for session_id, process in list(self.active_processes.items()):
            try:
                process.kill()
                await process.communicate()
            except:
                pass
        
        self.active_processes.clear()
        self._ready = False
        logger.info("Terminal service cleaned up")