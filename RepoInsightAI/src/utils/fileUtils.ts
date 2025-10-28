import { FileNode } from '../types';

export const getFileLanguage = (fileName: string): string => {
  const ext = fileName.split('.').pop()?.toLowerCase();
  const languageMap: Record<string, string> = {
    js: 'javascript',
    jsx: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    html: 'html',
    css: 'css',
    scss: 'scss',
    sass: 'sass',
    json: 'json',
    md: 'markdown',
    py: 'python',
    java: 'java',
    cpp: 'cpp',
    c: 'c',
    cs: 'csharp',
    php: 'php',
    rb: 'ruby',
    go: 'go',
    rs: 'rust',
    sh: 'shell',
    sql: 'sql',
    xml: 'xml',
    yaml: 'yaml',
    yml: 'yaml',
    dockerfile: 'dockerfile',
    cbl: 'cobol',
    cob: 'cobol',
    cpy: 'cobol',
    gitignore: 'plaintext',
    env: 'plaintext',
    txt: 'plaintext'
  };
  
  return languageMap[ext || ''] || 'plaintext';
};

export const buildFileTree = (files: File[]): FileNode[] => {
  const root: { [key: string]: FileNode } = {};
  
  files.forEach(file => {
    const pathParts = file.webkitRelativePath.split('/');
    let current = root;
    
    pathParts.forEach((part, index) => {
      if (!current[part]) {
        current[part] = {
          name: part,
          path: pathParts.slice(0, index + 1).join('/'),
          type: index === pathParts.length - 1 ? 'file' : 'directory',
          children: index === pathParts.length - 1 ? undefined : {},
          size: index === pathParts.length - 1 ? file.size : undefined,
          lastModified: index === pathParts.length - 1 ? file.lastModified : undefined
        };
      }
      
      if (index < pathParts.length - 1) {
        current = current[part].children as { [key: string]: FileNode };
      }
    });
  });
  
  const convertToArray = (obj: { [key: string]: FileNode }): FileNode[] => {
    return Object.values(obj).map(node => ({
      ...node,
      children: node.children ? convertToArray(node.children as { [key: string]: FileNode }) : undefined
    })).sort((a, b) => {
      // Sort directories first, then files
      if (a.type !== b.type) {
        return a.type === 'directory' ? -1 : 1;
      }
      // Within same type, sort alphabetically (case-insensitive)
      return a.name.toLowerCase().localeCompare(b.name.toLowerCase());
    });
  };
  
  return convertToArray(root);
};

export const flattenFileTree = (nodes: FileNode[]): FileNode[] => {
  const result: FileNode[] = [];
  
  const traverse = (node: FileNode) => {
    result.push(node);
    if (node.children) {
      node.children.forEach(traverse);
    }
  };
  
  nodes.forEach(traverse);
  return result;
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

export const countLines = (content: string): number => {
  return content.split('\n').length;
};