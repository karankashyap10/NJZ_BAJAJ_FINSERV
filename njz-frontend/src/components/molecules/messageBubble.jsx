import React from "react";
import ReactMarkdown from "react-markdown";
import Avatar from "../atoms/avatar";
import Spinner from "../atoms/spinner";
import Timestamp from "../atoms/timestamp";

const MessageBubble = ({
  message,
  timestamp,
  sender = "user",
  isLoading = false,
}) => {
  const isUser = sender === "user";
  const isUpload = message.startsWith("📎 Uploaded file: ");
  return (
    <div className={`flex ${isUser ? "justify-end" : `${isUpload ? "justify-center" : "justify-start"}`} mb-4 w-full`}>
      <div
        className={`flex ${isUser ? "flex-row-reverse" : "flex-row"} max-w-2xl w-full`}
      >
        <Avatar name={sender} type={isUser ? "user" : "ai"} />
        <div className={`mx-3 flex-1 ${isUser ? "text-right" : "text-left"}`}>
          <div
            className={`inline-block px-5 py-3 rounded-2xl shadow ${isUser
              ? "bg-[#23232b] text-[#e5e7eb] border border-[#6366f1]"
              : "bg-[#23232b] text-[#a1a1aa] border border-[#23232b]"
              }`}
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <Spinner size="sm" />
                <span className="text-[#00fff7]">Thinking...</span>
              </div>
            ) : isUser ? (
              <div className="whitespace-pre-wrap">{message}</div>
            ) : (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown
                  components={{
                    // Custom styling for markdown elements
                    h1: ({ node, ...props }) => <h1 className="text-lg font-bold mb-2 text-[#e5e7eb]" {...props} />,
                    h2: ({ node, ...props }) => <h2 className="text-base font-bold mb-2 text-[#e5e7eb]" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-sm font-bold mb-1 text-[#e5e7eb]" {...props} />,
                    p: ({ node, ...props }) => <p className="mb-2 text-[#a1a1aa]" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-2 text-[#a1a1aa]" {...props} />,
                    ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-2 text-[#a1a1aa]" {...props} />,
                    li: ({ node, ...props }) => <li className="mb-1 text-[#a1a1aa]" {...props} />,
                    code: ({ node, inline, ...props }) =>
                      inline ? (
                        <code className="bg-[#2d2d30] text-[#00fff7] px-1 py-0.5 rounded text-xs" {...props} />
                      ) : (
                        <code className="block bg-[#2d2d30] text-[#00fff7] p-2 rounded text-xs overflow-x-auto" {...props} />
                      ),
                    pre: ({ node, ...props }) => <pre className="bg-[#2d2d30] p-2 rounded mb-2 overflow-x-auto" {...props} />,
                    blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-[#6366f1] pl-4 italic text-[#a1a1aa] mb-2" {...props} />,
                    strong: ({ node, ...props }) => <strong className="font-bold text-[#e5e7eb]" {...props} />,
                    em: ({ node, ...props }) => <em className="italic text-[#a1a1aa]" {...props} />,
                    a: ({ node, ...props }) => <a className="text-[#6366f1] hover:underline" {...props} />,
                    table: ({ node, ...props }) => <table className="border-collapse border border-[#2d2d30] mb-2" {...props} />,
                    th: ({ node, ...props }) => <th className="border border-[#2d2d30] px-2 py-1 text-[#e5e7eb] bg-[#2d2d30]" {...props} />,
                    td: ({ node, ...props }) => <td className="border border-[#2d2d30] px-2 py-1 text-[#a1a1aa]" {...props} />,
                  }}
                >
                  {message}
                </ReactMarkdown>
              </div>
            )}
          </div>
          <div className="mt-1 text-xs text-[#a1a1aa] opacity-80">
            <Timestamp date={timestamp} />
          </div>
        </div>
      </div>
    </div>
  );
};
export default MessageBubble;