@echo off
setlocal enabledelayedexpansion
title Iniciador PRO - FastAPI + Frontend + Ngrok

:: ==================================================
:: UBICARSE EN LA RAIZ DONDE ESTA ESTE .BAT
:: ==================================================
cd /d "%~dp0"

echo ==========================================
echo   INICIANDO PROYECTO COMPLETO - VERSION PRO
echo ==========================================
echo.

:: ==================================================
:: VALIDAR CARPETAS
:: ==================================================
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual en /venv
    pause
    exit
)

if not exist "backend" (
    echo [ERROR] No se encontro carpeta /backend
    pause
    exit
)

if not exist "frontend" (
    echo [ERROR] No se encontro carpeta /frontend
    pause
    exit
)

:: ==================================================
:: CERRAR PROCESOS ANTERIORES (OPCIONAL)
:: ==================================================
echo Cerrando procesos anteriores...
taskkill /f /im ngrok.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1

:: ==================================================
:: ABRIR VS CODE
:: ==================================================
echo Abriendo VS Code...
start "" code .

timeout /t 2 /nobreak >nul

:: ==================================================
:: BACKEND FASTAPI
:: ==================================================
echo Iniciando Backend...
start "BACKEND" cmd /k "cd /d %~dp0backend && call ..\venv\Scripts\activate && uvicorn app.main:app --reload"

:: ==================================================
:: ESPERAR BACKEND
:: ==================================================
echo Esperando backend...
timeout /t 6 /nobreak >nul

:: ==================================================
:: FRONTEND
:: ==================================================
echo Iniciando Frontend...
start "FRONTEND" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 6 /nobreak >nul

:: ==================================================
:: NGROK
:: ==================================================
echo Iniciando Ngrok...
start "NGROK" cmd /k "ngrok http 8000"

timeout /t 5 /nobreak >nul

:: ==================================================
:: ABRIR NAVEGADOR
:: ==================================================
start http://localhost:8000/docs

echo.
echo ==========================================
echo TODO INICIADO CORRECTAMENTE
echo ==========================================
echo Backend   : http://localhost:8000
echo Swagger   : http://localhost:8000/docs
echo Frontend  : revisar ventana FRONTEND
echo Ngrok     : revisar ventana NGROK
echo ==========================================
pause
