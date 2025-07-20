import React from "react";
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

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 w-full`}>
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
            ) : (
              <div className="whitespace-pre-wrap">{message}</div>
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