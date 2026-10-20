"""Synchronous /chat route. No SSE/streaming per CLAUDE.md MVP scope."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.app.dependencies import get_conversational_chain

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
def chat(request: ChatRequest) -> ChatResponse:
  """Synchronously answers technical questions using hybrid retrieval and code citations."""
  if not request.question.strip():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Question cannot be empty.",
    )

  try:
    # 1. Obtain repository-scoped conversational chain
    chain = get_conversational_chain(repo_id=request.repo_id)

    # 2. Format chat history into list of (user_msg, assistant_msg) tuples
    history_tuples = []
    user_msg = None
    for msg in request.chat_history:
      if msg.role == "user":
        user_msg = msg.content
      elif msg.role == "assistant" and user_msg is not None:
        history_tuples.append((user_msg, msg.content))
        user_msg = None

    # 3. Ask the chain
    result = chain.ask(question=request.question, chat_history=history_tuples)

    # 4. Map citations to response models
    citations = [
        CitationResponse(
            file_path=c.file_path,
            line_start=c.line_start,
            line_end=c.line_end,
            chunk_type=c.chunk_type,
            symbols=c.symbols,
        )
        for c in result.citations
    ]

    return ChatResponse(answer=result.answer, citations=citations)

  except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error processing question: {str(e)}",
    ) from e