@echo off
REM Script para compilar e executar Batalha Naval no Windows

echo.
echo ╔════════════════════════════════════════╗
echo ║   Batalha Naval - Jogo em Java Swing   ║
echo ╚════════════════════════════════════════╝
echo.

REM Verificar se Java está instalado
javac -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Erro: Java Development Kit (JDK) nao esta instalado!
    echo.
    echo Instale o JDK seguindo as instrucoes em INSTRUCOES_EXECUCAO.md
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('java -version 2^>^&1') do (
    echo ✓ Java encontrado: %%i
    goto :compile
)

:compile
echo.
echo 🔨 Compilando...
javac BatalhaNavalLogic.java BatalhaNavalGUI.java

if %errorlevel% neq 0 (
    echo ❌ Erro na compilacao!
    pause
    exit /b 1
)

echo ✓ Compilacao bem-sucedida!
echo.
echo 🎮 Iniciando o jogo...
echo.

java BatalhaNavalGUI
pause
