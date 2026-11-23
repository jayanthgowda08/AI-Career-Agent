"""
start.py — Production Entrypoint for Cloud Hosts (Render, Railway, Fly.io)

Guarantees binding to 0.0.0.0 on the host-assigned port (e.g. 10000 on Render)
without relying on shell variable expansion ($PORT).
"""
import os
import sys
import uvicorn

if __name__ == "__main__":
    port_str = os.environ.get("PORT", "10000")
    try:
        port = int(port_str)
    except ValueError:
        port = 10000

    print(f"🚀 Starting AI Career Agent on host 0.0.0.0, port {port} (Python {sys.version.split()[0]})...", flush=True)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
