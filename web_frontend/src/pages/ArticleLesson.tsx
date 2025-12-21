import { useState, useCallback } from "react";
import type { ChatMessage } from "../types/lesson";
import { sampleArticle } from "../data/sampleArticle";
import ArticlePanel from "../components/article/ArticlePanel";
import ChatPanel from "../components/article/ChatPanel";

type Layout = "horizontal" | "vertical";

export default function ArticleLesson() {
  const [layout, setLayout] = useState<Layout>("horizontal");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: `Welcome! You're about to read "${sampleArticle.title}" by ${sampleArticle.author}.\n\nBefore we begin, what do you already know about artificial general intelligence (AGI)? Have you thought about whether it's possible, and what it might mean if we built one?`,
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [articleBlurred, setArticleBlurred] = useState(false);

  const sendMessage = useCallback(
    async (content: string) => {
      const userMessage: ChatMessage = { role: "user", content };
      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      setIsLoading(true);

      try {
        const response = await fetch("/api/chat/lesson", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: updatedMessages,
            system_context: `You are a tutor helping someone read and understand the article "${sampleArticle.title}" by ${sampleArticle.author}.

The article presents four key claims:
1. General intelligence exists - humans have a real, general problem-solving ability
2. AI could surpass human intelligence - there's no fundamental barrier to building superintelligent machines
3. Superintelligent AI would shape the future - such systems would have immense influence
4. AI won't be beneficial by default - we need to solve alignment challenges

Ask probing questions to check comprehension. Help them think critically about the arguments. If they seem confused, clarify. If they're understanding well, push them to think deeper.

Keep responses concise (2-3 sentences typically). Be encouraging but intellectually rigorous.`,
          }),
        });

        if (!response.ok) throw new Error("Failed to send message");

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let assistantContent = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "text") {
                assistantContent += data.content;
              }
            } catch {
              // Skip invalid JSON
            }
          }
        }

        setMessages([
          ...updatedMessages,
          { role: "assistant", content: assistantContent },
        ]);
      } catch (error) {
        console.error("Error sending message:", error);
        setMessages([
          ...updatedMessages,
          {
            role: "assistant",
            content: "Sorry, something went wrong. Please try again.",
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [messages]
  );

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">
            Article Lesson Prototype
          </h1>
          <p className="text-sm text-gray-500">{sampleArticle.title}</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Layout toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Layout:</span>
            <div className="flex rounded-lg border border-gray-300 overflow-hidden">
              <button
                onClick={() => setLayout("horizontal")}
                className={`px-3 py-1 text-sm ${
                  layout === "horizontal"
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-700 hover:bg-gray-50"
                }`}
              >
                Horizontal
              </button>
              <button
                onClick={() => setLayout("vertical")}
                className={`px-3 py-1 text-sm ${
                  layout === "vertical"
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-700 hover:bg-gray-50"
                }`}
              >
                Vertical
              </button>
            </div>
          </div>
          {/* Blur toggle for testing */}
          <button
            onClick={() => setArticleBlurred(!articleBlurred)}
            className={`px-3 py-1 text-sm rounded-lg border ${
              articleBlurred
                ? "bg-yellow-100 border-yellow-300 text-yellow-800"
                : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
            }`}
          >
            {articleBlurred ? "Blurred" : "Blur (test)"}
          </button>
        </div>
      </header>

      {/* Main content */}
      {layout === "horizontal" ? (
        <div className="flex-1 flex overflow-hidden">
          {/* Chat panel - left */}
          <div className="w-1/2 border-r border-gray-200 bg-white">
            <ChatPanel
              messages={messages}
              onSendMessage={sendMessage}
              isLoading={isLoading}
            />
          </div>
          {/* Article panel - right */}
          <div className="w-1/2 bg-white relative">
            <ArticlePanel
              content={sampleArticle.content}
              title={sampleArticle.title}
              author={sampleArticle.author}
              date={sampleArticle.date}
              blurred={articleBlurred}
            />
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Article panel - top */}
          <div className="flex-1 border-b border-gray-200 bg-white relative overflow-hidden">
            <ArticlePanel
              content={sampleArticle.content}
              title={sampleArticle.title}
              author={sampleArticle.author}
              date={sampleArticle.date}
              blurred={articleBlurred}
            />
          </div>
          {/* Chat panel - bottom (fixed height) */}
          <div className="h-72 bg-white">
            <ChatPanel
              messages={messages}
              onSendMessage={sendMessage}
              isLoading={isLoading}
            />
          </div>
        </div>
      )}
    </div>
  );
}
