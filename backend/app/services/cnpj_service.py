"""
Serviço de Consulta e Recuperação Cadastral de CNPJ na Receita Federal
Integrado com múltiplos provedores públicos em cascata (BrasilAPI -> ReceitaWS -> MinhaReceita)
Garante alta disponibilidade, resiliência e sanitização estrita de dados.
"""

import re
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("cnpj_service")

def formatar_cnpj(cnpj_limpo: str) -> str:
    """Aplica a máscara padrão XX.XXX.XXX/XXXX-XX no CNPJ numérico de 14 dígitos."""
    if len(cnpj_limpo) == 14:
        return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"
    return cnpj_limpo

def consultar_dados_cnpj(cnpj_bruto: str) -> Dict[str, Any]:
    """
    Consulta os dados cadastrais da empresa na Receita Federal a partir do CNPJ.
    Possui mecanismo de fallback automático:
    1º Provedor: BrasilAPI (Rápido, oficial e sem limites estritos)
    2º Provedor: ReceitaWS (Fallback confiável)
    3º Provedor: MinhaReceita (Rede aberta)
    """
    if not cnpj_bruto:
        return {
            "sucesso": False,
            "erro": "CNPJ não informado."
        }

    # Remove qualquer pontuação ou caracter especial
    cnpj_limpo = re.sub(r"\D", "", cnpj_bruto)

    if len(cnpj_limpo) != 14:
        return {
            "sucesso": False,
            "erro": f"CNPJ inválido ({len(cnpj_limpo)} dígitos). O CNPJ deve conter exatamente 14 números."
        }

    headers = {
        "User-Agent": "PainelDemonstracoesFinanceiras/2.0 (Validador Cadastral)"
    }
    timeout = 6.0

    # -------------------------------------------------------------
    # 1. TENTATIVA COM BRASILAPI
    # -------------------------------------------------------------
    try:
        url_brasilapi = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
        with httpx.Client(timeout=timeout, headers=headers) as client:
            resp = client.get(url_brasilapi)
            if resp.status_code == 200:
                data = resp.json()
                tipo_desc = str(data.get("descricao_identificador_matriz_filial") or "").strip().upper()
                tipo_unidade = "FILIAL" if "FILIAL" in tipo_desc else "MATRIZ"

                # Regime ou Porte
                optante_simples = data.get("opcao_pelo_simples")
                regime = "Simples Nacional" if optante_simples is True else "Lucro Real"

                return {
                    "sucesso": True,
                    "fonte": "Receita Federal (BrasilAPI)",
                    "cnpj": formatar_cnpj(cnpj_limpo),
                    "cnpj_limpo": cnpj_limpo,
                    "razao_social": data.get("razao_social") or "",
                    "nome_fantasia": data.get("nome_fantasia") or data.get("razao_social") or "",
                    "cidade": data.get("municipio") or "",
                    "uf": (data.get("uf") or "").upper(),
                    "tipo_unidade": tipo_unidade,
                    "regime_tributario": regime,
                    "situacao_cadastral": data.get("descricao_situacao_cadastral") or "ATIVA",
                    "logradouro": data.get("logradouro") or "",
                    "bairro": data.get("bairro") or "",
                    "cep": data.get("cep") or ""
                }
            elif resp.status_code == 404:
                return {
                    "sucesso": False,
                    "erro": f"CNPJ {formatar_cnpj(cnpj_limpo)} não encontrado na base da Receita Federal."
                }
    except Exception as ex:
        logger.warning(f"Falha na consulta BrasilAPI para {cnpj_limpo}: {ex}")

    # -------------------------------------------------------------
    # 2. TENTATIVA COM RECEITAWS (FALLBACK)
    # -------------------------------------------------------------
    try:
        url_receitaws = f"https://receitaws.com.br/v1/cnpj/{cnpj_limpo}"
        with httpx.Client(timeout=timeout, headers=headers) as client:
            resp = client.get(url_receitaws)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ERROR":
                    return {
                        "sucesso": False,
                        "erro": data.get("message") or "CNPJ não encontrado."
                    }
                tipo_desc = str(data.get("tipo") or "").strip().upper()
                tipo_unidade = "FILIAL" if "FILIAL" in tipo_desc else "MATRIZ"

                simples_data = data.get("simples") or {}
                optante = simples_data.get("optante")
                regime = "Simples Nacional" if optante is True else "Lucro Real"

                return {
                    "sucesso": True,
                    "fonte": "Receita Federal (ReceitaWS)",
                    "cnpj": formatar_cnpj(cnpj_limpo),
                    "cnpj_limpo": cnpj_limpo,
                    "razao_social": data.get("nome") or "",
                    "nome_fantasia": data.get("fantasia") or data.get("nome") or "",
                    "cidade": data.get("municipio") or "",
                    "uf": (data.get("uf") or "").upper(),
                    "tipo_unidade": tipo_unidade,
                    "regime_tributario": regime,
                    "situacao_cadastral": data.get("situacao") or "ATIVA",
                    "logradouro": data.get("logradouro") or "",
                    "bairro": data.get("bairro") or "",
                    "cep": data.get("cep") or ""
                }
    except Exception as ex:
        logger.warning(f"Falha na consulta ReceitaWS para {cnpj_limpo}: {ex}")

    # -------------------------------------------------------------
    # 3. TENTATIVA COM MINHARECEITA (FALLBACK FINAL)
    # -------------------------------------------------------------
    try:
        url_minhareceita = f"https://minhareceita.org/{cnpj_limpo}"
        with httpx.Client(timeout=timeout, headers=headers) as client:
            resp = client.get(url_minhareceita)
            if resp.status_code == 200:
                data = resp.json()
                tipo_desc = str(data.get("descricao_identificador_matriz_filial") or "").strip().upper()
                tipo_unidade = "FILIAL" if "FILIAL" in tipo_desc else "MATRIZ"

                return {
                    "sucesso": True,
                    "fonte": "Receita Federal (MinhaReceita)",
                    "cnpj": formatar_cnpj(cnpj_limpo),
                    "cnpj_limpo": cnpj_limpo,
                    "razao_social": data.get("razao_social") or "",
                    "nome_fantasia": data.get("nome_fantasia") or data.get("razao_social") or "",
                    "cidade": data.get("municipio") or "",
                    "uf": (data.get("uf") or "").upper(),
                    "tipo_unidade": tipo_unidade,
                    "regime_tributario": "Lucro Real",
                    "situacao_cadastral": data.get("descricao_situacao_cadastral") or "ATIVA",
                    "logradouro": data.get("logradouro") or "",
                    "bairro": data.get("bairro") or "",
                    "cep": data.get("cep") or ""
                }
    except Exception as ex:
        logger.warning(f"Falha na consulta MinhaReceita para {cnpj_limpo}: {ex}")

    return {
        "sucesso": False,
        "erro": "Não foi possível conectar aos servidores da Receita Federal no momento. Preencha os campos manualmente ou tente novamente em instantes."
    }
