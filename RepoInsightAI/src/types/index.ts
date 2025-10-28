export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  content?: string;
  children?: FileNode[];
  size?: number;
  lastModified?: number;
}

export interface SelectedFile {
  name: string;
  path: string;
  content: string;
  language: string;
  size: number;
  lines: number;
}