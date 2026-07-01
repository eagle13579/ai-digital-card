"""API Version Redirect Middleware.

Rewrites /api/v1/xxx -> /api/xxx at ASGI scope level for unregistered v1 paths.
Adds Sunset/Deprecation headers for all v1-style requests.

For explicitly registered v1 endpoints (in v1_deprecated.py), the path is NOT
rewritten but deprecation headers are still added.
"""

from __future__ import annotations

# V1 endpoints explicitly registered in the app — these will NOT be rewritten
_EXPLICIT_V1_PREFIXES = frozenset({
    "/api/v1/users",
    "/api/v1/brochures",
})


class APIVersionRedirectMiddleware:
    """Rewrite /api/v1/xxx -> /api/xxx at ASGI scope level.
    For explicitly registered v1 endpoints, the path is preserved and
    deprecated headers are added. For all other v1 paths, they're rewritten
    to the corresponding /api/ path and deprecation headers are added.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]

            if path.startswith("/api/v1/"):
                is_explicit = any(
                    path.startswith(prefix)
                    for prefix in _EXPLICIT_V1_PREFIXES
                )

                if not is_explicit:
                    # Rewrite to /api/ version
                    scope["path"] = "/api/" + path[8:]
                    scope["raw_path"] = scope["path"].encode()

                # Wrap send to inject deprecation headers
                original_send = send

                async def _send(message):
                    if message["type"] == "http.response.start":
                        headers = list(message.get("headers", []))
                        headers.append(
                            (b"sunset", b"Sat, 01 Jan 2027 00:00:00 GMT")
                        )
                        headers.append((b"deprecation", b"true"))
                        headers.append(
                            (b"link", b'</api/v2/brochures>; rel="successor-version"')
                        )
                        message["headers"] = headers
                    await original_send(message)

                return await self.app(scope, receive, _send)

        await self.app(scope, receive, send)
