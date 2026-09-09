import type { ChatMessage, Citation } from "../api/client";

export interface MessageBubbleProps {
  message: ChatMessage;
  citations?: Citation[];
}

export function MessageBubble(props: MessageBubbleProps): JSX.Element {
  throw new Error("not implemented");
}
