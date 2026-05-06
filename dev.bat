@echo off
echo Starting PhotoEarth dev servers...

start "PhotoEarth Backend" cmd /k "cd backend && %USERPROFILE%\.local\bin\uv run uvicorn app.main:app --reload --port 8000"
start "PhotoEarth Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
