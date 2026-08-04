from __future__ import annotations

import uuid


def unique_name(prefix: str, feature: str) -> str:
    return f"{prefix}{feature}-{uuid.uuid4().hex[:8]}"
