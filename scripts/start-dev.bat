@echo off
setlocal enabledelayedexpansion

REM Ir a la raiz del proyecto
cd /d "%~dp0\.."

REM Crear venv global si no existe
if not exist ".venv" (
    echo Creando entorno virtual global...
    python -m venv .venv
)

REM Activar venv global
call .venv\Scripts\activate.bat

REM Instalar dependencias de backend
echo Instalando dependencias del backend...
if exist "backend\requirements.txt" (
    pip install -r backend\requirements.txt -q
)

REM Instalar dependencias de frontend
echo Instalando dependencias del frontend...
if exist "frontend\requirements.txt" (
    pip install -r frontend\requirements.txt -q
)

REM Abrir backend en terminal separada
echo Iniciando backend...
start cmd /k "cd backend && call ..\.venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload"

REM Abrir frontend en terminal separada
timeout /t 3 /nobreak
echo Iniciando frontend...
start cmd /k "cd frontend && call ..\.venv\Scripts\activate.bat && reflex run --backend-port 8001"

echo.
echo Backend y frontend lanzados en terminales separadas.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
pause
