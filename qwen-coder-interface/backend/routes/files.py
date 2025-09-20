from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

files_router = APIRouter()

class FileOperation(BaseModel):
    path: str
    content: Optional[str] = None
    operation: str  # read, write, delete, rename

class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    is_directory: bool
    modified: str
    mime_type: Optional[str] = None

@files_router.post("/read")
async def read_file(file_op: FileOperation):
    """Read a file"""
    
    try:
        file_path = Path(file_op.path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Check file size
        file_size = file_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10MB
        
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "path": str(file_path),
            "content": content,
            "size": file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@files_router.post("/write")
async def write_file(file_op: FileOperation):
    """Write to a file"""
    
    try:
        if file_op.content is None:
            raise HTTPException(status_code=400, detail="Content is required")
        
        file_path = Path(file_op.path)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_op.content)
        
        return {
            "path": str(file_path),
            "success": True,
            "size": len(file_op.content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@files_router.post("/delete")
async def delete_file(file_op: FileOperation):
    """Delete a file or directory"""
    
    try:
        file_path = Path(file_op.path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Safety check - don't delete system directories
        restricted_paths = ["/", "/usr", "/etc", "/var", "/bin", "/sbin", "/lib"]
        if str(file_path) in restricted_paths:
            raise HTTPException(status_code=403, detail="Cannot delete system directories")
        
        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            file_path.unlink()
        
        return {
            "path": str(file_path),
            "success": True,
            "message": "File deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@files_router.post("/rename")
async def rename_file(old_path: str, new_path: str):
    """Rename or move a file"""
    
    try:
        old = Path(old_path)
        new = Path(new_path)
        
        if not old.exists():
            raise HTTPException(status_code=404, detail="Source file not found")
        
        if new.exists():
            raise HTTPException(status_code=400, detail="Destination already exists")
        
        # Create parent directories if needed
        new.parent.mkdir(parents=True, exist_ok=True)
        
        # Move/rename
        old.rename(new)
        
        return {
            "old_path": str(old),
            "new_path": str(new),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@files_router.get("/list")
async def list_directory(path: str = ".", show_hidden: bool = False):
    """List directory contents"""
    
    try:
        dir_path = Path(path)
        
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        files = []
        for item in sorted(dir_path.iterdir()):
            # Skip hidden files if requested
            if not show_hidden and item.name.startswith('.'):
                continue
            
            try:
                stat = item.stat()
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "size": stat.st_size if item.is_file() else 0,
                    "is_directory": item.is_dir(),
                    "modified": stat.st_mtime
                })
            except:
                # Skip files we can't stat
                continue
        
        return {
            "path": str(dir_path),
            "files": files,
            "count": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@files_router.post("/upload")
async def upload_file(file: UploadFile = File(...), path: str = "."):
    """Upload a file"""
    
    try:
        # Validate path
        upload_dir = Path(path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@files_router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a file"""
    
    try:
        path = Path(file_path)
        
        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        return FileResponse(
            path=str(path),
            filename=path.name,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))