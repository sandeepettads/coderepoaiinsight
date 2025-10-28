import React from 'react';
import Editor from '@monaco-editor/react';
import { SelectedFile } from '../types';
import { formatFileSize } from '../utils/fileUtils';
import { registerCobolLanguage } from '../utils/cobolLanguage';

interface CodeEditorProps {
  selectedFile: SelectedFile | null;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ selectedFile }) => {
  const handleEditorWillMount = (monaco: any) => {
    registerCobolLanguage(monaco);
  };

  if (!selectedFile) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <div className="text-center">
          <div className="text-6xl mb-4">📁</div>
          <p className="text-lg">Select a file to view its contents</p>
        </div>
      </div>
    );
  }

  const breadcrumbs = selectedFile.path.split('/');

  return (
    <div className="h-full flex flex-col">
      {/* Breadcrumb Navigation */}
      <div className="px-4 py-2 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center text-sm text-gray-300 mb-1">
          {breadcrumbs.map((crumb, index) => (
            <React.Fragment key={index}>
              {index > 0 && <span className="mx-2 text-gray-500">/</span>}
              <span className={index === breadcrumbs.length - 1 ? 'text-blue-400' : ''}>
                {crumb}
              </span>
            </React.Fragment>
          ))}
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>{selectedFile.lines} lines</span>
          <span>{formatFileSize(selectedFile.size)}</span>
        </div>
      </div>

      {/* Code Editor */}
      <div className="flex-1">
        <Editor
          height="100%"
          language={selectedFile.language}
          value={selectedFile.content}
          theme="vs-dark"
          beforeMount={handleEditorWillMount}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            wordWrap: 'off',
            renderWhitespace: 'selection',
            cursorBlinking: 'blink',
            cursorSmoothCaretAnimation: 'on',
            smoothScrolling: true
          }}
        />
      </div>
    </div>
  );
};

export default CodeEditor;