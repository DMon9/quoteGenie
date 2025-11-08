"""Deprecated duplicate auth/payment endpoint definitions.

This file previously duplicated logic now consolidated inside `app.py`.
Intentionally left as a stub to avoid accidental re-import; safe to delete.
"""

# If imported accidentally, raise to indicate deprecated usage.
raise RuntimeError("auth_endpoints.py is deprecated. Use endpoints defined in app.py only.")
