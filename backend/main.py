# ============================================================
# ReplicarIA - Main Entry Point for Railway/ASGI Servers
# ============================================================

import sys
import os

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from server import app
    print("✅ Successfully imported app from server.py")
except Exception as e:
    print(f"❌ Failed to import app from server: {e}")
    import traceback
    traceback.print_exc()

    # Create a minimal fallback app for debugging
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/")
    def error_info():
        return {"error": "Failed to load main app", "details": str(e)}

    @app.get("/health")
    def health():
        return {"status": "error", "message": "App failed to load"}

# Re-export app for uvicorn/gunicorn
__all__ = ["app"]
