@echo off
title Enviar Projeto para o GitHub
cd /d "%~dp0"
echo ========================================================
echo   ENVIANDO CODIGO PARA O GITHUB (BRANCH MAIN)
echo   Repositorio: sergiolima-web/painel-demonstracoes-financeiras
echo ========================================================
echo.
echo Se abrir uma janela no navegador, clique em "Sign in with your browser" ou "Authorize".
echo.
git push -u origin main
echo.
if %errorlevel% equ 0 (
    echo ========================================================
    echo   [SUCESSO] Seu projeto ja esta publicado no GitHub!
    echo   Acesse: https://github.com/sergiolima-web/painel-demonstracoes-financeiras
    echo ========================================================
) else (
    echo ========================================================
    echo   [AVISO] Houve uma falha de autenticacao.
    echo ========================================================
)
echo.
pause

