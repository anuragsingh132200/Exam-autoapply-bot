@echo off
echo Starting Exam Auto-Apply Bot...

:: Start Backend
echo Launching Backend Server...
start "Backend - Exam Auto-Apply Bot" cmd /k "cd backend && npm install && npm start"

:: Start Frontend
echo Launching Frontend Client...
start "Frontend - Exam Auto-Apply Bot" cmd /k "cd cleint && npm install && npm run dev"

echo All services are starting in separate windows.
pause
