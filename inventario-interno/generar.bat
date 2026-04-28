@echo off
chcp 65001 >nul
echo.
echo  Pinturas Autos Torres — Generador de Inventario
echo  ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado.
    echo.
    echo Descárgalo en: https://www.python.org/downloads/
    echo Marca la opción "Add Python to PATH" al instalar.
    echo.
    pause
    exit /b 1
)

pip install pandas openpyxl xlrd -q

python "%~dp0procesar_inventario.py"
