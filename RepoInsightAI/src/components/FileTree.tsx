import React from 'react';
import { 
  Folder, 
  FolderOpen, 
  FileText, 
  ChevronRight, 
  ChevronDown 
} from 'lucide-react';
import { FileNode } from '../types';

interface FileTreeProps {
  nodes: FileNode[];
  onFileSelect: (file: FileNode) => void;
  selectedFile: string | null;
  expandedFolders: Set<string>;
  onFolderToggle: (path: string) => void;
  searchTerm: string;
}

interface FileTreeItemProps {
  node: FileNode;
  onFileSelect: (file: FileNode) => void;
  selectedFile: string | null;
  expandedFolders: Set<string>;
  onFolderToggle: (path: string) => void;
  level: number;
  searchTerm: string;
}

const FileTreeItem: React.FC<FileTreeItemProps> = ({
  node,
  onFileSelect,
  selectedFile,
  expandedFolders,
  onFolderToggle,
  level,
  searchTerm
}) => {
  const isExpanded = expandedFolders.has(node.path);
  const isSelected = selectedFile === node.path;
  
  // Improved search logic - show if name matches or if any descendant matches
  const shouldShow = !searchTerm || 
    node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (node.children && hasMatchingDescendant(node.children, searchTerm));

  if (!shouldShow) {
    return null;
  }

  const handleClick = () => {
    if (node.type === 'directory') {
      onFolderToggle(node.path);
    } else {
      onFileSelect(node);
    }
  };

  const paddingLeft = level * 12 + 8;

  return (
    <>
      <div
        className={`flex items-center gap-1 py-1 px-2 cursor-pointer hover:bg-gray-700 ${
          isSelected ? 'bg-gray-600' : ''
        }`}
        style={{ paddingLeft: `${paddingLeft}px` }}
        onClick={handleClick}
        title={node.path}
      >
        {node.type === 'directory' && (
          <span className="w-4 h-4 flex items-center justify-center">
            {isExpanded ? (
              <ChevronDown className="w-3 h-3 text-gray-400" />
            ) : (
              <ChevronRight className="w-3 h-3 text-gray-400" />
            )}
          </span>
        )}
        {node.type === 'directory' ? (
          isExpanded ? (
            <FolderOpen className="w-4 h-4 text-blue-400" />
          ) : (
            <Folder className="w-4 h-4 text-blue-400" />
          )
        ) : (
          <FileText className="w-4 h-4 text-gray-400 ml-4" />
        )}
        <span className="text-sm text-gray-300 truncate flex-1">{node.name}</span>
        {node.type === 'file' && node.size && (
          <span className="text-xs text-gray-500 ml-2">
            {formatFileSize(node.size)}
          </span>
        )}
      </div>
      {node.type === 'directory' && isExpanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeItem
              key={child.path}
              node={child}
              onFileSelect={onFileSelect}
              selectedFile={selectedFile}
              expandedFolders={expandedFolders}
              onFolderToggle={onFolderToggle}
              level={level + 1}
              searchTerm={searchTerm}
            />
          ))}
        </div>
      )}
    </>
  );
};

// Helper function to check if any descendant matches the search term
const hasMatchingDescendant = (children: FileNode[], searchTerm: string): boolean => {
  return children.some(child => 
    child.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (child.children && hasMatchingDescendant(child.children, searchTerm))
  );
};

// Import formatFileSize function
import { formatFileSize } from '../utils/fileUtils';

const FileTree: React.FC<FileTreeProps> = ({
  nodes,
  onFileSelect,
  selectedFile,
  expandedFolders,
  onFolderToggle,
  searchTerm
}) => {
  return (
    <div className="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
      {nodes.map((node) => (
        <FileTreeItem
          key={node.path}
          node={node}
          onFileSelect={onFileSelect}
          selectedFile={selectedFile}
          expandedFolders={expandedFolders}
          onFolderToggle={onFolderToggle}
          level={0}
          searchTerm={searchTerm}
        />
      ))}
    </div>
  );
};

export default FileTree;