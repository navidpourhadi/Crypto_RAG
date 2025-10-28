"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { ArrowUp, Square } from "lucide-react";
import {
  Message as ChatMessageComponent,
  MessageContent,
} from "@/app/chat/components/ChatMessage";
import {
  PromptInput,
  PromptInputTextarea,
  PromptInputActions,
} from "@/app/chat/components/PromptInput";
import Sidebar from "@/app/chat/components/Sidebar";
import type { ChatSession, Message } from "@/types/chat";
import { authenticatedApi, publicApi } from "@/lib/api/axiosInstances";
import { Bitcoin } from "lucide-react";

export default function Chat() {
  // State management
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isLoadingAnswer, setIsLoadingAnswer] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFetchingChats, setIsFetchingChats] = useState(true);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Function to focus the textarea
  const focusTextarea = useCallback(() => {
    if (textareaRef.current) {
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 0);
    }
  }, []);

  // Focus textarea after sending a message and receiving a response
  useEffect(() => {
    if (!isLoadingAnswer && !isSubmitting) {
      focusTextarea();
    }
  }, [isLoadingAnswer, isSubmitting, focusTextarea]);

  // Fetch all chat sessions
  const getChatSessions = useCallback(async () => {
    setIsFetchingChats(true);
    setError(null);

    try {
      const response = await publicApi.get("/chat/");
      const chats = Array.isArray(response.data)
        ? response.data
        : response.data.chats;
      setChatSessions(chats || []);
    } catch (error) {
      console.error("Error fetching chats:", error);
      setError("Failed to load your chat history. Please try again.");
      setChatSessions([]);
    } finally {
      setIsFetchingChats(false);
    }
  }, []);

  // Load on initial render
  useEffect(() => {
    getChatSessions();
    focusTextarea();
  }, [getChatSessions, focusTextarea]);

  // Load chat history for a specific chat
  const loadChatMessages = useCallback(
    async (chatId: string) => {
      setIsLoadingHistory(true);
      setError(null);
      focusTextarea();

      try {
        const response = await authenticatedApi.get(`/chat/${chatId}`);
        setMessages(response.data);
        setActiveChatId(chatId);
      } catch (error) {
        console.error("Error loading chat messages:", error);
        setError("Failed to load chat messages. Please try again.");
      } finally {
        setIsLoadingHistory(false);
      }
    },
    [focusTextarea]
  );

  // Common function to send messages for both new and existing chats
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isSubmitting) return;
      setError(null);
      setIsSubmitting(true);
      setIsLoadingAnswer(true);

      // Create optimistic user message for immediate UI feedback
      const userMessage: Message = {
        content,
        role: "user",
        timestamp: new Date().toISOString(),
      };

      const isNewChat = !activeChatId;

      // Update UI optimistically
      setMessages((prev) =>
        isNewChat ? [userMessage] : [...prev, userMessage]
      );
      setInputValue("");

      try {
        // Use the same API pattern for both endpoints
        const response = await authenticatedApi.post(
          activeChatId ? `/chat/${activeChatId}` : "/chat/",
          null,
          {
            params: { user_message: content },
          }
        );

        // Create assistant message from response
        const assistantMessage: Message = {
          content: response.data.agent_response,
          role: "assistant",
          timestamp: new Date().toISOString(),
        };

        // Update messages in UI
        if (isNewChat) {
          setMessages([userMessage, assistantMessage]);
          // For new chats, set the active chat ID and refresh the list
          await getChatSessions();
          setActiveChatId(response.data.chat_id);
        } else {
          setMessages((prev) => [...prev, assistantMessage]);
        }
      } catch (error) {
        console.error("Error in chat:", error);
        setError("Failed to send message. Please try again.");

        // Remove the optimistic message if the request failed
        setMessages((prev) => (isNewChat ? [] : prev.slice(0, -1)));
      } finally {
        setIsLoadingAnswer(false);
        setIsSubmitting(false);
      }
    },
    [activeChatId, getChatSessions, isSubmitting]
  );

  // Handle starting a new chat
  const handleNewChat = useCallback(() => {
    setActiveChatId(null);
    setMessages([]);
    setError(null);
    focusTextarea();

    if (inputValue.trim()) {
      sendMessage(inputValue);
    }
  }, [inputValue, sendMessage, focusTextarea]);

  return (
    <div className="relative min-h-screen w-full flex bg-[#212121]">
      <Sidebar
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        chatSessions={chatSessions}
        onNewChat={handleNewChat}
        activeChatId={activeChatId}
        onChatSelect={loadChatMessages}
        isLoading={isFetchingChats}
      />

      <main className="flex-1 flex flex-col h-screen overflow-auto">
        <div style={{ padding: "20px 0 0 20px" }}>
          <Bitcoin size={32} className="inline-block " color="#f3ab24ff" />
          <h1 className="inline-block ml-2 text-2xl font-bold">Crypto AI</h1>
        </div>
        <div className="max-w-5xl mx-auto w-full flex-1 flex flex-col p-4 lg:p-8">
          {error && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-white text-sm">
              {error}
            </div>
          )}

          <div className="flex-1 overflow-y-auto mb-4 space-y-4">
            {isLoadingHistory ? (
              <div className="h-full flex items-center justify-center">
                <p className="text-gray-400">Loading conversation...</p>
              </div>
            ) : messages.length === 0 ? (
              <div className="h-full flex items-center justify-left pl-30 ">
                <p className="text-[#ddd] text-xl">
                  I am your{" "}
                  <strong className="text-3xl text-[#f3ab24ff]">
                    Crypto AI
                  </strong>{" "}
                  assistant. <br />
                  Let's talk about the market of Cryptocurrencies!
                </p>
              </div>
            ) : (
              messages.map((message, index) => (
                <ChatMessageComponent
                  key={`${message.timestamp}-${index}`}
                  className={`${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <MessageContent
                    markdown
                    className={`${
                      message.role === "user"
                        ? "bg-[#aaaaaa22]"
                        : "bg-[#f3ab2422]"
                    } text-white`}
                  >
                    {message.content}
                  </MessageContent>
                </ChatMessageComponent>
              ))
            )}
          </div>

          <div className="sticky bottom-0 pt-2 max-w-3xl mx-auto w-full">
            <PromptInput
              isLoading={isLoadingAnswer || isSubmitting}
              maxHeight={250}
              onSubmit={() => sendMessage(inputValue)}
              className="bg-[#333333] border-white/20 border-2 
                hover:border-white/50 focus-within:border-white/50"
            >
              <PromptInputTextarea
                placeholder="Ask me..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isLoadingAnswer || isSubmitting}
                ref={textareaRef}
              />
              <PromptInputActions className="justify-end pt-2">
                <button
                  onClick={() => sendMessage(inputValue)}
                  disabled={
                    !inputValue.trim() || isLoadingAnswer || isSubmitting
                  }
                  className="h-8 w-8 rounded-full bg-white flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoadingAnswer ? (
                    <Square className="size-5 fill-current text-black" />
                  ) : (
                    <ArrowUp className="size-5 text-black" />
                  )}
                </button>
              </PromptInputActions>
            </PromptInput>
          </div>
        </div>
      </main>
    </div>
  );
}
