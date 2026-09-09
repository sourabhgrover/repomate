// Fetch wrappers for the backend's three routes: POST /index, GET /status, POST /chat.
// /chat is a single request/response call — no EventSource/SSE handling here,
// matching the backend's synchronous-only /chat contract.

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
  throw new Error("not implemented");
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  throw new Error("not implemented");
}

export async function sendChat(
  repoId: string,
  question: string,
  chatHistory: ChatMessage[]
): Promise<ChatResponse> {
  throw new Error("not implemented");
}
