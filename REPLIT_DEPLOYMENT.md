# RepoInsight AI - Replit Deployment Guide

## Deployment Configuration

### Build Command
```bash
bash build.sh
```

### Run Command
```bash
bash start.sh
```

## Configuration Details

### Files Created for Replit
- `build.sh` - Builds both backend and frontend
- `start.sh` - Starts both services simultaneously  
- `requirements.txt` - Root-level Python dependencies
- `.replit` - Replit configuration file

### Environment Variables (Deployment Secrets)
Add these in Replit's "Deployment secrets" section:

**Required:**
- `OPENAI_API_KEY` - Your OpenAI API key

**Optional (with defaults):**
- `ENVIRONMENT` - Set to `production` (default: `development`)
- `DEBUG` - Set to `False` (default: `True`)
- `LOG_LEVEL` - Set to `INFO` (default: `INFO`)

### Ports
- **Backend (FastAPI)**: Port 8000
- **Frontend (React/Vite)**: Port 5173

### How It Works

1. **Build Phase**: 
   - Installs Python dependencies from `requirements.txt`
   - Installs Node.js dependencies in `RepoInsightAI/` folder

2. **Run Phase**:
   - Starts FastAPI backend on port 8000 (background process)
   - Starts Vite dev server on port 5173 (foreground process)
   - Frontend proxies API requests to backend via `/api` route

### Accessing the Application

- **Frontend**: Your Replit app URL (port 5173)
- **Backend API**: Your Replit app URL + `/api` (proxied to port 8000)
- **API Docs**: Your Replit app URL + `/api/docs`

### Project Structure
```
.
├── backend/              # FastAPI backend
│   ├── main.py
│   ├── api/
│   ├── services/
│   └── utils/
├── RepoInsightAI/        # React frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── build.sh              # Build script
├── start.sh              # Startup script
├── requirements.txt      # Python dependencies
└── .replit              # Replit config
```

## Troubleshooting

### Build Fails
- Ensure all dependencies are listed in `requirements.txt` and `package.json`
- Check that Node.js version is compatible (v16+)

### Backend Not Starting
- Verify `OPENAI_API_KEY` is set in deployment secrets
- Check logs for port conflicts

### Frontend Can't Connect to Backend
- Ensure both services are running
- Check that proxy configuration in `vite.config.ts` is correct
- Verify CORS settings in `backend/main.py`

## Manual Deployment Commands

If you need to deploy manually:

```bash
# Build
pip install -r requirements.txt
cd RepoInsightAI && npm install && cd ..

# Run
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 &
cd RepoInsightAI && npm run dev -- --host 0.0.0.0 --port 5173
```
