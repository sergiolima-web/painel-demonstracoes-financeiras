@echo off
title Painel de Demonstracoes Financeiras e Acionistas (JEV Engine)
echo ========================================================
echo   PAINEL DE BALANCO, DRE E ACIONISTAS (JEV ENGINE)
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/2] Verificando dependencias do Backend Python...
cd backend
python -m pip install -r requirements.txt --quiet

echo [2/2] Iniciando Servidor Completo com Painel Visual...
start "Backend & Painel Visual" python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

ping 127.0.0.1 -n 4 > nul
echo Abrindo o painel no navegador...
start http://127.0.0.1:8000


echo.
echo ========================================================
echo   SISTEMA ONLINE!
echo   Painel Visual: http://127.0.0.1:8000
echo   API Docs:      http://127.0.0.1:8000/docs
echo ========================================================
echo.
echo Pressione qualquer tecla para fechar esta janela de status (o servidor continuara rodando).
pause > nul



