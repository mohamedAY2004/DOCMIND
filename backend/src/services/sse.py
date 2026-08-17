"""Small Server-Sent Events encoder shared by POST streaming routes."""
from __future__ import annotations

import json
from typing import Any


def encode_sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, separators=(',', ':'))}\n\n"
