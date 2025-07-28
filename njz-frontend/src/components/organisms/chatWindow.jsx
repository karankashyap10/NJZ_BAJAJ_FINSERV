import React, { useRef, useEffect } from "react";
import { MessageSquare } from "lucide-react";
import Icon from '../atoms/icons';
import MessageBubble from '../molecules/messageBubble';
import ChatInputBox from '../molecules/chatInputbox';
import ChatHeader from '../molecules/chatHeader';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const token = localStorage.getItem('accessToken');
  

const ChatWindow = ({ messages, isLoading, message, setMessage, onSendMessage, onFileUpload, files = [], onFileRemove, onShowGraph, onToggleSidebar, isSidebarCollapsed, disabled, selectedChatId, user, handleLogout }) => {
  const messagesEndRef = useRef(null);
  const [localMessages, setLocalMessages] = React.useState(messages);
  const [loading, setLoading] = React.useState(false);

  // Update local messages when parent messages change (when chat is selected)
  useEffect(() => {
    setLocalMessages(messages);
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [localMessages]);

  const handleSend = async () => {
    if (!message.trim() || !selectedChatId) return;
    
    const userMessage = {
      content: message,
      sender: 'user',
      timestamp: new Date()
    };
    
    // Add user message immediately for better UX
    setLocalMessages(prev => [...prev, userMessage]);
    setMessage('');
    setLoading(true);
    
    try {
      const res = await axios.post(`${API_BASE}/rag/chats/${selectedChatId}/query/`, { question: message }, {
        headers: {
          "Authorization":`Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      const aiMessage = {
        content: res.data.answer,
        sender: 'ai',
        timestamp: new Date()
      };
      
      // Add AI response to local messages
      setLocalMessages(prev => [...prev, aiMessage]);
      
      // Also update parent messages to keep them in sync
      if (onSendMessage) {
        onSendMessage([...localMessages, userMessage, aiMessage]);
      }
      
    } catch (err) {
      const errorMessage = {
        content: 'Error: Could not get answer from Gemini.',
        sender: 'ai',
        timestamp: new Date()
      };
      setLocalMessages(prev => [...prev, errorMessage]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-full">
      <ChatHeader
        onShowGraph={onShowGraph}
        onToggleSidebar={onToggleSidebar}
        isSidebarCollapsed={isSidebarCollapsed}
        user={user}
        handleLogout={handleLogout}
      />

      <div className="flex-1 overflow-y-auto p-8 bg-[#18181b]" style={{ borderLeft: '1px solid #23232b' }}>
        {localMessages.length === 0 ? (
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
            {localMessages.map((msg, index) => (
              <MessageBubble
                key={index}
                message={msg.content}
                timestamp={msg.timestamp}
                sender={msg.sender}
              />
            ))}
            {loading && (
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
        onSend={handleSend}
        onFileUpload={onFileUpload}
        files={files}
        onFileRemove={onFileRemove}
        disabled={false}
      />
    </div>
  );
};
export default ChatWindow