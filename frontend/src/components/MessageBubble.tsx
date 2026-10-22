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

        {/* Render answer text — preserve newlines and code blocks */}
        <div className="message-text">
          {message.content.split("\n").map((line, index) => (
            <span key={index}>
              {line}
              <br />
            </span>
          ))}
        </div>

        {/* Citations shown only on assistant messages */}
        {!isUser && citations && citations.length > 0 && (
          <CitationList citations={citations} />
        )}
      </div>
    </div>
  );
}