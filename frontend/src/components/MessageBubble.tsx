import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage, Citation } from "../api/client";
import { CitationList } from "./CitationList";

export interface MessageBubbleProps {
  message: ChatMessage;
  citations?: Citation[];
}

export function MessageBubble({ message, citations }: MessageBubbleProps): JSX.Element {
  const isUser = message.role === "user";

  return (
    <div className={`message-bubble message-bubble--${message.role}`}>
      {/* Avatar / Role Label */}
      <div className="message-avatar">
        {isUser ? "🧑‍💻" : "🤖"}
      </div>

      {/* Message Content */}
      <div className="message-content">
        <div className="message-role">
          {isUser ? "You" : "RepoMate"}
        </div>

        {/* Dynamic formatted content: paragraphs, bullet points, tables, code blocks */}
        <div className="message-text">
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Citations shown only on assistant messages */}
        {!isUser && citations && citations.length > 0 && (
          <CitationList citations={citations} />
        )}
      </div>
    </div>
  );
}