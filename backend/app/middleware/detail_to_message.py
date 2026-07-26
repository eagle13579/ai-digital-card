"""
Middleware: adds `message` field to JSON error responses for backward compat.

v4: properly updates Content-Length when body is modified.
Buffers start + body, modifies if needed, then sends both.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


class DetailToMessageMiddleware:
    """ASGI middleware: ensures `message` field in JSON error responses."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        status_code = 200
        resp_headers: list[tuple[bytes, bytes]] = []
        body_chunks: list[bytes] = []

        async def send_wrapper(message):
            nonlocal status_code, resp_headers, body_chunks

            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                resp_headers = message.get("headers", [])
                # Don't forward yet — buffer until we have the full body

            elif message["type"] == "http.response.body":
                chunk = message.get("body", b"")
                if chunk:
                    body_chunks.append(chunk)

                if message.get("more_body", False):
                    return  # Wait for more chunks

                # Full body received — decide what to send
                body_bytes = b"".join(body_chunks)

                if status_code >= 400 and _is_json(resp_headers) and body_bytes:
                    try:
                        data = json.loads(body_bytes)
                        if isinstance(data, dict) and "detail" in data and "message" not in data:
                            data["message"] = data["detail"]
                            body_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
                            # Update Content-Length
                            resp_headers = [
                                (k, v) if k.lower() != b"content-length"
                                else (k, str(len(body_bytes)).encode())
                                for k, v in resp_headers
                            ]
                    except (json.JSONDecodeError, Exception):
                        pass

                # Send start + body together
                await send({
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": resp_headers,
                })
                await send({
                    "type": "http.response.body",
                    "body": body_bytes,
                    "more_body": False,
                })

            else:
                await send(message)

        await self.app(scope, receive, send_wrapper)


def _is_json(headers: list[tuple[bytes, bytes]]) -> bool:
    for k, v in headers:
        if k.lower() == b"content-type" and b"application/json" in v.lower():
            return True
    return False
