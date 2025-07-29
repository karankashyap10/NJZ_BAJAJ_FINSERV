import Button from '../atoms/buttons';
import InputField from '../atoms/inputfeild';
import React, { useRef, useState } from 'react';
import { Upload, Send, FileText, Plus } from 'lucide-react';
import Icon from '../atoms/icons';
import Tag from '../atoms/tag';

const ChatInputBox = ({
  message,
  setMessage,
  onSend,
  onFileUpload,
  files = [],
  onFileRemove,
  disabled = false,
  onCreateChat,
  selectedChatId
}) => {
  const fileInputRef = useRef(null);
  const [chatName, setChatName] = useState('');

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (message.trim() && !disabled) {
        onSend();
      }
    }
  };

  const handleCreateChat = () => {
    if (chatName.trim() && onCreateChat) {
      onCreateChat(chatName.trim());
      setChatName('');
    }
  };

  const handleChatNameKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleCreateChat();
    }
  };

  return (
    <div className="border-t border-[#23232b] bg-[#18181b] p-4">
      {/* Chat Name Input - Only show if no chat is selected */}
      {!selectedChatId && (
        <div className="mb-4">
          <label className="block text-xs text-[#a1a1aa] mb-1 uppercase tracking-wider">
            Create New Chat
          </label>
          <div className="flex items-center space-x-2">
            <InputField
              placeholder="Enter chat name..."
              value={chatName}
              onChange={(e) => setChatName(e.target.value)}
              onKeyPress={handleChatNameKeyPress}
              className="flex-1 bg-[#23232b] text-[#e5e7eb] border-[#23232b] focus:ring-[#6366f1] focus:border-[#6366f1] placeholder:text-[#a1a1aa]"
            />
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreateChat}
              disabled={!chatName.trim()}
              className="bg-[#6366f1] text-white hover:bg-[#4f46e5] font-semibold border border-[#6366f1]"
            >
              <Icon icon={Plus} />
            </Button>
          </div>
        </div>
      )}

      <label className="block text-xs text-[#a1a1aa] mb-1 uppercase tracking-wider">
        {selectedChatId ? 'Type your message' : 'Select a chat first'}
      </label>

      {/* Uploaded Files Appear Above Input */}
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {files.map((file, idx) => (
            <Tag
              key={file.name + idx}
              onRemove={() => onFileRemove(idx)}
              className="bg-[#23232b] border border-cyan-300 text-cyan-300"
            >
              <Icon icon={FileText} size="sm" className="mr-1" />
              {file.name}
            </Tag>
          ))}
        </div>
      )}

      <div className="flex items-end space-x-2">
        <div className="flex-1 relative">
          <InputField
            multiline
            rows={2}
            placeholder={selectedChatId ? "Ask a question about your documents..." : "Create a chat first to start messaging..."}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={disabled || !selectedChatId}
            className="bg-[#23232b] text-[#e5e7eb] border-[#23232b] focus:ring-[#6366f1] focus:border-[#6366f1] placeholder:text-[#a1a1aa]"
          />
        </div>
        <div className="flex space-x-2 mb-5">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={!selectedChatId}
            className="hover:bg-[#23232b]"
          >
            <Icon icon={Upload} />
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={onSend}
            disabled={!message.trim() || disabled || !selectedChatId}
            className="bg-[#6366f1] text-white hover:bg-[#4f46e5] font-semibold border border-[#6366f1]"
          >
            <Icon icon={Send} />
          </Button>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.docx"
        onChange={(e) => onFileUpload(Array.from(e.target.files))}
        className="hidden"
      />
    </div>
  );
};

export default ChatInputBox;
