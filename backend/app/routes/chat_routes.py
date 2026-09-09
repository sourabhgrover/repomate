"""Synchronous /chat route. No SSE/streaming per CLAUDE.md MVP scope."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    repo_id: str
    question: str
    chat_history: list[ChatMessage] = []


class CitationResponse(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    chunk_type: str
    symbols: list[str]


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, chain_factory=Depends(...)) -> ChatResponse:
    ...
