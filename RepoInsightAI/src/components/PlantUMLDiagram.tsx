import React, { useState } from 'react';
import { Copy, Check, ExternalLink } from 'lucide-react';

// Import plantuml-encoder (suppress TypeScript errors)
// @ts-ignore
import * as plantumlEncoder from 'plantuml-encoder';

interface PlantUMLDiagramProps {
  code: string;
  title?: string;
}

const PlantUMLDiagram: React.FC<PlantUMLDiagramProps> = ({ code, title }) => {
  const [copied, setCopied] = useState(false);
  const [imageError, setImageError] = useState(false);

  if (!code) return null;

  // Encode the PlantUML code
  let encodedCode = '';
  let diagramUrl = '';
  
  try {
    encodedCode = plantumlEncoder.encode(code);
    diagramUrl = `https://www.plantuml.com/plantuml/png/${encodedCode}`;
  } catch (error) {
    console.error('Error encoding PlantUML:', error);
    setImageError(true);
  }

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const openInEditor = () => {
    const editorUrl = `https://www.plantuml.com/plantuml/uml/${encodedCode}`;
    window.open(editorUrl, '_blank');
  };

  return (
    <div className="bg-gray-900 border border-gray-600 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h5 className="text-sm font-medium text-gray-300">{title || 'PlantUML Diagram'}</h5>
        <div className="flex gap-2">
          <button
            onClick={copyToClipboard}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
            title="Copy PlantUML code"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-green-400" />
                <span className="text-green-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>Copy Code</span>
              </>
            )}
          </button>
          <button
            onClick={openInEditor}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-700 hover:bg-blue-600 text-white rounded transition-colors"
            title="Open in PlantUML Editor"
          >
            <ExternalLink className="w-3 h-3" />
            <span>Edit</span>
          </button>
        </div>
      </div>

      {/* Rendered Diagram */}
      {!imageError && diagramUrl && (
        <div className="mb-4 bg-white rounded p-4 flex justify-center">
          <img
            src={diagramUrl}
            alt={`PlantUML Diagram: ${title || 'Sequence Diagram'}`}
            className="max-w-full h-auto"
            onError={() => setImageError(true)}
            onLoad={() => setImageError(false)}
          />
        </div>
      )}

      {/* Fallback: Show code if image fails to load */}
      {imageError && (
        <div className="mb-4">
          <div className="bg-red-900/20 border border-red-600 rounded p-3 mb-3">
            <p className="text-red-400 text-xs">
              ⚠️ Diagram rendering failed. Showing PlantUML code instead.
            </p>
          </div>
          <div className="bg-gray-800 border border-gray-700 rounded p-3">
            <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap overflow-x-auto">
              {code}
            </pre>
          </div>
        </div>
      )}

      {/* Source Code (Collapsible) */}
      <details className="mt-3">
        <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-300">
          View PlantUML Source Code
        </summary>
        <div className="mt-2 bg-gray-800 border border-gray-700 rounded p-3">
          <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap overflow-x-auto">
            {code}
          </pre>
        </div>
      </details>

      <div className="mt-2 text-xs text-gray-400">
        💡 Diagram rendered via{' '}
        <a 
          href="https://www.plantuml.com/" 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300 underline"
        >
          PlantUML Server
        </a>
      </div>
    </div>
  );
};

export default PlantUMLDiagram;
