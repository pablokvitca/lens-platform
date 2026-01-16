// web_frontend_next/src/components/narrative-lesson/NarrativeChatSection.tsx
"use client";

import { useState, useRef, useLayoutEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage, PendingMessage } from "@/types/unified-lesson";

type NarrativeChatSectionProps = {
  messages: ChatMessage[];
  pendingMessage: PendingMessage | null;
  streamingContent: string;
  isLoading: boolean;
  onSendMessage: (content: string) => void;
  onRetryMessage?: () => void;
};

/**
 * Chat section for NarrativeLesson with 75vh max height.
 * All instances share the same state (passed via props).
 *
 * Simplified from ChatPanel - no recording, no transition buttons.
 * Just messages + input.
 */
export default function NarrativeChatSection({
  messages,
  pendingMessage,
  streamingContent,
  isLoading,
  onSendMessage,
  onRetryMessage,
}: NarrativeChatSectionProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useLayoutEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Filter out system messages for display
  const visibleMessages = messages.filter((m) => m.role !== "system");

  return (
    <div className="max-w-[700px] mx-auto py-4 px-4">
      <div
        className="border border-gray-200 rounded-lg bg-white shadow-sm flex flex-col"
        style={{ maxHeight: "75vh" }}
      >
        {/* Messages area */}
        <div
          ref={scrollContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4"
        >
          {visibleMessages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-4 py-2 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-900"
                }`}
              >
                {msg.role === "assistant" ? (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
            </div>
          ))}

          {/* Pending user message */}
          {pendingMessage && (
            <div className="flex justify-end">
              <div
                className={`max-w-[85%] rounded-lg px-4 py-2 ${
                  pendingMessage.status === "failed"
                    ? "bg-red-100 text-red-800 border border-red-200"
                    : "bg-blue-600 text-white opacity-70"
                }`}
              >
                <p className="whitespace-pre-wrap">{pendingMessage.content}</p>
                {pendingMessage.status === "failed" && onRetryMessage && (
                  <button
                    onClick={onRetryMessage}
                    className="text-red-600 text-sm underline mt-1"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Streaming response */}
          {streamingContent && (
            <div className="flex justify-start">
              <div className="max-w-[85%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900">
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {streamingContent}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          )}

          {/* Loading indicator */}
          {isLoading && !streamingContent && (
            <div className="flex justify-start">
              <div className="rounded-lg px-4 py-2 bg-gray-100">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  />
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4">
          <div className="flex gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              rows={1}
              className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-default"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
