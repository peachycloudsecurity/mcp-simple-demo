#!/usr/bin/env python3
"""
Application configuration using dataclasses for type safety and validation.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
_project_root = Path(__file__).parent.parent
load_dotenv(dotenv_path=_project_root / '.env')


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for the Large Language Model backend."""
    api_endpoint: str = field(default_factory=lambda: os.getenv("LLM_API_ENDPOINT", "http://localhost:11434"))
    model_name: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "llama3.2:1b"))
    request_timeout: int = field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT", "120")))


@dataclass(frozen=True)
class ServerConfig:
    """Configuration for the tool server component."""
    identifier: str = field(default_factory=lambda: os.getenv("SERVER_ID", "tool-execution-server"))
    host: str = field(default_factory=lambda: os.getenv("SERVER_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("SERVER_PORT", "8765")))


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration container."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    data_directory: Path = field(default_factory=lambda: _project_root / "data")
    
    def __post_init__(self):
        # Ensure data directory exists
        self.data_directory.mkdir(exist_ok=True)


# Singleton configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Retrieve the application configuration singleton."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """Force reload of configuration from environment."""
    global _config
    _config = AppConfig()
    return _config
