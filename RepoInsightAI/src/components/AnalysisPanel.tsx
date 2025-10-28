import React, { useState } from 'react';
import { 
  Building2, 
  Code2, 
  FileText, 
  Brain, 
  Shield, 
  TestTube,
  Play,
  AlertCircle,
  CheckCircle,
  Clock,
  Loader2
} from 'lucide-react';
import { AnalysisApiService, AnalysisResponse } from '../services/apiClient';
import CobolAnalysisDisplay from './CobolAnalysisDisplay';
import RepositoryAnalysisDisplay from './RepositoryAnalysisDisplay';

interface Tab {
  id: string;
  title: string;
  icon: React.ReactNode;
  description: string;
}

const tabs: Tab[] = [
  {
    id: 'architectural',
    title: 'Architectural & Structural Analysis',
    icon: <Building2 className="w-4 h-4" />,
    description: 'Analyze code architecture, design patterns, and structural relationships'
  },
  {
    id: 'quality',
    title: 'Code Quality & Refactoring',
    icon: <Code2 className="w-4 h-4" />,
    description: 'Identify code smells, suggest improvements, and refactoring opportunities'
  },
  {
    id: 'documentation',
    title: 'Documentation & Explanation',
    icon: <FileText className="w-4 h-4" />,
    description: 'Generate repository documentation and PlantUML sequence diagrams'
  },
  {
    id: 'business',
    title: 'Business Logic & Domain Understanding',
    icon: <Brain className="w-4 h-4" />,
    description: 'Understand business rules, domain logic, and functional requirements'
  },
  {
    id: 'security',
    title: 'Security & Vulnerability Analysis',
    icon: <Shield className="w-4 h-4" />,
    description: 'Scan for security vulnerabilities, potential threats, and best practices'
  },
  {
    id: 'testing',
    title: 'Testing & Test Case Generation',
    icon: <TestTube className="w-4 h-4" />,
    description: 'Generate test cases, identify testing gaps, and suggest test strategies'
  }
];

interface AnalysisPanelProps {
  selectedFile: string | null;
  files: File[];
  projectName: string;
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ selectedFile, files, projectName, activeTab, onTabChange }) => {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState<string>('');

  const renderTabContent = () => {
    const activeTabData = tabs.find(tab => tab.id === activeTab);
    
    if (!selectedFile) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-gray-400 p-8">
          <AlertCircle className="w-12 h-12 mb-4" />
          <h3 className="text-lg font-medium mb-2">No File Selected</h3>
          <p className="text-center text-sm">
            Select a file from the file tree to begin analysis
          </p>
        </div>
      );
    }

    return (
      <div className="p-6 h-full overflow-y-auto">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-200 mb-2 flex items-center gap-2">
            {activeTabData?.icon}
            {activeTabData?.title}
          </h3>
          <p className="text-sm text-gray-400 mb-4">
            {activeTabData?.description}
          </p>
        </div>

        <div className="space-y-4">
          {/* Analysis Status */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4 text-yellow-400" />
              <span className="text-sm font-medium text-gray-300">Analysis Status</span>
            </div>
            {!analysisResult && !isAnalyzing && (
              <>
                <p className="text-sm text-gray-400 mb-3">
                  Ready to analyze {files.length} files from {projectName || 'your repository'}.
                </p>
                <button 
                  onClick={handleRunAnalysis}
                  disabled={files.length === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-md transition-colors text-sm"
                >
                  <Play className="w-4 h-4" />
                  Run Architectural Analysis
                </button>
              </>
            )}
            
            {isAnalyzing && (
              <>
                <p className="text-sm text-gray-400 mb-3">
                  {analysisProgress || 'Analyzing repository architecture...'}
                </p>
                <div className="flex items-center gap-2 text-blue-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Analysis in progress</span>
                </div>
              </>
            )}
            
            {analysisError && (
              <>
                <p className="text-sm text-red-400 mb-3">
                  Analysis failed: {analysisError}
                </p>
                <button 
                  onClick={handleRunAnalysis}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors text-sm"
                >
                  <Play className="w-4 h-4" />
                  Retry Analysis
                </button>
              </>
            )}
            
            {analysisResult && (
              <>
                <p className="text-sm text-green-400 mb-3">
                  Analysis completed in {analysisResult.repository_info.analysis_duration}
                </p>
                <div className="flex items-center gap-2 text-green-400">
                  <CheckCircle className="w-4 h-4" />
                  <span className="text-sm">Ready to view results</span>
                </div>
              </>
            )}
          </div>

          {/* Analysis Results */}
          {analysisResult && renderAnalysisResults()}

          {/* Analysis Options */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Analysis Options</h4>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm text-gray-400">
                <input type="checkbox" className="rounded border-gray-600 bg-gray-700" defaultChecked />
                Include detailed explanations
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-400">
                <input type="checkbox" className="rounded border-gray-600 bg-gray-700" defaultChecked />
                Suggest improvements
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-400">
                <input type="checkbox" className="rounded border-gray-600 bg-gray-700" />
                Include code examples
              </label>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const handleRunAnalysis = async () => {
    if (files.length === 0) return;
    
    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisProgress('Uploading files and starting analysis...');

    // Check if this is documentation tab for repository analysis
    if (activeTab === 'documentation') {
      return handleRepositoryAnalysis();
    }
    
    try {
      // Start analysis
      const response = await AnalysisApiService.startArchitecturalAnalysis(
        files,
        projectName,
        true, // include diagrams
        true  // include recommendations
      );
      
      setAnalysisProgress('Analysis started, processing repository...');
      
      // Poll for results
      await pollForResults(response.analysis_id);
      
    } catch (error) {
      console.error('Analysis failed:', error);
      setAnalysisError(error instanceof Error ? error.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  const handleRepositoryAnalysis = async () => {
    try {
      setAnalysisProgress('Starting repository analysis...');
      
      // Call repository analysis endpoint
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      formData.append('repository_name', projectName);
      formData.append('analysis_type', 'documentation');

      const response = await fetch('http://localhost:8000/api/repository-analysis', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Repository analysis failed: ${response.statusText}`);
      }

      const result = await response.json();
      const analysisId = result.analysis_id;

      setAnalysisProgress('Repository analysis in progress...');

      // Poll for results
      const pollForResults = async () => {
        try {
          const statusResponse = await fetch(`http://localhost:8000/api/analysis/${analysisId}/status`);
          if (!statusResponse.ok) {
            throw new Error('Failed to get analysis status');
          }

          const statusData = await statusResponse.json();
          
          if (statusData.status === 'completed') {
            setAnalysisResult({
              ...statusData,
              repository_analysis: statusData.repository_analysis
            });
            setIsAnalyzing(false);
          } else if (statusData.status === 'failed') {
            throw new Error(statusData.error_message || 'Repository analysis failed');
          } else {
            // Continue polling
            setTimeout(pollForResults, 2000);
          }
        } catch (error) {
          console.error('Polling error:', error);
          setAnalysisError(error instanceof Error ? error.message : 'Failed to get analysis results');
          setIsAnalyzing(false);
        }
      };

      // Start polling
      setTimeout(pollForResults, 2000);

    } catch (error) {
      console.error('Repository analysis failed:', error);
      setAnalysisError(error instanceof Error ? error.message : 'Repository analysis failed');
      setIsAnalyzing(false);
    }
  };
  
  const pollForResults = async (analysisId: string) => {
    const maxAttempts = 60; // 5 minutes with 5-second intervals
    let attempts = 0;
    
    const poll = async () => {
      try {
        attempts++;
        const status = await AnalysisApiService.getAnalysisStatus(analysisId);
        
        if (status.status === 'completed') {
          const results = await AnalysisApiService.getAnalysisResults(analysisId);
          setAnalysisResult(results);
          setIsAnalyzing(false);
          setAnalysisProgress('');
        } else if (status.status === 'failed') {
          setAnalysisError(status.error_message || 'Analysis failed');
          setIsAnalyzing(false);
          setAnalysisProgress('');
        } else if (attempts >= maxAttempts) {
          setAnalysisError('Analysis timed out');
          setIsAnalyzing(false);
          setAnalysisProgress('');
        } else {
          // Continue polling
          setAnalysisProgress(`Analysis in progress... (${attempts}/${maxAttempts})`);
          setTimeout(poll, 5000);
        }
      } catch (error: any) {
        console.error('Polling error:', error);
        if (attempts >= maxAttempts) {
          setAnalysisError('Failed to get analysis results');
          setIsAnalyzing(false);
          setAnalysisProgress('');
        } else {
          setTimeout(poll, 5000);
        }
      }
    };
    
    setTimeout(poll, 2000); // Start polling after 2 seconds
  };
  
  const renderAnalysisResults = () => {
    if (!analysisResult) return null;

    // Check if this is repository analysis
    if (analysisResult.repository_analysis) {
      return (
        <RepositoryAnalysisDisplay 
          analysisData={analysisResult.repository_analysis}
        />
      );
    }

    // Check if this is COBOL analysis
    if (analysisResult.architectural_analysis?.overview?.includes('Call Tree') || 
        analysisResult.architectural_analysis?.overview?.includes('PlantUML')) {
      return (
        <CobolAnalysisDisplay 
          analysisContent={analysisResult.architectural_analysis.overview}
        />
      );
    }

    if (!analysisResult?.architectural_analysis) return null;
    
    const analysis = analysisResult.architectural_analysis;
    
    return (
      <div className="space-y-4">
        {/* Repository Overview */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-sm font-medium text-gray-300">Repository Overview</span>
            </div>
            <div className="text-xs text-gray-500">
              {analysisResult.repository_info.total_files} files • {analysisResult.repository_info.total_lines} lines
            </div>
          </div>
          <p className="text-sm text-gray-300 mb-3">{analysis.overview}</p>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-gray-500">Primary Language:</span>
              <span className="text-gray-300 ml-2">{analysisResult.repository_info.primary_language}</span>
            </div>
            <div>
              <span className="text-gray-500">Components:</span>
              <span className="text-gray-300 ml-2">{analysis.components.length}</span>
            </div>
          </div>
        </div>
        
        {/* Architectural Components */}
        {analysis.components.length > 0 && (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Architectural Components</h4>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {analysis.components.map((component, index) => (
                <div key={index} className="border-l-2 border-blue-500 pl-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-200">{component.component_name}</span>
                    <span className="text-xs px-2 py-1 bg-gray-700 rounded text-gray-400">{component.type}</span>
                  </div>
                  <div className="text-xs text-gray-400 mb-2">
                    {component.responsibilities.slice(0, 2).map((resp, i) => (
                      <div key={i}>• {resp}</div>
                    ))}
                  </div>
                  {component.dependencies.length > 0 && (
                    <div className="text-xs text-gray-500">
                      Dependencies: {component.dependencies.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Architectural Patterns */}
        {analysis.patterns.length > 0 && (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Detected Patterns</h4>
            <div className="space-y-2">
              {analysis.patterns.map((pattern, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div>
                    <span className="text-sm text-gray-200">{pattern.pattern}</span>
                    <p className="text-xs text-gray-400 mt-1">{pattern.description}</p>
                  </div>
                  <div className="text-xs text-gray-500">
                    {Math.round(pattern.confidence * 100)}% confidence
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Diagrams */}
        {analysisResult.diagrams.length > 0 && (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Architecture Diagrams</h4>
            <div className="space-y-4">
              {analysisResult.diagrams.map((diagram, index) => (
                <div key={index}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-medium text-gray-200">{diagram.title}</span>
                    <span className="text-xs px-2 py-1 bg-gray-700 rounded text-gray-400">{diagram.diagram_type}</span>
                  </div>
                  <p className="text-xs text-gray-400 mb-3">{diagram.description}</p>
                  <div className="bg-gray-700 p-3 rounded text-xs font-mono text-gray-300">
                    {diagram.mermaid_code}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Recommendations */}
        {analysisResult.recommendations.length > 0 && (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Recommendations</h4>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {analysisResult.recommendations.map((rec, index) => (
                <div key={index} className="border-l-2 border-yellow-500 pl-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-200">{rec.title}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      rec.priority === 'high' ? 'bg-red-900 text-red-200' :
                      rec.priority === 'medium' ? 'bg-yellow-900 text-yellow-200' :
                      'bg-green-900 text-green-200'
                    }`}>{rec.priority}</span>
                  </div>
                  <p className="text-xs text-gray-400 mb-1">{rec.description}</p>
                  <div className="text-xs text-gray-500">Impact: {rec.impact}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full bg-gray-900 border-l border-gray-700 flex flex-col">
      {/* Tab Content - No tab navigation, controlled from parent */}
      <div className="flex-1 overflow-hidden">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default AnalysisPanel;