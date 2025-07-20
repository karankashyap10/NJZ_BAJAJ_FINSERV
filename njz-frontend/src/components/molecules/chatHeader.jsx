import React from 'react';
import { MessageSquare, Network, Sun, Moon, Settings, ChevronLeft, ChevronRight } from 'lucide-react';
import Icon from '../atoms/icons';
import Button from '../atoms/buttons';
const ChatHeader = ({ title = "NJZ Chat", onShowGraph, onToggleSidebar, isSidebarCollapsed }) => {

  return (
    <div className="border-b border-[#23232b] bg-[#18181b] p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">

          <Icon icon={MessageSquare} className="text-[#6366f1]" />
          <div>
            <h1 className="text-xl font-semibold text-left text-[#e5e7eb] tracking-wide">{title}</h1>
            <div className="text-xs text-[#a1a1aa] mt-1">Upload documents and chat with AI. Powered by <span className='font-bold text-[#6366f1]'>Gemini-2.5</span>.</div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="sm" onClick={onShowGraph}>
            <Icon icon={Network} className="mr-1" />
            Show RAG Graph
          </Button>

          <Button variant="ghost" size="sm">
            <Icon icon={Settings} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatHeader;