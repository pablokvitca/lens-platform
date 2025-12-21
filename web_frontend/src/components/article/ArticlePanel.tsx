import ReactMarkdown from "react-markdown";

type ArticlePanelProps = {
  content: string;
  title?: string;
  author?: string;
  date?: string;
  blurred?: boolean; // For active recall - blur the content
};

export default function ArticlePanel({
  content,
  title,
  author,
  date,
  blurred = false,
}: ArticlePanelProps) {
  return (
    <div className="h-full overflow-y-auto">
      <article className={`prose prose-gray max-w-none p-6 ${blurred ? "blur-sm select-none" : ""}`}>
        {title && <h1 className="text-2xl font-bold mb-2">{title}</h1>}
        {(author || date) && (
          <div className="text-sm text-gray-500 mb-6">
            {author && <span>{author}</span>}
            {author && date && <span> · </span>}
            {date && <span>{date}</span>}
          </div>
        )}
        <ReactMarkdown
          components={{
            // Style links
            a: ({ children, href }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                {children}
              </a>
            ),
            // Style headings
            h1: ({ children }) => (
              <h1 className="text-2xl font-bold mt-8 mb-4">{children}</h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-xl font-bold mt-6 mb-3">{children}</h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-lg font-bold mt-5 mb-2">{children}</h3>
            ),
            h4: ({ children }) => (
              <h4 className="text-base font-bold mt-4 mb-2">{children}</h4>
            ),
            // Style paragraphs
            p: ({ children }) => (
              <p className="mb-4 leading-relaxed">{children}</p>
            ),
            // Style lists
            ul: ({ children }) => (
              <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>
            ),
            // Style emphasis
            strong: ({ children }) => (
              <strong className="font-semibold">{children}</strong>
            ),
            em: ({ children }) => (
              <em className="italic">{children}</em>
            ),
            // Style blockquotes
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-gray-300 pl-4 italic my-4">
                {children}
              </blockquote>
            ),
            // Style horizontal rules
            hr: () => <hr className="my-8 border-gray-300" />,
          }}
        >
          {content}
        </ReactMarkdown>
      </article>

      {blurred && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/50">
          <div className="bg-yellow-100 border border-yellow-300 rounded-lg px-4 py-2 text-yellow-800">
            Answer the question to reveal the article
          </div>
        </div>
      )}
    </div>
  );
}
