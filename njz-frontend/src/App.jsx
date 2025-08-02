import { useState } from 'react'
import React from 'react';

import './App.css'
import FileUploadSidebar from './components/organisms/fileUploadSidebar';
import ChatWindow from './components/organisms/chatWindow';
import RAGGraphModal from './components/organisms/ragGraph';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

const API_BASE = 'http://localhost:8000';

function getAuthHeaders() {
  const token = localStorage.getItem('accessToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const App = () => {
  const [files, setFiles] = useState([]);
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGraphModalOpen, setIsGraphModalOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [selectedChatId, setSelectedChatId] = useState(null);
  const [graphData, setGraphData] = useState({});
  const [user, setUser] = useState(null);
  
  // Fetch chat history on mount
  React.useEffect(() => {
    async function fetchChats() {
      try {
        const res = await axios.get(`${API_BASE}/rag/chats/`, {
          headers: {
            ...getAuthHeaders(),
          },
        });
        setChatHistory(res.data.map(chat => ({
          id: chat.id,
          title: chat.name,
          messageCount: chat.messages ? chat.messages.length : 0,
          lastUpdated: chat.created_at
        })));
      } catch (err) {
        console.error(err);
      }
    }
    fetchChats();
  }, []);

  // Fetch user info from JWT after login
  React.useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      try {
        const decoded = jwtDecode(token);
        setUser({ username: decoded.username || decoded.user_name || decoded.email || 'User' });
      } catch (e) {
        setUser(null);
        console.error(e);
      }
    } else {
      setUser(null);
    }
  }, []);

  const handleCreateChat = async (chatName) => {
    try {
      const res = await axios.post(`${API_BASE}/rag/chats/`, { name: chatName }, {
        headers: {
          ...getAuthHeaders(),
        },
      });
      const chat = res.data;
      const newChatItem = {
        id: chat.id,
        title: chat.name,
        messageCount: chat.messages ? chat.messages.length : 0,
        lastUpdated: chat.created_at
      };
      
      // Add new chat to history
      setChatHistory(prev => [...prev, newChatItem]);
      
      // Automatically switch to the new chat and clear messages
      setSelectedChatId(chat.id);
      setMessages([]); // Clear messages for new chat
      
      console.log('Created and switched to new chat:', chat.id);
      
    } catch (err) {
      console.error('Error creating chat:', err);
      throw err; // Re-throw so the sidebar can handle the error state
    }
  };

  const handleFileUpload = async (newFiles) => {
    const validFiles = newFiles.filter(file =>
      file.type === 'application/pdf' ||
      file.name.endsWith('.docx')
    );
    setFiles(prev => [...prev, ...validFiles]);
    
    const uploadMessage = {
      content: `📎 Uploaded file: ${validFiles.map(file => file.name).join(', ')}`,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, uploadMessage]);
    
    // Send message to backend if a chat is selected
    if (selectedChatId) {
      try {
        await axios.post(`${API_BASE}/rag/chats/${selectedChatId}/messages/`, {
          content: uploadMessage.content,
          sender: uploadMessage.sender
        }, {
          headers: {
            ...getAuthHeaders(),
          },
        });
      } catch (err) {
        console.error('Error storing file upload message:', err);
      }
    }
  };

  const handleFileRemove = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleChatSelect = async (chatId) => {
    if (chatId === selectedChatId) return; // Don't reload if same chat
    
    setSelectedChatId(chatId);
    setMessages([]); // Clear messages while loading
    
    try {
      console.log('Fetching messages for chat:', chatId);
      const res = await axios.get(`${API_BASE}/rag/chats/${chatId}/messages/`, {
        headers: {
          ...getAuthHeaders(),
        },
      });
      console.log('Backend response:', res.data);
      const messages = res.data.messages || [];
      console.log('Parsed messages:', messages);
      
      // Convert backend message format to frontend format
      const parsedMessages = messages.map(msg => ({
        content: msg.content,
        sender: msg.sender,
        timestamp: new Date(msg.timestamp)
      }));
      console.log('Final parsed messages:', parsedMessages);
      setMessages(parsedMessages);
    } catch (err) {
      console.error('Error fetching chat messages:', err);
      setMessages([]);
    }
  };

  const handleSendMessage = (newMessages) => {
    setMessages(newMessages);
    // Update message count in chat history
    if (selectedChatId) {
      setChatHistory(prev => prev.map(chat =>
        chat.id === selectedChatId
          ? { ...chat, messageCount: newMessages.length, lastUpdated: new Date().toISOString() }
          : chat
      ));
    }
  };

  const handleToggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleShowGraph = async () => {
    if (!selectedChatId) return;
    try {
      const res = await axios.get(`${API_BASE}/rag/chats/${selectedChatId}/knowledge_graph/`, {
        headers: {
          ...getAuthHeaders(),
        },
      });
      setGraphData(res.data.graph_data || {});
    } catch (err) {
      setGraphData({ error: 'Could not fetch knowledge graph.' });
      console.error(err);
    }
    setIsGraphModalOpen(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setUser(null);
    window.location.reload();
  };

  return (
    <>
      <div className="fixed inset-0 flex w-screen h-screen bg-gray-100">
        <FileUploadSidebar
          files={files}
          onFileUpload={handleFileUpload}
          onFileRemove={handleFileRemove}
          chatHistory={chatHistory}
          onChatSelect={handleChatSelect}
          selectedChatId={selectedChatId}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={handleToggleSidebar}
          onCreateChat={handleCreateChat}
        />

        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            message={currentMessage}
            setMessage={setCurrentMessage}
            onSendMessage={handleSendMessage}
            onFileUpload={handleFileUpload}
            files={files}
            onFileRemove={handleFileRemove}
            onShowGraph={handleShowGraph}
            onToggleSidebar={handleToggleSidebar}
            isSidebarCollapsed={isSidebarCollapsed}
            disabled={files.length === 0}
            selectedChatId={selectedChatId}
            user={user}
            handleLogout={handleLogout}
            onCreateChat={handleCreateChat}
          />
        </div>

        <RAGGraphModal
          isOpen={isGraphModalOpen}
          onClose={() => setIsGraphModalOpen(false)}
          graphData={graphData}
        />
      </div>
    </>
  );
};

export default App;