# RepoInsight AI - Integration Testing Guide

## Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key (already configured)
   ```

4. **Start the FastAPI backend:**
   ```bash
   python main.py
   ```
   Backend will run on: http://localhost:8000

## Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd RepoInsightAI
   ```

2. **Install dependencies (already done):**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   Frontend will run on: http://localhost:5173

## Testing the Integration

### Step 1: Verify Backend Health
- Visit: http://localhost:8000/health
- Should return: `{"status":"healthy","timestamp":"...","service":"RepoInsight AI Backend"}`

### Step 2: Test Frontend
1. Open: http://localhost:5173
2. Upload a code repository (folder with multiple files)
3. Wait for files to load in the file tree
4. Click on "Architectural & Structural Analysis" tab (right panel)
5. Click "Run Architectural Analysis" button

### Step 3: Monitor Analysis Progress
- Watch the progress messages in the Analysis Panel
- Backend will process files and call OpenAI GPT
- Results will appear automatically when complete

### Expected Results
- Repository overview with file count and language detection
- Architectural components list
- Detected patterns with confidence scores
- Interactive Mermaid diagrams (sequence, component, integration)
- Actionable recommendations

## Troubleshooting

### Backend Issues
- Check OpenAI API key is valid
- Verify port 8000 is available
- Check console for error messages

### Frontend Issues
- Ensure backend is running on port 8000
- Check browser console for API errors
- Verify file upload permissions

### Analysis Issues
- Large files (5000+ lines) may take 2-5 minutes
- Check OpenAI API rate limits
- Monitor backend logs for chunking details

## Test Files
For testing, try uploading:
- Small Python/JavaScript projects (< 1000 lines)
- Medium repositories (1000-5000 lines)
- Large COBOL files (5000+ lines)

The system will automatically chunk large files and provide comprehensive architectural analysis.
