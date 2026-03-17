"""Configuration management for File Master."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration."""
    
    # Bailian/Qwen API
    api_key: str = ""
    api_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    model: str = "qwen-plus"
    
    # PDF processing
    max_file_size_mb: int = 100  # Maximum file size in MB
    max_pages_per_request: int = 20  # Max pages per AI request
    chunk_overlap_pages: int = 2  # Page overlap between chunks
    
    # Processing limits
    default_max_pages: int = 50  # Default max pages to process
    hard_max_pages: int = 200  # Absolute maximum
    
    # Timeouts
    api_timeout_seconds: int = 60
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            api_base_url=os.getenv(
                "DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/api/v1"
            ),
            model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
            max_file_size_mb=int(os.getenv("PDF_MAX_FILE_SIZE_MB", "100")),
            max_pages_per_request=int(os.getenv("PDF_MAX_PAGES_PER_REQUEST", "20")),
        )


# Global config instance
config = Config.from_env()
