# 🐘 Especificação de Auditoria Geral da Base de Código (EGM Protocol)

**Data:** 02/11/2026  
**Status:** Em Auditoria (Aguardando Parecer do Goldfish)  
**Autor:** Agente Elefante  
**Alvo:** Backend (FastAPI), Frontend (React/TS), Segurança Zero Trust e Conformidade Contábil

---

## 🎯 1. Objetivo da Auditoria
Realizar uma varredura rigorosa, aprofundada e crítica em toda a base de código do projeto de Análise de Demonstrações Financeiras para identificar:
1. **Fragilidades de Segurança e Zero Trust:** Exposição de chaves, sanitização de inputs, proteção contra path traversal em uploads, vazamento de exceções e CORS.
2. **Integridade das Fórmulas Contábeis:** Riscos de divisão por zero em indicadores econômico-financeiros, consistência entre Ativo, Passivo e PL, integridade da DRE.
3. **Robustez do Serviço JEV (TypeSafe):** Fallbacks caso a chave/serviço esteja indisponível, badges visuais `⚡🧠` no frontend, consistência de payloads.
4. **Resiliência e Qualidade do Frontend:** Tratamento de erros de rede no Axios, tipagem TypeScript estrita, estados de loading e feedback ao usuário.
5. **Cobertura de Testes Automatizados:** Suficiência da suíte em `backend/tests/test_sistema_seguro.py`.

---

## 📁 2. Arquivos no Escopo da Auditoria
* **Backend:**
  - `backend/app/main.py`
  - `backend/app/services/jev_service.py`
  - `backend/app/services/calculos_indices.py`
  - `backend/app/services/planilha_service.py`
  - `backend/app/services/pdf_service.py`
  - `backend/app/services/matriz_empresa_service.py`
  - `backend/tests/test_sistema_seguro.py`
  - `backend/.env.example` e `.gitignore`
* **Frontend:**
  - `frontend/src/App.tsx`
  - `frontend/src/services/api.ts`
  - `frontend/src/types/financeiro.ts`
  - `frontend/src/components/EnsinoJevView.tsx`
  - `frontend/src/components/BalancoView.tsx`
  - `frontend/src/components/DreView.tsx`
  - `frontend/src/components/IndicesView.tsx`

---

## 🔍 3. Critérios de Avaliação do Auditor Goldfish
O auditor deve avaliar cada módulo sob uma postura estritamente cética e pontuar:
- [CRÍTICO] Falha grave de segurança ou quebra funcional garantida.
- [ALERTA] Risco de inconsistência, falta de tratamento de exceção ou violação de diretriz.
- [MELHORIA] Oportunidade de refatoração para robustez, legibilidade ou performance.

