from pydantic import BaseSettings, Field
from typing import Optional, List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Qwen Coder Interface"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Model settings
    model_name: str = Field(default="Qwen/Qwen2.5-Coder-7B-Instruct", env="MODEL_NAME")
    model_device: str = Field(default="cuda" if os.path.exists("/usr/local/cuda") else "cpu", env="MODEL_DEVICE")
    model_max_length: int = Field(default=32768, env="MODEL_MAX_LENGTH")
    model_cache_dir: Optional[str] = Field(default="./model_cache", env="MODEL_CACHE_DIR")
    use_quantization: bool = Field(default=False, env="USE_QUANTIZATION")
    
    # Terminal settings
    terminal_max_output: int = Field(default=10000, env="TERMINAL_MAX_OUTPUT")
    terminal_timeout: int = Field(default=30, env="TERMINAL_TIMEOUT")
    terminal_allowed_commands: List[str] = Field(
        default=[
            "ls", "pwd", "cd", "cat", "echo", "grep", "find", 
            "python", "pip", "npm", "node", "git", "docker"
        ],
        env="TERMINAL_ALLOWED_COMMANDS"
    )
    terminal_forbidden_patterns: List[str] = Field(
        default=["rm -rf /", "sudo", "chmod 777", "curl | bash"],
        env="TERMINAL_FORBIDDEN_PATTERNS"
    )
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database
    database_url: Optional[str] = Field(default="sqlite:///./sessions.db", env="DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default=["*"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    # Agency Swarm integration
    enable_agency_swarm: bool = Field(default=True, env="ENABLE_AGENCY_SWARM")
    agency_swarm_model: str = Field(default="gpt-5", env="AGENCY_SWARM_MODEL")
    
    # Jetson specific settings
    is_jetson: bool = Field(default=os.path.exists("/etc/nv_tegra_release"), env="IS_JETSON")
    use_tensorrt: bool = Field(default=False, env="USE_TENSORRT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'