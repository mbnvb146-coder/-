#!/usr/bin/env python3
"""Startup entry point — prints diagnostics then launches uvicorn."""
import os
import sys

PORT = os.environ.get("PORT", "8000")

print(f"[start] PORT={PORT}", flush=True)
print(f"[start] Python {sys.version}", flush=True)
print(f"[start] cwd={os.getcwd()}", flush=True)
print(f"[start] files={os.listdir('.')}", flush=True)

# Verify critical imports before handing off to uvicorn
try:
    import fastapi, uvicorn, pycapcut
    print("[start] core imports OK", flush=True)
except Exception as e:
    print(f"[start] IMPORT ERROR: {e}", flush=True)
    sys.exit(1)

os.execvp("python3", [
    "python3", "-m", "uvicorn",
    "agent.server:app",
    "--host", "0.0.0.0",
    "--port", PORT,
    "--log-level", "info",
])
