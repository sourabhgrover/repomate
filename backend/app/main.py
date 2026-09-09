"""FastAPI app factory and route registration.

Single-pass retrieval-and-generation service (CLAUDE.md: NOT an autonomous
multi-tool agent) — only /index, /status, and /chat are exposed.
"""

from fastapi import FastAPI


def create_app() -> FastAPI:
    ...
