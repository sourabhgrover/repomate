// Fetch wrappers for the backend's three routes: POST /index, GET /status, POST /chat.
// /chat is a single request/response call — no EventSource/SSE handling here,
// matching the backend's synchronous-only /chat contract.

const API_BASE_URL = (import.meta as any).env.VITE_API_URL || "http://127.0.0.1:8000";

export interface IndexRequest {
  owner: string;
  name: string;
  ref?: string;
}

export interface IndexResponse {
  job_id: string;
}

export interface StatusResponse {
  job_id: string;
  repo_id: string;
  status: string;
  files_processed: number;
  chunks_created: number;
  error_message: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface Citation {
  file_path: string;
  line_start: number;
  line_end: number;
  chunk_type: string;
  symbols: string[];
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
}

export async function startIndex(request: IndexRequest): Promise<IndexResponse> {
  const response = await fetch(`${API_BASE_URL}/index`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      owner: request.owner,
      name: request.name,
      ref: request.ref || "main",
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to start indexing: ${errorText}`);
  }

  return response.json();
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE_URL}/status?job_id=${encodeURIComponent(jobId)}`, {
    method: "GET",
    headers: {
      "Accept": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to get status: ${errorText}`);
  }

  return response.json();
}

export async function sendChat(
  repoId: string,
  question: string,
  chatHistory: ChatMessage[] = []
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      repo_id: repoId,
      question: question,
      chat_history: chatHistory,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `Chat request failed with status ${response.status}`);
  }

  return response.json();
}