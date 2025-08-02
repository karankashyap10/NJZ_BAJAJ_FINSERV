import React from "react";
import { ChevronRight, Upload, MessageSquare, ChevronLeft } from "lucide-react";
import Icon from '../atoms/icons';
import Button from '../atoms/buttons';
import Divider from '../atoms/divider';
import FileUploadField from '../molecules/fileUpload';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const token = localStorage.getItem('accessToken');
console.log(token);


const FileUploadSidebar = ({ files, onFileUpload, onFileRemove, chatHistory, onChatSelect, selectedChatId, isCollapsed, onToggleCollapse, onCreateChat }) => {
  const [uploading, setUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState(null);
  const [newChatName, setNewChatName] = React.useState('');
  const [creatingChat, setCreatingChat] = React.useState(false);

  const handleUpload = async (file) => {
    if (!selectedChatId) {
      setUploadError('Please select a chat first.');
      return;
    }

    if (!token) {
      setUploadError('You are not authenticated. Please log in.');
      return;
    }

    setUploading(true);
    setUploadError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API_BASE}/rag/chats/${selectedChatId}/upload_pdf/`, formData, {
        headers: {
          "Authorization": `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });
    } catch (err) {
      console.error('Upload error:', err);
      setUploadError(
        err.response?.data?.detail || 'Upload failed. Please try again.'
      );
    } finally {
      setUploading(false);
    }
  };

  const handleFileUploadWrapper = (newFiles) => {
    onFileUpload(newFiles);
    if (newFiles.length > 0) {
      handleUpload(newFiles[0]);
    }
  };

  const handleCreateChatClick = async () => {
    if (newChatName.trim() && !creatingChat) {
      setCreatingChat(true);
      try {
        await onCreateChat(newChatName.trim()); 
        setNewChatName('');
      } catch (error) {
        console.error('Error creating chat:', error);
      } finally {
        setCreatingChat(false);
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleCreateChatClick();
    }
  };

  return (
    <div className={`${isCollapsed ? 'w-16' : 'w-80'} transition-all duration-300 ease-in-out border-r border-[#23232b] bg-[#18181b] flex flex-col h-full`}>
      {/* Collapsed state - show only icons */}
      {isCollapsed ? (
        <div className="flex flex-col items-center py-4 space-y-4">
          <Button variant="ghost" size="sm" onClick={onToggleCollapse} className="mb-2">
            <Icon icon={ChevronRight} />
          </Button>

          {files.length > 0 && (
            <div className="relative group">
              <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                {files.length}
              </div>
              <div className="absolute left-full ml-2 top-0 bg-gray-900 dark:bg-gray-700 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                {files.length} file{files.length !== 1 ? 's' : ''} uploaded
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Expanded state - show full content */
        <>
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-[#e5e7eb] tracking-wide">
                Document Upload
              </h2>
              <Button variant="ghost" size="sm" onClick={onToggleCollapse}>
                <Icon icon={ChevronLeft} />
              </Button>
            </div>
            <div className="flex mb-2 gap-2">
              <input
                type="text"
                placeholder="New chat name"
                value={newChatName}
                onChange={e => setNewChatName(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={creatingChat}
                className="flex-1 px-2 py-1 rounded bg-[#23232b] border border-cyan-300 text-cyan-300 disabled:opacity-50"
              />
              <Button 
                variant="primary" 
                size="sm" 
                onClick={handleCreateChatClick}
                disabled={!newChatName.trim() || creatingChat}
              >
                {creatingChat ? '...' : '+'}
              </Button>
            </div>
            <FileUploadField
              files={files}
              onFileUpload={handleFileUploadWrapper}
              onFileRemove={onFileRemove}
            />
            {uploading && <div className="text-xs text-blue-400 mt-2">Uploading...</div>}
            {uploadError && <div className="text-xs text-red-400 mt-2">{uploadError}</div>}
          </div>

          <Divider />

          <div className="flex-1 p-4 overflow-y-auto">
            <h3 className="text-xs font-semibold text-[#a1a1aa] mb-3 uppercase tracking-wider">
              Chat History
            </h3>

            {chatHistory.length === 0 ? (
              <div className="text-center py-8">
                <Icon icon={MessageSquare} className="mx-auto mb-2 text-gray-400" />
                <p className="text-gray-500 dark:text-gray-400 text-sm">
                  No previous chats
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {chatHistory.map((chat) => (
                  <div
                    key={chat.id}
                    onClick={() => onChatSelect(chat.id)}
                    className={`p-3 rounded-md cursor-pointer transition-all border ${selectedChatId === chat.id
                      ? 'bg-[#23232b] border-[#6366f1] text-[#fff]'
                      : 'bg-transparent border-transparent hover:bg-[#23232b] hover:border-[#6366f1] text-[#e5e7eb]'
                      }`}
                  >
                    <div className="text-sm font-medium truncate">
                      {chat.title}
                    </div>
                    <div className="text-xs text-[#a1a1aa] mt-1">
                      {chat.messageCount} messages • {new Date(chat.lastUpdated).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default FileUploadSidebar;