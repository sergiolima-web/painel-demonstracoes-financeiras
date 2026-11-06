# 🛡️ Especificação Técnica: Blindagem de Segurança 360° para Nuvem (EGM Protocol)

**Autor (O Elefante):** Sessão Principal de Arquitetura  
**Protocolo:** Elephant-Goldfish Model (EGM) + Zero Trust + OWASP Top 10  
**Data:** 2026-11-05  
**Alvo:** Backend FastAPI, Frontend React e Endpoints em Produção (`onrender.com`)  

---

## 1. 🎯 Objetivo e Escopo
Eliminar todas as vulnerabilidades da aplicação em ambiente de nuvem pública, aplicando o princípio de **Defesa em Camadas (*Defense-in-Depth*)** e os pilares das nossas Skills (`rag-security`, `typesafe-jev`, `AGENTS.md` Seção 2).

### Vetores de Ameaça Cobertos:
1. **Acesso Não Autorizado aos Dados:** Qualquer pessoa com o link da Render ver os números contábeis;
2. **Negação de Serviço (DoS / Flood de Requisições):** Robôs sobrecarregarem o chat ou uploads;
3. **Ataques Web Modernos (OWASP):** Clickjacking, MIME-sniffing e sequestro de iframe;
4. **CORS Excessivamente Permissivo:** Bloqueio de chamadas externas não autorizadas.

---

## 2. 🧱 As 4 Camadas de Proteção Especificadas

### Camada 1: Headers de Segurança Web (OWASP Top 10)
Adicionar middleware HTTP global no FastAPI que injeta em todas as respostas:
* `X-Frame-Options: DENY` (Impede o painel de ser embutido em iframes maliciosos);
* `X-Content-Type-Options: nosniff` (Força o navegador a respeitar os tipos MIME);
* `Strict-Transport-Security: max-age=31536000; includeSubDomains` (Força HTTPS em toda a navegação);
* `X-XSS-Protection: 1; mode=block` (Barreira contra cross-site scripting);
* `Referrer-Policy: strict-origin-when-cross-origin`.

### Camada 2: Restrição Estrita de CORS
Substituir o `allow_origins=["*"]` por lista controlada:
* O domínio de produção na nuvem: `https://painel-demonstracoes-financeiras.onrender.com`
* Os domínios locais de homologação: `http://127.0.0.1:8000`, `http://localhost:8000`
* Suporte à variável de ambiente `CORS_ALLOWED_ORIGINS` para novos domínios customizados.

### Camada 3: Rate Limiting em Memória (Proteção contra Flood/DoS)
* Criar limitador de requisições por IP cliente (`RateLimiter`):
  * Rotas padrão: até 60 requisições/minuto;
  * Rotas sensíveis (`/api/chat/agente-financeiro`, `/api/upload-demonstracao`): até 20 requisições/minuto;
  * Se exceder, retorna HTTP 429 (`Too Many Requests`) com aviso amigável.

### Camada 4: Autenticação de Acesso dos Acionistas (PIN / Token de Acesso)
* **No Backend (`.env`):** Variável opcional `PAINEL_ACCESS_TOKEN` (se configurada, ativa a exigência de chave de acesso);
* **Endpoint de Autenticação:** `POST /api/auth/verificar-acesso` que valida o token e retorna status aprovado;
* **No Frontend:** Modal elegante de bloqueio inicial se o token for requerido, solicitando o PIN/Chave de Acesso do Acionista e guardando na sessão (`sessionStorage`).

---

## 3. 🧪 Plano de Homologação (Seção 7 do AGENTS.md)
Criar casos de teste no `backend/tests/test_sistema_seguro.py`:
1. `test_headers_seguranca_owasp`: Verifica presença de HSTS, X-Frame-Options e nosniff em todas as rotas;
2. `test_rate_limiter_bloqueio_flood`: Simula rajada rápida de requisições e verifica retorno 429;
3. `test_cors_restrito`: Verifica rejeição ou cabeçalhos adequados para origens externas não autorizadas;
4. `test_autenticacao_acesso_acionista`: Valida autenticação por token correto e bloqueio com token inválido.

