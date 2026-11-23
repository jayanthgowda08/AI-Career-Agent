"""
start.py — Root Production Entrypoint for Cloud Hosts (Render, Railway, Fly.io)

Ensures that whether Render runs commands from the repository root or from backend/,
the FastAPI application always imports cleanly and binds to 0.0.0.0 on $PORT.
"""
import os
import sys

# Ensure backend directory is in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")

if os.path.isdir(backend_dir) and backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import uvicorn

if __name__ == "__main__":
    port_str = os.environ.get("PORT", "10000")
    try:
        port = int(port_str)
    except ValueError:
        port = 10000

    print(f"🚀 Starting AI Career Agent on host 0.0.0.0, port {port} (Python {sys.version.split()[0]})...", flush=True)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
