import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  code: string;
  className?: string;
}

const MermaidDiagram: React.FC<MermaidDiagramProps> = ({ code, className = '' }) => {
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize mermaid with dark theme
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        primaryColor: '#3b82f6',
        primaryTextColor: '#e5e7eb',
        primaryBorderColor: '#374151',
        lineColor: '#6b7280',
        secondaryColor: '#1f2937',
        tertiaryColor: '#111827',
        background: '#111827',
        mainBkg: '#1f2937',
        secondBkg: '#374151',
        tertiaryBkg: '#4b5563'
      }
    });
  }, []);

  useEffect(() => {
    if (elementRef.current && code) {
      const renderDiagram = async () => {
        try {
          // Clear previous content
          elementRef.current!.innerHTML = '';
          
          // Generate unique ID for this diagram
          const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
          
          // Render the diagram
          const { svg } = await mermaid.render(id, code);
          
          if (elementRef.current) {
            elementRef.current.innerHTML = svg;
          }
        } catch (error) {
          console.error('Mermaid rendering error:', error);
          if (elementRef.current) {
            elementRef.current.innerHTML = `
              <div class="text-red-400 text-sm p-4 border border-red-600 rounded bg-red-900/20">
                <p class="font-medium mb-2">Diagram rendering failed</p>
                <p class="text-xs text-red-300">Please check the diagram syntax</p>
                <details class="mt-2">
                  <summary class="cursor-pointer text-xs">Show raw code</summary>
                  <pre class="mt-2 text-xs bg-gray-800 p-2 rounded overflow-x-auto">${code}</pre>
                </details>
              </div>
            `;
          }
        }
      };

      renderDiagram();
    }
  }, [code]);

  return (
    <div className={`mermaid-container ${className}`}>
      <div 
        ref={elementRef} 
        className="bg-gray-800 rounded-lg p-4 overflow-x-auto"
        style={{ minHeight: '200px' }}
      />
    </div>
  );
};

export default MermaidDiagram;
