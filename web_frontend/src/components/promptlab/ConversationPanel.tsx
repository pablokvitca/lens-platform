import { useState, useRef, useEffect } from "react";
import ChatMarkdown from "@/components/ChatMarkdown";

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
  isRegenerated?: boolean;
  originalContent?: string;
  thinkingContent?: string;
}

interface ConversationPanelProps {
  messages: ConversationMessage[];
  selectedMessageIndex: number | null;
  streamingContent: string;
  streamingThinking: string;
  isStreaming: boolean;
  onSelectMessage: (index: number) => void;
  onRegenerate: () => void;
  onSendFollowUp: (message: string) => void;
  canRegenerate: boolean;
  canSendFollowUp: boolean;
}

/**
 * Right panel of the Prompt Lab: conversation display with message selection,
 * regeneration, original/new comparison, chain-of-thought, and follow-up input.
 */
export default function ConversationPanel({
  messages,
  selectedMessageIndex,
  streamingContent,
  streamingThinking,
  isStreaming,
  onSelectMessage,
  onRegenerate,
  onSendFollowUp,
  canRegenerate,
  canSendFollowUp,
}: ConversationPanelProps) {
  const [followUpInput, setFollowUpInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Track which original messages are expanded (by index)
  const [expandedOriginals, setExpandedOriginals] = useState<Set<number>>(
    new Set(),
  );
  // Track which thinking sections are expanded (by index)
  const [expandedThinking, setExpandedThinking] = useState<Set<number>>(
    new Set(),
  );

  // Auto-scroll when streaming
  useEffect(() => {
    if (isStreaming && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [isStreaming, streamingContent, streamingThinking]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      const maxHeight = 120;
      textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
      textarea.style.overflowY =
        textarea.scrollHeight > maxHeight ? "auto" : "hidden";
    }
  }, [followUpInput]);

  function toggleOriginal(index: number) {
    setExpandedOriginals((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }

  function toggleThinking(index: number) {
    setExpandedThinking((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }

  function handleSendFollowUp(e: React.FormEvent) {
    e.preventDefault();
    const text = followUpInput.trim();
    if (text && canSendFollowUp && !isStreaming) {
      onSendFollowUp(text);
      setFollowUpInput("");
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendFollowUp(e);
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h2 className="text-sm font-semibold text-slate-700">Conversation</h2>
        {canRegenerate && (
          <button
            onClick={onRegenerate}
            disabled={isStreaming}
            className={`text-xs font-medium px-3 py-1.5 rounded transition-colors ${
              isStreaming
                ? "bg-slate-100 text-slate-400 cursor-default"
                : "bg-blue-600 text-white hover:bg-blue-700"
            }`}
          >
            Regenerate from selected
          </button>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, index) => {
          const isSelected = selectedMessageIndex === index;
          const isDimmed =
            selectedMessageIndex !== null && index > selectedMessageIndex;
          const isAssistant = msg.role === "assistant";

          return (
            <div
              key={index}
              className={`transition-opacity ${isDimmed ? "opacity-40" : ""}`}
            >
              {/* Original content (collapsed by default, only for regenerated messages) */}
              {msg.isRegenerated && msg.originalContent && (
                <div className="mb-2">
                  <button
                    onClick={() => toggleOriginal(index)}
                    className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition-colors mb-1"
                  >
                    <svg
                      className={`w-3 h-3 transition-transform ${expandedOriginals.has(index) ? "rotate-90" : ""}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                    Original response
                  </button>
                  {expandedOriginals.has(index) && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-500">
                      <ChatMarkdown>{msg.originalContent}</ChatMarkdown>
                    </div>
                  )}
                </div>
              )}

              {/* Message bubble */}
              <div
                onClick={() => {
                  if (isAssistant && !isStreaming) {
                    onSelectMessage(index);
                  }
                }}
                className={`p-3 rounded-lg ${
                  isAssistant
                    ? `bg-blue-50 text-gray-800 ${
                        !isStreaming ? "cursor-pointer hover:bg-blue-100" : ""
                      }`
                    : "bg-gray-100 text-gray-800 ml-8"
                } ${
                  isSelected
                    ? "ring-2 ring-blue-400"
                    : ""
                }`}
              >
                <div className="text-xs text-gray-500 mb-1">
                  {isAssistant ? "Tutor" : "Student"}
                  {isAssistant && !isStreaming && (
                    <span className="ml-2 text-gray-300">
                      click to select
                    </span>
                  )}
                </div>
                <div
                  className={isAssistant ? "" : "whitespace-pre-wrap"}
                >
                  {isAssistant ? (
                    <ChatMarkdown>{msg.content}</ChatMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>

              {/* Chain-of-thought (collapsed by default, only for regenerated messages) */}
              {msg.isRegenerated && msg.thinkingContent && (
                <div className="mt-2">
                  <button
                    onClick={() => toggleThinking(index)}
                    className="flex items-center gap-1.5 text-xs text-amber-600 hover:text-amber-700 transition-colors"
                  >
                    <svg
                      className={`w-3 h-3 transition-transform ${expandedThinking.has(index) ? "rotate-90" : ""}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                    Show reasoning
                  </button>
                  {expandedThinking.has(index) && (
                    <div className="mt-1 bg-amber-50 border border-amber-200 rounded-lg p-3 font-mono text-xs text-amber-900 whitespace-pre-wrap leading-relaxed">
                      {msg.thinkingContent}
                    </div>
                  )}
                </div>
              )}

              {/* Dimmed indicator */}
              {isDimmed && index === (selectedMessageIndex ?? 0) + 1 && (
                <div className="text-xs text-slate-400 mt-1 text-center">
                  Messages below will be replaced
                </div>
              )}
            </div>
          );
        })}

        {/* Streaming indicator */}
        {isStreaming && (
          <div>
            {/* Streaming thinking */}
            {streamingThinking && !streamingContent && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-3">
                <div className="text-xs text-amber-600 mb-1">Thinking...</div>
                <div className="font-mono text-xs text-amber-900 whitespace-pre-wrap leading-relaxed">
                  {streamingThinking}
                </div>
              </div>
            )}

            {/* Streaming response */}
            {streamingContent ? (
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Tutor</div>
                <div>
                  <ChatMarkdown>{streamingContent}</ChatMarkdown>
                </div>
              </div>
            ) : !streamingThinking ? (
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Tutor</div>
                <div className="text-gray-400">Generating...</div>
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* Follow-up input */}
      <form
        onSubmit={handleSendFollowUp}
        className="flex gap-2 p-3 border-t border-gray-200 items-end"
      >
        <textarea
          ref={textareaRef}
          value={followUpInput}
          onChange={(e) => setFollowUpInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Send a follow-up message as the student..."
          disabled={!canSendFollowUp || isStreaming}
          rows={1}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none leading-normal disabled:bg-gray-50 disabled:text-gray-400"
        />
        <button
          type="submit"
          disabled={!canSendFollowUp || isStreaming || !followUpInput.trim()}
          className="bg-blue-600 text-white text-sm px-3 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-default transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}
