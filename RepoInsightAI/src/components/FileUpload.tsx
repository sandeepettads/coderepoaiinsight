import React from 'react';
import { Upload, FolderOpen, AlertCircle } from 'lucide-react';

interface FileUploadProps {
  onFilesUpload: (files: FileList) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFilesUpload }) => {
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      onFilesUpload(files);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    
    const items = event.dataTransfer.items;
    if (items && items.length > 0) {
      const item = items[0];
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry();
        if (entry && entry.isDirectory) {
          // Handle directory drop - this would require additional implementation
          console.log('Directory dropped:', entry.name);
        }
      }
    }
  };
  return (
    <div 
      className="flex flex-col items-center justify-center h-full p-8"
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <div className="text-center">
        <FolderOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-300 mb-2">
          Upload Project Folder
        </h2>
        <p className="text-gray-500 mb-6">
          Select a folder to browse your entire code repository
        </p>
        
        <div className="mb-6 p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
          <div className="flex items-center gap-2 text-blue-400 mb-2">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Important</span>
          </div>
          <p className="text-xs text-blue-300">
            Make sure to select a folder (not individual files) to upload your entire codebase.
            The browser will ask for permission to access the folder contents.
          </p>
        </div>
        
        <label className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg cursor-pointer transition-colors">
          <Upload className="w-4 h-4" />
          Choose Folder
          <input
            type="file"
            webkitdirectory=""
            directory=""
            multiple
            onChange={handleFileChange}
            className="hidden"
          />
        </label>
        
        <p className="text-xs text-gray-500 mt-3">
          Supports all file types • No file size limits • Client-side only
        </p>
      </div>
    </div>
  );
};

export default FileUpload;