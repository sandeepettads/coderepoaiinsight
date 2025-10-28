import { useState, useCallback } from 'react';
import { FileText, ChevronLeft, ChevronRight, 
         AlertCircle, Loader2, Play, CheckCircle, Building2, 
         Shield, TestTube, Code2, Brain, Files } from 'lucide-react';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import FileTree from './components/FileTree';
import CodeEditor from './components/CodeEditor';
import SearchBar from './components/SearchBar';
import ChatPanel from './components/ChatPanel';
import { AnalysisApiService, AnalysisResponse } from './services/apiClient';
import MermaidDiagram from './components/MermaidDiagram';
import CobolAnalysisDisplay from './components/CobolAnalysisDisplay';
import { FileNode, SelectedFile } from './types';
import { buildFileTree, getFileLanguage, countLines } from './utils/fileUtils';

function App() {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<SelectedFile | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [projectName, setProjectName] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [fileCount, setFileCount] = useState(0);
  const [isFileTreeCollapsed, setIsFileTreeCollapsed] = useState(false);
  const [activeAnalysisTab, setActiveAnalysisTab] = useState('architectural');
  const [activeMiddleTab, setActiveMiddleTab] = useState('code');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState<string>('');

  const handleFilesUpload = useCallback(async (uploadedFiles: FileList) => {
    setIsLoading(true);
    const fileArray = Array.from(uploadedFiles);
    setFileCount(fileArray.length);
    setFiles(fileArray);
    
    // Extract project name from the first file's path
    if (fileArray.length > 0) {
      const firstPath = fileArray[0].webkitRelativePath;
      const projectName = firstPath.split('/')[0];
      setProjectName(projectName);
    }
    
    // Use setTimeout to allow UI to update with loading state
    setTimeout(() => {
      const tree = buildFileTree(fileArray);
      setFileTree(tree);
      
      // Auto-expand the root directory
      if (tree.length > 0 && tree[0].type === 'directory') {
        setExpandedFolders(new Set([tree[0].path]));
      }
      
      setIsLoading(false);
    }, 100);
  }, []);

  const handleFileSelect = useCallback(async (fileNode: FileNode) => {
    const file = files.find(f => f.webkitRelativePath === fileNode.path);
    if (file) {
      try {
        const content = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsText(file);
        });

        const selectedFileData: SelectedFile = {
          name: fileNode.name,
          path: fileNode.path,
          content,
          language: getFileLanguage(fileNode.name),
          size: file.size,
          lines: countLines(content)
        };

        setSelectedFile(selectedFileData);
      } catch (error) {
        console.error('Error reading file:', error);
        // Handle binary files or files that can't be read as text
        const selectedFileData: SelectedFile = {
          name: fileNode.name,
          path: fileNode.path,
          content: '// This file cannot be displayed as text (binary file or encoding issue)',
          language: 'plaintext',
          size: file.size,
          lines: 1
        };
        setSelectedFile(selectedFileData);
      }
    }
  }, [files]);

  const handleFolderToggle = useCallback((path: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  }, []);

  const toggleFileTreeCollapse = useCallback(() => {
    setIsFileTreeCollapsed(prev => !prev);
  }, []);

  // Handle architectural analysis
  const handleArchitecturalAnalysis = useCallback(async () => {
    if (files.length === 0) return;
    
    // Check if a file is selected
    if (!selectedFile) {
      setAnalysisError('Please select a file to analyze');
      return;
    }
    
    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisProgress('Starting analysis of selected file...');
    setActiveMiddleTab('analysis'); // Switch to analysis tab
    
    try {
      // Find the selected file in the files array
      const fileToAnalyze = files.find(file => file.webkitRelativePath === selectedFile.path);
      if (!fileToAnalyze) {
        throw new Error('Selected file not found in uploaded files');
      }
      
      // Start analysis with only the selected file
      const response = await AnalysisApiService.startArchitecturalAnalysis(
        [fileToAnalyze], // Only send the selected file
        selectedFile.name, // Use selected file name as project name
        true, // include diagrams
        true  // include recommendations
      );
      
      setAnalysisProgress(`Analyzing ${selectedFile.name}...`);
      
      // Poll for results
      await pollForResults(response.analysis_id);
      
    } catch (error: any) {
      console.error('Analysis failed:', error);
      setAnalysisError(error.response?.data?.detail || error.message || 'Unknown error occurred');
      setIsAnalyzing(false);
    }
  }, [files, projectName, selectedFile]);

  // Handle repository-wide documentation analysis
  const handleRepositoryAnalysis = useCallback(async () => {
    if (files.length === 0) return;
    
    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisProgress('Starting repository analysis...');
    setActiveMiddleTab('documentation'); // Switch to documentation tab
    
    try {
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
      await pollForRepositoryResults(analysisId);

    } catch (error: any) {
      console.error('Repository analysis failed:', error);
      setAnalysisError(error.message || 'Repository analysis failed');
      setIsAnalyzing(false);
    }
  }, [files, projectName]);

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

  const pollForRepositoryResults = async (analysisId: string) => {
    const maxAttempts = 60; // 5 minutes with 5-second intervals
    let attempts = 0;
    
    const poll = async () => {
      try {
        attempts++;
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
          setAnalysisProgress('');
        } else if (statusData.status === 'failed') {
          setAnalysisError(statusData.error_message || 'Repository analysis failed');
          setIsAnalyzing(false);
          setAnalysisProgress('');
        } else if (attempts >= maxAttempts) {
          setAnalysisError('Repository analysis timed out');
          setIsAnalyzing(false);
          setAnalysisProgress('');
        } else {
          // Continue polling
          setAnalysisProgress(`Repository analysis in progress... (${attempts}/${maxAttempts})`);
          setTimeout(poll, 5000);
        }
      } catch (error: any) {
        console.error('Polling error:', error);
        if (attempts >= maxAttempts) {
          setAnalysisError('Failed to get repository analysis results');
          setIsAnalyzing(false);
          setAnalysisProgress('');
        } else {
          setTimeout(poll, 5000);
        }
      }
    };
    
    setTimeout(poll, 2000); // Start polling after 2 seconds
  };

  const renderRepositoryAnalysisContent = (repositoryAnalysis: any) => {
    return (
      <div className="p-6 space-y-6">
        {/* Repository Documentation Header */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-medium text-gray-300">Repository Documentation</span>
            </div>
            <div className="text-xs text-gray-500">
              Generated from {analysisResult?.repository_info.total_files} files
            </div>
          </div>
        </div>

        {/* Documentation Content */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Documentation & Analysis</h4>
          <div className="prose prose-invert prose-sm max-w-none">
            {typeof repositoryAnalysis === 'string' ? (
              <div className="whitespace-pre-wrap text-gray-300 text-sm leading-relaxed">
                {repositoryAnalysis}
              </div>
            ) : (
              <div className="space-y-4">
                {repositoryAnalysis.overview && (
                  <div>
                    <h5 className="text-gray-200 font-medium mb-2">Overview</h5>
                    <p className="text-gray-300 text-sm">{repositoryAnalysis.overview}</p>
                  </div>
                )}
                {repositoryAnalysis.structure && (
                  <div>
                    <h5 className="text-gray-200 font-medium mb-2">Structure Analysis</h5>
                    <p className="text-gray-300 text-sm">{repositoryAnalysis.structure}</p>
                  </div>
                )}
                {repositoryAnalysis.documentation && (
                  <div>
                    <h5 className="text-gray-200 font-medium mb-2">Generated Documentation</h5>
                    <div className="text-gray-300 text-sm whitespace-pre-wrap">
                      {repositoryAnalysis.documentation}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* PlantUML Diagrams if available */}
        {repositoryAnalysis.diagrams && repositoryAnalysis.diagrams.length > 0 && (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Repository Diagrams</h4>
            <div className="space-y-4">
              {repositoryAnalysis.diagrams.map((diagram: any, index: number) => (
                <div key={index}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-medium text-gray-200">{diagram.title || `Diagram ${index + 1}`}</span>
                    <span className="text-xs px-2 py-1 bg-gray-700 rounded text-gray-400">PlantUML</span>
                  </div>
                  <div className="bg-gray-900 border border-gray-600 rounded p-3">
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap overflow-x-auto">
                      {diagram.content || diagram.plantuml_code}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderAnalysisContent = () => {
    if (!analysisResult && !isAnalyzing && !analysisError) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-gray-400 p-8">
          <AlertCircle className="w-12 h-12 mb-4" />
          <h3 className="text-lg font-medium mb-2">No Analysis Results</h3>
          <p className="text-center text-sm">
            Click the Architecture button in the file tree panel to start analysis
          </p>
        </div>
      );
    }

    if (isAnalyzing) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-gray-400 p-8">
          <Loader2 className="w-12 h-12 text-blue-400 animate-spin mb-4" />
          <h3 className="text-lg font-medium mb-2">Analyzing Repository</h3>
          <p className="text-center text-sm mb-4">
            {analysisProgress || 'Processing your code repository...'}
          </p>
        </div>
      );
    }

    if (analysisError) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-red-400 p-8">
          <AlertCircle className="w-12 h-12 mb-4" />
          <h3 className="text-lg font-medium mb-2">Analysis Failed</h3>
          <p className="text-center text-sm mb-4">{analysisError}</p>
          <button 
            onClick={handleArchitecturalAnalysis}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors text-sm"
          >
            <Play className="w-4 h-4" />
            Retry Analysis
          </button>
        </div>
      );
    }

    if (!analysisResult?.architectural_analysis && !analysisResult?.repository_analysis) return null;
    
    // Handle repository analysis (documentation) results
    if (analysisResult.repository_analysis) {
      return renderRepositoryAnalysisContent(analysisResult.repository_analysis);
    }
    
    const analysis = analysisResult.architectural_analysis;
    if (!analysis) return null;
    
    // Check if this is COBOL analysis with structured format
    const isCobolAnalysis = analysisResult.repository_info.primary_language?.toLowerCase() === 'cobol';
    const hasStructuredFormat = typeof analysis.overview === 'string' && 
      (analysis.overview.includes('Call Tree + Pseudocode') || 
       analysis.overview.includes('Data Dictionary & Structural Layout') ||
       analysis.overview.includes('PlantUML Diagrams'));
    
    if (isCobolAnalysis && hasStructuredFormat) {
      return <CobolAnalysisDisplay analysisContent={analysis.overview} />;
    }
    
    return (
      <div className="p-6 space-y-6">
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
                  <MermaidDiagram code={diagram.mermaid_code} />
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

  // Analysis tabs configuration
  const analysisTabs = [
    {
      id: 'architectural',
      title: 'Architectural & Structural Analysis',
      icon: <Building2 className="w-4 h-4" />,
      shortTitle: 'Architecture'
    },
    {
      id: 'quality',
      title: 'Code Quality & Refactoring',
      icon: <Code2 className="w-4 h-4" />,
      shortTitle: 'Quality'
    },
    {
      id: 'documentation',
      title: 'Documentation & Explanation',
      icon: <FileText className="w-4 h-4" />,
      shortTitle: 'Docs'
    },
    {
      id: 'business',
      title: 'Business Logic & Domain Understanding',
      icon: <Brain className="w-4 h-4" />,
      shortTitle: 'Business'
    },
    {
      id: 'security',
      title: 'Security & Vulnerability Analysis',
      icon: <Shield className="w-4 h-4" />,
      shortTitle: 'Security'
    },
    {
      id: 'testing',
      title: 'Testing & Test Case Generation',
      icon: <TestTube className="w-4 h-4" />,
      shortTitle: 'Testing'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <Header />
      <div className="flex h-screen">
        {/* Left Panel - File Tree (collapsible) */}
        <div className={`${isFileTreeCollapsed ? 'w-12' : 'w-1/4 min-w-64'} border-r border-gray-700 bg-gray-800 flex flex-col transition-all duration-300`} style={{ height: 'calc(100vh - 3rem)' }}>
          {/* Header */}
          <div className="p-3 border-b border-gray-700 flex items-center gap-2">
            <button
              onClick={toggleFileTreeCollapse}
              className="p-1 hover:bg-gray-700 rounded transition-colors"
              title={isFileTreeCollapsed ? 'Expand file tree' : 'Collapse file tree'}
            >
              {isFileTreeCollapsed ? (
                <ChevronRight className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronLeft className="w-4 h-4 text-gray-400" />
              )}
            </button>
            {!isFileTreeCollapsed && (
              <>
                <Files className="w-4 h-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-300">
                  {projectName || 'Files'} {fileCount > 0 && `(${fileCount} files)`}
                </span>
              </>
            )}
          </div>

          {!isFileTreeCollapsed && (
            isLoading ? (
              <div className="flex flex-col items-center justify-center h-full p-8">
                <Loader2 className="w-8 h-8 text-blue-400 animate-spin mb-4" />
                <p className="text-gray-300 mb-2">Processing files...</p>
                <p className="text-sm text-gray-500">{fileCount} files uploaded</p>
              </div>
            ) : fileTree.length === 0 ? (
              <FileUpload onFilesUpload={handleFilesUpload} />
            ) : (
              <>
                <SearchBar 
                  searchTerm={searchTerm} 
                  onSearchChange={setSearchTerm} 
                />
                <div className="flex-1 overflow-hidden">
                  <FileTree
                    nodes={fileTree}
                    onFileSelect={handleFileSelect}
                    selectedFile={selectedFile?.path || null}
                    expandedFolders={expandedFolders}
                    onFolderToggle={handleFolderToggle}
                    searchTerm={searchTerm}
                  />
                </div>
              </>
            )
          )}

          {/* Analysis Tab Buttons - Bottom of File Tree Panel */}
          {!isFileTreeCollapsed && fileTree.length > 0 && (
            <div className="border-t border-gray-700 bg-gray-800">
              <div className="p-2 space-y-1">
                {analysisTabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveAnalysisTab(tab.id);
                      if (tab.id === 'architectural') {
                        handleArchitecturalAnalysis();
                      } else if (tab.id === 'documentation') {
                        handleRepositoryAnalysis();
                      }
                    }}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-sm font-medium rounded transition-colors ${
                      activeAnalysisTab === tab.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                    title={tab.title}
                    disabled={(tab.id === 'architectural' || tab.id === 'documentation') && isAnalyzing}
                  >
                    {tab.icon}
                    <span className="text-left">{tab.shortTitle}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Collapsed Analysis Tab Buttons */}
          {isFileTreeCollapsed && (
            <div className="border-t border-gray-700 bg-gray-800 flex-1 flex flex-col justify-center">
              <div className="p-1 space-y-1">
                {analysisTabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveAnalysisTab(tab.id);
                      if (tab.id === 'architectural') {
                        handleArchitecturalAnalysis();
                      } else if (tab.id === 'documentation') {
                        handleRepositoryAnalysis();
                      }
                    }}
                    className={`w-full flex items-center justify-center p-2 rounded transition-colors ${
                      activeAnalysisTab === tab.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                    title={tab.title}
                    disabled={(tab.id === 'architectural' || tab.id === 'documentation') && isAnalyzing}
                  >
                    {tab.icon}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Center Panel - Tabbed Interface (dynamic width) */}
        <div className={`${isFileTreeCollapsed ? 'w-3/5' : 'w-1/2'} bg-gray-900 transition-all duration-300 flex flex-col`} style={{ height: 'calc(100vh - 3rem)' }}>
          {/* Tab Navigation */}
          <div className="border-b border-gray-700 bg-gray-800">
            <div className="flex">
              <button
                onClick={() => setActiveMiddleTab('code')}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeMiddleTab === 'code'
                    ? 'text-blue-400 border-blue-400 bg-gray-700'
                    : 'text-gray-400 border-transparent hover:text-gray-300 hover:bg-gray-750'
                }`}
              >
                <Code2 className="w-4 h-4" />
                Code
              </button>
              <button
                onClick={() => setActiveMiddleTab('analysis')}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeMiddleTab === 'analysis'
                    ? 'text-blue-400 border-blue-400 bg-gray-700'
                    : 'text-gray-400 border-transparent hover:text-gray-300 hover:bg-gray-750'
                }`}
              >
                <Building2 className="w-4 h-4" />
                Analysis
                {isAnalyzing && activeAnalysisTab === 'architectural' && <Loader2 className="w-3 h-3 animate-spin" />}
              </button>
              <button
                onClick={() => setActiveMiddleTab('documentation')}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeMiddleTab === 'documentation'
                    ? 'text-blue-400 border-blue-400 bg-gray-700'
                    : 'text-gray-400 border-transparent hover:text-gray-300 hover:bg-gray-750'
                }`}
              >
                <FileText className="w-4 h-4" />
                Documentation
                {isAnalyzing && activeAnalysisTab === 'documentation' && <Loader2 className="w-3 h-3 animate-spin" />}
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeMiddleTab === 'code' ? (
              <CodeEditor selectedFile={selectedFile} />
            ) : activeMiddleTab === 'documentation' ? (
              <div className="h-full overflow-y-auto">
                {analysisResult?.repository_analysis ? 
                  renderRepositoryAnalysisContent(analysisResult.repository_analysis) :
                  <div className="flex flex-col items-center justify-center h-full text-gray-400 p-8">
                    <FileText className="w-12 h-12 mb-4" />
                    <h3 className="text-lg font-medium mb-2">No Documentation Results</h3>
                    <p className="text-center text-sm">
                      Click the Docs button in the file tree panel to generate repository documentation
                    </p>
                  </div>
                }
              </div>
            ) : (
              <div className="h-full overflow-y-auto">
                {renderAnalysisContent()}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Chat Panel (dynamic width) */}
        <div className={`${isFileTreeCollapsed ? 'w-2/5' : 'w-1/4'} min-w-80 transition-all duration-300`} style={{ height: 'calc(100vh - 3rem)' }}>
          <ChatPanel selectedFile={selectedFile} />
        </div>
      </div>
    </div>
  );
}

export default App;