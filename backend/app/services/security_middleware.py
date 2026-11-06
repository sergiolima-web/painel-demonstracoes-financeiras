"""
========================================================================================
🛡️ SERVIÇO DE MIDDLEWARE DE SEGURANÇA E RATE LIMITING (EGM Protocol)
========================================================================================
Implementa:
1. Rate Limiting em memória por IP (proteção contra DoS / Flood);
2. Headers de Segurança Web (OWASP Top 10, CSP calibrada, Anti-Clickjacking);
3. Controle de Acesso Zero Trust (Validação de Token de Acionistas no Backend).
========================================================================================
"""

import os
import time
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

# --------------------------------------------------------------------------------------
# 1. Rate Limiter em Memória com Janela Deslizante
# --------------------------------------------------------------------------------------
class InMemoryRateLimiter:
    """
    Controla a frequência de requisições por IP cliente.
    Possui bypass automático para suíte de testes (testclient) e separa buckets de leitura e escrita.
    """
    def __init__(self, limite_padrao_minuto: int = 300, limite_sensivel_minuto: int = 60):
        self.limite_padrao = limite_padrao_minuto
        self.limite_sensivel = limite_sensivel_minuto
        self.historico_ips: Dict[str, List[float]] = {}

    def verificar_limite(self, request: Request, eh_rota_sensivel: bool = False) -> Tuple[bool, int]:
        # 1. Bypass mandatória apontada pelo Goldfish para não quebrar a suíte de testes (testclient)
        client_ip = request.client.host if request.client else "unknown"
        if client_ip == "testclient" or os.getenv("TESTING", "").lower() == "true":
            return True, 0

        chave_bucket = f"{client_ip}:sensivel" if eh_rota_sensivel else f"{client_ip}:padrao"
        limite = self.limite_sensivel if eh_rota_sensivel else self.limite_padrao
        agora = time.time()
        janela = agora - 60.0  # Janela de 1 minuto

        # Limpa requisições mais antigas que 1 minuto
        if chave_bucket not in self.historico_ips:
            self.historico_ips[chave_bucket] = []

        self.historico_ips[chave_bucket] = [t for t in self.historico_ips[chave_bucket] if t > janela]

        if len(self.historico_ips[chave_bucket]) >= limite:
            tempo_espera = int(60.0 - (agora - self.historico_ips[chave_bucket][0]))
            return False, max(1, tempo_espera)

        self.historico_ips[chave_bucket].append(agora)
        return True, 0

rate_limiter = InMemoryRateLimiter()

# --------------------------------------------------------------------------------------
# 2. Middleware de Headers OWASP Top 10 & CSP Calibrada
# --------------------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injeta headers de segurança em todas as respostas HTTP, respeitando a calibração
    da auditoria Goldfish para não quebrar React/Babel/Tailwind CDN.
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Rate limiting pré-processamento
        rota_sensivel = any(request.url.path.startswith(p) for p in ["/api/chat", "/api/upload", "/api/limpar-dados"])
        permitido, tempo_espera = rate_limiter.verificar_limite(request, eh_rota_sensivel=rota_sensivel)

        if not permitido:
            return JSONResponse(
                status_code=429,
                content={
                    "erro": True,
                    "mensagem": f"Limite de requisições excedido. Por favor, aguarde {tempo_espera} segundos.",
                    "detalhe": "Too Many Requests (Rate Limit Exceeded)"
                },
                headers={"Retry-After": str(tempo_espera)}
            )

        response: Response = await call_next(request)

        # 2. Injeção de Headers OWASP
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # HSTS ativo para requisições seguras
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content-Security-Policy calibrada pelo Goldfish (permite CDNs necessárias sem tela branca)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' https://painel-demonstracoes-financeiras.onrender.com; "
            "frame-ancestors 'none';"
        )

        return response

# --------------------------------------------------------------------------------------
# 3. Autenticação Zero Trust no Backend (Validação de Token de Acionistas)
# --------------------------------------------------------------------------------------
API_KEY_HEADER = APIKeyHeader(name="X-Access-Token", auto_error=False)

def verificar_token_acesso(token_recebido: Optional[str] = Security(API_KEY_HEADER)) -> bool:
    """
    Dependência FastAPI:
    Se PAINEL_ACCESS_TOKEN estiver configurado no .env, exige validação estrita no backend.
    Se não estiver configurado (modo local aberto), permite acesso sem fricção.
    """
    token_esperado = os.getenv("PAINEL_ACCESS_TOKEN", "").strip()
    
    # Se nenhuma senha foi definida no .env, o sistema roda aberto localmente
    if not token_esperado:
        return True

    if not token_recebido or token_recebido != token_esperado:
        raise HTTPException(
            status_code=401,
            detail="Acesso não autorizado. Chave de acesso de acionista inválida ou ausente.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    return True

