from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _path_env(name: str, default: str) -> Path:
    return Path(os.getenv(name, default)).expanduser().resolve()


@dataclass(frozen=True)
class Settings:
    db_path: Path = _path_env("LOVDATA_DB_PATH", "./data/lovdata.sqlite3")
    public_api_base_url: str = os.getenv(
        "LOVDATA_PUBLIC_API_BASE_URL", "https://api.lovdata.no"
    ).rstrip("/")
    pro_gateway_url: str = os.getenv("LOVDATA_PRO_GATEWAY_URL", "").rstrip("/")
    pro_gateway_token: str = os.getenv("LOVDATA_PRO_GATEWAY_TOKEN", "")
    pro_search_path: str = os.getenv("LOVDATA_PRO_SEARCH_PATH", "/v1/search")
    pro_document_path: str = os.getenv(
        "LOVDATA_PRO_DOCUMENT_PATH", "/v1/documents/{document_id}"
    )
    actions_api_key: str = os.getenv("LOVDATA_ACTIONS_API_KEY", "")
    host: str = os.getenv("MCP_HOST", "0.0.0.0")
    port: int = int(os.getenv("MCP_PORT", "8000"))


settings = Settings()
