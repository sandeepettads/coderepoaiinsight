import React, { useState } from 'react';
import { GitBranch, Database, Network, Copy, Check } from 'lucide-react';
import PlantUMLDiagram from './PlantUMLDiagram';

interface CobolAnalysisDisplayProps {
  analysisContent: string;
}

interface ParsedCobolAnalysis {
  callTree: string;
  dataDict: string;
  plantUML: string;
}

const CobolAnalysisDisplay: React.FC<CobolAnalysisDisplayProps> = ({ analysisContent }) => {
  
  const parseCobolAnalysis = (content: string): ParsedCobolAnalysis => {
    const sections = {
      callTree: '',
      dataDict: '',
      plantUML: ''
    };

    try {
      // Split content by section headers
      const callTreeMatch = content.match(/(?:^|\n)(?:#\s*)?Call Tree \+ Pseudocode([\s\S]*?)(?=(?:\n(?:#\s*)?(?:Data Dictionary|PlantUML)|$))/i);
      const dataDictMatch = content.match(/(?:^|\n)(?:#\s*)?Data Dictionary & Structural Layout([\s\S]*?)(?=(?:\n(?:#\s*)?(?:Call Tree|PlantUML)|$))/i);
      const plantUMLMatch = content.match(/(?:^|\n)(?:#\s*)?PlantUML Diagrams?([\s\S]*?)$/i);

      sections.callTree = callTreeMatch ? callTreeMatch[1].trim() : '';
      sections.dataDict = dataDictMatch ? dataDictMatch[1].trim() : '';
      sections.plantUML = plantUMLMatch ? plantUMLMatch[1].trim() : '';
    } catch (error) {
      console.error('Error parsing COBOL analysis:', error);
    }

    return sections;
  };

  const renderCallTree = (content: string) => {
    const [copiedTree, setCopiedTree] = useState(false);
    const [copiedPseudo, setCopiedPseudo] = useState(false);

    if (!content) return <p className="text-gray-400 text-sm">No call tree data available</p>;

    // Split into tree and pseudocode sections
    const lines = content.split('\n');
    let treeLines: string[] = [];
    let pseudocodeLines: string[] = [];
    let inPseudocode = false;

    for (const line of lines) {
      if (line.toLowerCase().includes('pseudocode') || inPseudocode) {
        inPseudocode = true;
        pseudocodeLines.push(line);
      } else if (!inPseudocode) {
        // Include all non-empty lines before pseudocode section as part of call tree
        if (line.trim().length > 0) {
          treeLines.push(line);
        }
      }
    }

    const copyToClipboard = async (text: string, type: 'tree' | 'pseudo') => {
      try {
        await navigator.clipboard.writeText(text);
        if (type === 'tree') {
          setCopiedTree(true);
          setTimeout(() => setCopiedTree(false), 2000);
        } else {
          setCopiedPseudo(true);
          setTimeout(() => setCopiedPseudo(false), 2000);
        }
      } catch (err) {
        console.error('Failed to copy text: ', err);
      }
    };

    const highlightCobolSyntax = (text: string) => {
      return text
        // COBOL paragraph names (various patterns)
        .replace(/(\d{4}-[A-Z][A-Z0-9-]*)/g, '<span class="text-yellow-400 font-semibold">$1</span>')
        .replace(/(\d{3}-[A-Z][A-Z0-9-]*)/g, '<span class="text-yellow-400 font-semibold">$1</span>')
        .replace(/(\d{2}-[A-Z][A-Z0-9-]*)/g, '<span class="text-yellow-400 font-semibold">$1</span>')
        .replace(/(\d{1}-[A-Z][A-Z0-9-]*)/g, '<span class="text-yellow-400 font-semibold">$1</span>')
        // General paragraph names (word boundaries)
        .replace(/\b([A-Z][A-Z0-9-]*[A-Z0-9])\b/g, '<span class="text-yellow-400 font-semibold">$1</span>')
        // Tree characters
        .replace(/(├─|└─|│)/g, '<span class="text-gray-500">$1</span>')
        // Comments and annotations
        .replace(/(\([^)]+\))/g, '<span class="text-blue-300">$1</span>')
        // PERFORM statements
        .replace(/\b(PERFORM|CALL|GO TO)\b/g, '<span class="text-green-400">$1</span>');
    };

    return (
      <div className="space-y-4">
        {/* Call Tree */}
        {treeLines.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-sm font-medium text-gray-300">Call Tree</h5>
              <button
                onClick={() => copyToClipboard(treeLines.join('\n'), 'tree')}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                title="Copy call tree"
              >
                {copiedTree ? (
                  <>
                    <Check className="w-3 h-3 text-green-400" />
                    <span className="text-green-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3 text-gray-400" />
                    <span className="text-gray-400">Copy</span>
                  </>
                )}
              </button>
            </div>
            <div className="bg-gray-900 border border-gray-600 rounded p-4 relative">
              <pre 
                className="text-sm font-mono whitespace-pre overflow-x-auto"
                dangerouslySetInnerHTML={{
                  __html: highlightCobolSyntax(treeLines.join('\n'))
                }}
              />
            </div>
          </div>
        )}

        {/* Pseudocode */}
        {pseudocodeLines.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-sm font-medium text-gray-300">Pseudocode Logic</h5>
              <button
                onClick={() => copyToClipboard(pseudocodeLines.join('\n'), 'pseudo')}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                title="Copy pseudocode"
              >
                {copiedPseudo ? (
                  <>
                    <Check className="w-3 h-3 text-green-400" />
                    <span className="text-green-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3 text-gray-400" />
                    <span className="text-gray-400">Copy</span>
                  </>
                )}
              </button>
            </div>
            <div className="bg-gray-900 border border-gray-600 rounded p-4">
              <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap">
                {pseudocodeLines.join('\n')}
              </pre>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderDataDictionary = (content: string) => {
    if (!content) return <p className="text-gray-400 text-sm">No data dictionary available</p>;

    const lines = content.split('\n');
    const sections: { 
      orchestrationTable: string[][];
      workingStorageTable: string[][];
      traversalMechanics: string[];
      outputs: string[];
    } = {
      orchestrationTable: [],
      workingStorageTable: [],
      traversalMechanics: [],
      outputs: []
    };

    let currentSection = '';
    let currentTable: string[][] = [];

    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Detect sections
      if (trimmedLine.toLowerCase().includes('orchestration paragraphs')) {
        currentSection = 'orchestration';
        currentTable = [];
        continue;
      } else if (trimmedLine.toLowerCase().includes('working-storage structures') || 
                 trimmedLine.toLowerCase().includes('core working-storage')) {
        if (currentTable.length > 0) sections.orchestrationTable = [...currentTable];
        currentSection = 'workingStorage';
        currentTable = [];
        continue;
      } else if (trimmedLine.toLowerCase().includes('traversal mechanics')) {
        if (currentTable.length > 0 && currentSection === 'workingStorage') {
          sections.workingStorageTable = [...currentTable];
        }
        currentSection = 'traversal';
        continue;
      } else if (trimmedLine.toLowerCase().includes('outputs')) {
        currentSection = 'outputs';
        continue;
      }

      // Parse table rows
      if (trimmedLine.includes('|') && (currentSection === 'orchestration' || currentSection === 'workingStorage')) {
        const cells = trimmedLine.split('|').map(cell => cell.trim()).filter(cell => cell);
        if (cells.length > 1 && !cells[0].includes('---')) {
          currentTable.push(cells);
        }
      }
      
      // Parse bullet points
      else if ((trimmedLine.startsWith('•') || trimmedLine.startsWith('-')) && currentSection === 'traversal') {
        sections.traversalMechanics.push(trimmedLine);
      } else if ((trimmedLine.startsWith('•') || trimmedLine.startsWith('-')) && currentSection === 'outputs') {
        sections.outputs.push(trimmedLine);
      }
    }

    // Capture final table
    if (currentTable.length > 0 && currentSection === 'workingStorage') {
      sections.workingStorageTable = [...currentTable];
    }

    const renderTable = (title: string, rows: string[][], bgColor = 'bg-gray-900') => {
      if (rows.length === 0) return null;

      return (
        <div className="mb-6">
          <h5 className="text-base font-medium text-white mb-3">{title}</h5>
          <div className={`${bgColor} border border-gray-600 rounded-lg overflow-hidden`}>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  {rows.length > 0 && (
                    <tr className="bg-gray-800 border-b border-gray-600">
                      {rows[0].map((header, colIndex) => (
                        <th key={colIndex} className="px-4 py-3 text-left font-medium text-gray-200 text-sm">
                          {header}
                        </th>
                      ))}
                    </tr>
                  )}
                </thead>
                <tbody>
                  {rows.slice(1).map((row, rowIndex) => (
                    <tr key={rowIndex} className="border-b border-gray-700 hover:bg-gray-800/50 transition-colors">
                      {row.map((cell, colIndex) => (
                        <td key={colIndex} className="px-4 py-3 text-gray-300 text-sm">
                          <span className="font-mono">{cell}</span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      );
    };

    const renderBulletSection = (title: string, items: string[]) => {
      if (items.length === 0) return null;

      return (
        <div className="mb-6">
          <h5 className="text-base font-medium text-white mb-3">{title}</h5>
          <div className="bg-gray-900 border border-gray-600 rounded-lg p-4">
            <ul className="space-y-2">
              {items.map((item, index) => (
                <li key={index} className="text-gray-300 text-sm flex items-start">
                  <span className="text-gray-500 mr-2 mt-1">•</span>
                  <span className="font-mono">{item.replace(/^[•-]\s*/, '')}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      );
    };

    return (
      <div className="space-y-6">
        {renderTable('Orchestration paragraphs', sections.orchestrationTable)}
        {renderTable('Core working-storage structures', sections.workingStorageTable)}
        {renderBulletSection('Traversal mechanics & invariants', sections.traversalMechanics)}
      </div>
    );
  };

  const renderPlantUMLDiagrams = (content: string) => {
    if (!content) return <p className="text-gray-400 text-sm">No PlantUML diagrams available</p>;

    // Extract PlantUML code blocks
    const plantUMLBlocks = content.match(/```plantuml([\s\S]*?)```/g) || [];
    
    if (plantUMLBlocks.length === 0) {
      return (
        <div className="bg-gray-900 border border-gray-600 rounded p-3">
          <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">{content}</pre>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {plantUMLBlocks.map((block, index) => {
          const code = block.replace(/```plantuml\s*/, '').replace(/```\s*$/, '').trim();
          const title = index === 0 ? 'High-Level Orchestration' : 'Processing Deep-Dive';
          
          return (
            <PlantUMLDiagram
              key={index}
              code={code}
              title={title}
            />
          );
        })}
      </div>
    );
  };

  const parsedAnalysis = parseCobolAnalysis(analysisContent);

  return (
    <div className="p-6 space-y-6 h-full overflow-y-auto">
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
          <span className="text-sm font-medium text-gray-300">COBOL Analysis Complete</span>
        </div>
        <p className="text-xs text-gray-400">
          Analysis follows the three-deliverable format: Call Tree, Data Dictionary, and PlantUML Diagrams
        </p>
      </div>

      {/* Call Tree + Pseudocode Section */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <GitBranch className="w-4 h-4 text-green-400" />
          <h4 className="text-sm font-medium text-gray-300">Call Tree + Pseudocode</h4>
        </div>
        {renderCallTree(parsedAnalysis.callTree)}
      </div>

      {/* Data Dictionary Section */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <Database className="w-4 h-4 text-blue-400" />
          <h4 className="text-sm font-medium text-gray-300">Data Dictionary & Structural Layout</h4>
        </div>
        {renderDataDictionary(parsedAnalysis.dataDict)}
      </div>

      {/* PlantUML Diagrams Section */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <Network className="w-4 h-4 text-purple-400" />
          <h4 className="text-sm font-medium text-gray-300">PlantUML Sequence Diagrams</h4>
        </div>
        {renderPlantUMLDiagrams(parsedAnalysis.plantUML)}
      </div>

      {/* Raw Analysis (for debugging) */}
      <details className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <summary className="text-sm font-medium text-gray-300 cursor-pointer">
          Raw Analysis Output (Debug)
        </summary>
        <div className="mt-3 bg-gray-900 border border-gray-600 rounded p-3">
          <pre className="text-xs text-gray-400 whitespace-pre-wrap overflow-x-auto">
            {analysisContent}
          </pre>
        </div>
      </details>
    </div>
  );
};

export default CobolAnalysisDisplay;
