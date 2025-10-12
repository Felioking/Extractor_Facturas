@echo off
echo Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error instalando dependencias
    pause
    exit /b 1
)
echo Dependencias instaladas correctamente
pause
