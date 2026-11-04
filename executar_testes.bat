@echo off
title Validacao Segura - Testes Automatizados (Sandbox)
echo ========================================================
echo   ESTEIRA DE TESTES E HOMOLOGACAO PREVIA (SANDBOX)
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/2] Verificando dependencias de teste (pytest e httpx)...
cd backend
python -m pip install pytest httpx --quiet

echo.
echo [2/2] Executando suíte de testes em ambiente isolado...
python -m pytest tests/test_sistema_seguro.py -v

echo.
echo ========================================================
if %errorlevel% equ 0 (
    echo   [SUCESSO] Todos os testes passaram com seguranca!
    echo   O sistema esta apto e estavel.
) else (
    echo   [FALHA] Foram encontrados erros na validacao.
    echo   Nao suba alteracoes para producao antes de corrigir!
)
echo ========================================================
echo.
pause

