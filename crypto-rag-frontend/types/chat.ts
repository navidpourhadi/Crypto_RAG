/**
 * Chat session interface for managing conversations
 */
export interface ChatSession {
  id: string;
  title?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Message interface for chat interactions
 */
export interface Message {
  content: string;
  role: "user" | "assistant";
  timestamp: string;
}

/**
 * Response for chat creation
 */
export interface ChatCreateResponse {
  chat_id: string;
  agent_response: string;
}

/**
 * Response for chat messages
 */
export interface ChatMessagesResponse {
  messages: Message[];
}

/**
 * Request to update chat properties
 */
export interface ChatUpdateRequest {
  title?: string;
}
