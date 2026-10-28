@echo off
REM Deploy script for Agent-Infra Healing System (Windows)

echo ==========================================
echo Agent-Infra Healing System - Deployment
echo ==========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Docker not found. Please install Docker Desktop first.
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo X Docker Compose not found.
        exit /b 1
    )
)

echo √ Docker and Docker Compose found
echo.

REM Create .env file if not exists
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo.
    echo WARNING: Please edit .env and add your API keys:
    echo    - ANTHROPIC_API_KEY
    echo    - OPENAI_API_KEY ^(optional^)
    echo.
    pause
)

REM Start services
echo Starting services...
docker-compose up -d

echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo ==========================================
echo Deployment Complete!
echo ==========================================
echo.
echo Services:
echo   - Prometheus: http://localhost:9090
echo   - Grafana: http://localhost:3000 ^(admin/admin^)
echo   - Kibana: http://localhost:5601
echo   - Demo App: http://localhost:8080
echo.
echo View logs:
echo   docker-compose logs -f agent-system
echo.
echo Inject faults:
echo   curl -X POST http://localhost:8080/inject/errors -H "Content-Type: application/json" -d "{\"rate\": 0.5}"
echo   curl -X POST http://localhost:8080/inject/latency
echo.
echo Recover:
echo   curl -X POST http://localhost:8080/recover
echo.
echo Stop system:
echo   docker-compose down
echo.
pause
