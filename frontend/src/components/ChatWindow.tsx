// Minimal chat + citations UI (CLAUDE.md: no streaming inspector or Mermaid
// viewer in MVP scope). Sends one synchronous request per turn via api/client.

import { useState, useRef, useEffect } from "react";
import type { ChatMessage, Citation } from "../api/client";
import { sendChat } from "../api/client";
import { MessageBubble } from "./MessageBubble";

export interface ChatWindowProps {
  repoId: string;
}

interface MessageWithCitations {
  message: ChatMessage;
  citations?: Citation[];
}

export function ChatWindow({ repoId }: ChatWindowProps): JSX.Element {
  const [messages, setMessages] = useState<MessageWithCitations[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom whenever messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const question = inputText.trim();
    if (!question || isLoading) return;

    // Build chat history for the API (list of prior turns)
    const chatHistory: ChatMessage[] = messages.map((m) => m.message);

    // Optimistically add the user message to the thread
    const userMessage: ChatMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, { message: userMessage }]);
    setInputText("");
    setIsLoading(true);
    setError(null);

    try {
      // Single synchronous request/response — no SSE per CLAUDE.md
      const response = await sendChat(repoId, question, chatHistory);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.answer,
      };

      setMessages((prev) => [
        ...prev,
        { message: assistantMessage, citations: response.citations },
      ]);
    } catch (err: any) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Send on Enter (not Shift+Enter)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chat-window">
      {/* Message Thread */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>💬 Ask a question about <strong>{repoId}</strong>!</p>
            <p className="chat-empty-hint">
              e.g. "How does routing work?" or "Where is authentication defined?"
            </p>
          </div>
        )}

        {messages.map((item, index) => (
          <MessageBubble
            key={index}
            message={item.message}
            citations={item.citations}
          />
        ))}

        {/* Loading indicator while waiting for the backend */}
        {isLoading && (
          <div className="chat-loading">
            <span>🤖 RepoMate is thinking...</span>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="chat-error">
            ⚠️ {error}
          </div>
        )}

        {/* Invisible anchor div to scroll to bottom */}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div className="chat-input-area">
        <textarea
          className="chat-input"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`Ask a question about ${repoId}...`}
          rows={2}
          disabled={isLoading}
        />
        <button
          className="chat-send-btn"
          onClick={handleSend}
          disabled={isLoading || !inputText.trim()}
        >
          {isLoading ? "..." : "Send ➤"}
        </button>
      </div>
    </div>
  );
}