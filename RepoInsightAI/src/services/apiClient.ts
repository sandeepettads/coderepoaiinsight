import axios, { AxiosResponse } from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for large analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types for API responses
export interface RepositoryInfo {
  name: string;
  total_files: number;
  total_lines: number;
  total_size: number;
  primary_language: string;
  languages: string[];
  analysis_duration?: string;
}

export interface ArchitecturalComponent {
  component_name: string;
  type: string;
  responsibilities: string[];
  dependencies: string[];
  file_paths: string[];
}

export interface DiagramData {
  title: string;
  mermaid_code: string;
  description: string;
  diagram_type: string;
}

export interface ArchitecturalPattern {
  pattern: string;
  confidence: number;
  evidence: string[];
  description: string;
}

export interface Recommendation {
  category: string;
  priority: string;
  title: string;
  description: string;
  impact: string;
}

export interface ArchitecturalAnalysis {
  overview: string;
  components: ArchitecturalComponent[];
  patterns: ArchitecturalPattern[];
  dependencies: string[];
  external_integrations: string[];
}

export interface AnalysisResponse {
  analysis_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  repository_info: RepositoryInfo;
  architectural_analysis?: ArchitecturalAnalysis;
  diagrams: DiagramData[];
  recommendations: Recommendation[];
  insights: string[];
  created_at: string;
  completed_at?: string;
  error_message?: string;
  repository_analysis?: any;
}

// API Service Class
export class AnalysisApiService {
  
  static async startArchitecturalAnalysis(
    files: File[], 
    projectName?: string,
    includeDiagrams: boolean = true,
    includeRecommendations: boolean = true
  ): Promise<AnalysisResponse> {
    const formData = new FormData();
    
    // Add files to form data
    files.forEach(file => {
      formData.append('files', file);
    });
    
    // Add optional parameters
    if (projectName) {
      formData.append('project_name', projectName);
    }
    formData.append('include_diagrams', includeDiagrams.toString());
    formData.append('include_recommendations', includeRecommendations.toString());
    
    const response: AxiosResponse<AnalysisResponse> = await apiClient.post(
      '/api/analyze/architectural',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    return response.data;
  }
  
  static async getAnalysisStatus(analysisId: string): Promise<AnalysisResponse> {
    const response: AxiosResponse<AnalysisResponse> = await apiClient.get(
      `/api/analysis/${analysisId}/status`
    );
    return response.data;
  }
  
  static async getAnalysisResults(analysisId: string): Promise<AnalysisResponse> {
    const response: AxiosResponse<AnalysisResponse> = await apiClient.get(
      `/api/analysis/${analysisId}/results`
    );
    return response.data;
  }
  
  static async checkHealth(): Promise<{ status: string; timestamp: string; service: string }> {
    const response = await apiClient.get('/health');
    return response.data;
  }
}

// Error handling interceptor
apiClient.interceptors.response.use(
  (response: any) => response,
  (error: any) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
