"""Configuration settings for NEXUS."""

import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    falkordb_host: str = os.getenv("FALKORDB_HOST", "localhost")
    falkordb_port: int = int(os.getenv("FALKORDB_PORT", "6379"))
    falkordb_password: str | None = os.getenv("FALKORDB_PASSWORD", None)
    falkordb_graph_name: str = os.getenv("FALKORDB_GRAPH_NAME", "company_brain")

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY", None)
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    force_embedded: bool = os.getenv("FORCE_EMBEDDED", "false").lower() in ("true", "1", "yes")


settings = Settings()
