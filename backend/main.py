# ============================================================
# ReplicarIA - Main Entry Point for Railway/ASGI Servers
# ============================================================
# This file exists for compatibility with ASGI servers that
# look for "main:app" by default (like Railway's auto-detection).
# The actual application is defined in server.py
# ============================================================

from server import app

# Re-export app for uvicorn/gunicorn
__all__ = ["app"]
