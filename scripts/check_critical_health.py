#!/usr/bin/env python3
"""
Deployment guard: fail fast when critical backend health is unsafe.
Exits non-zero if /health/critical is not HTTP 200.
"""

from __future__ import annotations

import json
import os
import sys
from urllib import request, error


def main() -> int:
    base = os.getenv("BACKEND_URL", "http://localhost:8080")
    url = f"{base.rstrip('/')}/health/critical"
    try:
        with request.urlopen(url, timeout=8) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body) if body else {}
            print(json.dumps({"url": url, "http_status": resp.status, "status": data.get("status")}))
            return 0 if resp.status == 200 else 1
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(json.dumps({"url": url, "http_status": exc.code, "error": body[:500]}))
        return 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"url": url, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

