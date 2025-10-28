import React, { useState } from 'react';
import { GitBranch, Network, Copy, Check } from 'lucide-react';
import PlantUMLDiagram from './PlantUMLDiagram';

interface RepositoryAnalysisDisplayProps {
  analysisData: {
    repository_name: string;
    total_files: number;
    file_relationships: {
      entry_points: string[];
      call_relationships: Array<{
        caller: string;
        called: string;
        relationship_type: string;
        description: string;
      }>;
      data_flow: Array<{
        from: string;
        to: string;
        data_type: string;
        description: string;
      }>;
      shared_resources: Array<{
        resource: string;
        used_by: string[];
        type: string;
      }>;
      business_processes: Array<{
        process: string;
        files: string[];
        flow: string;
      }>;
    };
    plantuml_diagram: string;
    documentation: string;
    analysis_timestamp: string;
  };
}

const RepositoryAnalysisDisplay: React.FC<RepositoryAnalysisDisplayProps> = ({ analysisData }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'diagram' | 'relationships' | 'documentation'>('overview');
  const [copiedDoc, setCopiedDoc] = useState(false);

  const copyToClipboard = async (text: string, setCopied: (value: boolean) => void) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Repository Summary</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-600">Repository Name:</span>
            <p className="font-medium">{analysisData.repository_name}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Total Files:</span>
            <p className="font-medium">{analysisData.total_files}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Entry Points:</span>
            <p className="font-medium">{analysisData.file_relationships.entry_points.length}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Analysis Date:</span>
            <p className="font-medium">{new Date(analysisData.analysis_timestamp).toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-800 mb-3 flex items-center">
          <GitBranch className="w-5 h-5 mr-2" />
          Entry Points
        </h3>
        <div className="space-y-2">
          {analysisData.file_relationships.entry_points.map((entry, index) => (
            <div key={index} className="bg-white rounded p-2 border border-blue-200">
              <span className="font-mono text-sm">{entry}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-green-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-green-800 mb-3 flex items-center">
          <Network className="w-5 h-5 mr-2" />
          Business Processes
        </h3>
        <div className="space-y-3">
          {analysisData.file_relationships.business_processes.map((process, index) => (
            <div key={index} className="bg-white rounded p-3 border border-green-200">
              <h4 className="font-medium text-green-800">{process.process}</h4>
              <p className="text-sm text-gray-600 mt-1">Flow: {process.flow}</p>
              <div className="mt-2">
                <span className="text-xs text-gray-500">Files involved:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {process.files.map((file, fileIndex) => (
                    <span key={fileIndex} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                      {file}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderDiagram = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">Repository Sequence Diagram</h3>
      </div>
      
      {analysisData.plantuml_diagram ? (
        <PlantUMLDiagram 
          code={analysisData.plantuml_diagram}
          title="Repository Flow Diagram"
        />
      ) : (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-gray-500">No PlantUML diagram available</p>
        </div>
      )}
    </div>
  );

  const renderRelationships = () => (
    <div className="space-y-6">
      <div className="bg-purple-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-purple-800 mb-3">Call Relationships</h3>
        <div className="space-y-2">
          {analysisData.file_relationships.call_relationships.map((rel, index) => (
            <div key={index} className="bg-white rounded p-3 border border-purple-200">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-mono text-sm font-medium">{rel.caller}</span>
                  <span className="mx-2 text-purple-600">→</span>
                  <span className="font-mono text-sm font-medium">{rel.called}</span>
                </div>
                <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">
                  {rel.relationship_type}
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-2">{rel.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-orange-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-orange-800 mb-3">Data Flow</h3>
        <div className="space-y-2">
          {analysisData.file_relationships.data_flow.map((flow, index) => (
            <div key={index} className="bg-white rounded p-3 border border-orange-200">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-mono text-sm font-medium">{flow.from}</span>
                  <span className="mx-2 text-orange-600">⟹</span>
                  <span className="font-mono text-sm font-medium">{flow.to}</span>
                </div>
                <span className="bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded">
                  {flow.data_type}
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-2">{flow.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-teal-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-teal-800 mb-3">Shared Resources</h3>
        <div className="space-y-2">
          {analysisData.file_relationships.shared_resources.map((resource, index) => (
            <div key={index} className="bg-white rounded p-3 border border-teal-200">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-teal-800">{resource.resource}</span>
                <span className="bg-teal-100 text-teal-800 text-xs px-2 py-1 rounded">
                  {resource.type}
                </span>
              </div>
              <div>
                <span className="text-xs text-gray-500">Used by:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {resource.used_by.map((file, fileIndex) => (
                    <span key={fileIndex} className="bg-teal-100 text-teal-800 text-xs px-2 py-1 rounded">
                      {file}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderDocumentation = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">Repository Documentation</h3>
        <button
          onClick={() => copyToClipboard(analysisData.documentation, setCopiedDoc)}
          className="flex items-center space-x-1 px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm transition-colors"
        >
          {copiedDoc ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
          <span>{copiedDoc ? 'Copied!' : 'Copy'}</span>
        </button>
      </div>
      
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div 
          className="prose prose-sm max-w-none"
          dangerouslySetInnerHTML={{ 
            __html: analysisData.documentation.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>')
          }}
        />
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col">
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-4">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'overview'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('diagram')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'diagram'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Sequence Diagram
        </button>
        <button
          onClick={() => setActiveTab('relationships')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'relationships'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Relationships
        </button>
        <button
          onClick={() => setActiveTab('documentation')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'documentation'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Documentation
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'diagram' && renderDiagram()}
        {activeTab === 'relationships' && renderRelationships()}
        {activeTab === 'documentation' && renderDocumentation()}
      </div>
    </div>
  );
};

export default RepositoryAnalysisDisplay;
