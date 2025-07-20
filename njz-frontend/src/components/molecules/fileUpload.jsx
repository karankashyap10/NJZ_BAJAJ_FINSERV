import React, { useRef } from 'react';
import { Upload, FileText } from 'lucide-react';
import Icon from '../atoms/icons';
import Tag from '../atoms/tag';

const FileUploadField = ({ files = [], onFileUpload, onFileRemove }) => {
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    onFileUpload(selectedFiles);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    onFileUpload(droppedFiles);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div className="space-y-3">
      <div
        className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-blue-500 transition-colors cursor-pointer"
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <Icon icon={Upload} className="mx-auto mb-2 text-gray-400" />
        <p className="text-gray-600 dark:text-gray-400">
          Drop files here or <span className="text-blue-600 dark:text-blue-400">browse</span>
        </p>
        <p className="text-xs text-gray-500 mt-1">PDF, DOCX files supported</p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.docx"
        onChange={handleFileSelect}
        className="hidden"
      />

      {files.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {files.map((file, index) => (
            <Tag
              key={index}
              onRemove={() => onFileRemove(index)}
            >
              <Icon icon={FileText} size="sm" className="mr-1" />
              {file.name}
            </Tag>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUploadField;