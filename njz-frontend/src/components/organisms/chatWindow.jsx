import React, { useRef, useEffect } from "react";
import { MessageSquare } from "lucide-react";
import Icon from '../atoms/icons';
import MessageBubble from '../molecules/messageBubble';
import ChatInputBox from '../molecules/chatInputbox';
import ChatHeader from '../molecules/chatHeader';

const ChatWindow = ({ messages, isLoading, message, setMessage, onSendMessage, onFileUpload, onShowGraph, onToggleSidebar, isSidebarCollapsed, disabled }) => {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <ChatHeader
        onShowGraph={onShowGraph}
        onToggleSidebar={onToggleSidebar}
        isSidebarCollapsed={isSidebarCollapsed}
      />

      <div className="flex-1 overflow-y-auto p-8 bg-[#18181b]" style={{ borderLeft: '1px solid #23232b' }}>
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Icon icon={MessageSquare} size="lg" className="text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No messages yet
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Upload some documents and start asking questions!
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => (
              <MessageBubble
                key={index}
                message={msg.content}
                timestamp={msg.timestamp}
                sender={msg.sender}
              />
            ))}
            {isLoading && (
              <MessageBubble
                message=""
                timestamp={new Date()}
                sender="ai"
                isLoading={true}
              />
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <ChatInputBox
        message={message}
        setMessage={setMessage}
        onSend={onSendMessage}
        onFileUpload={onFileUpload}
        disabled={disabled}
      />
    </div>
  );
};
export default ChatWindow