@echo off
REM Face Recognition Pipeline - Windows Stop Script
REM This script stops all services safely

echo.
echo =================================================================
echo 🛑 Stopping Face Recognition Pipeline and Monitoring Services
echo =================================================================
echo.

echo 📊 Stopping monitoring stack...
docker-compose -f docker-compose.monitoring.yml down

echo 🔧 Stopping main application services...
docker-compose down

echo.
echo ✅ All services have been stopped successfully!
echo.
echo 💡 To start again, run: start-windows.bat
echo.
pause
