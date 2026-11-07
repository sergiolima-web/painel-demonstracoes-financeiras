import os
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Response, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.services.jev_service import jev_service
from app.services.agente_langgraph_service import agente_langgraph
from app.services.planilha_service import gerar_modelo_planilha_exemplo, processar_demonstracoes_com_jev
from app.services.pdf_service import gerar_modelo_pdf_exemplo, processar_pdf_demonstracoes_com_jev
from app.services.matriz_empresa_service import conglutinador_jev, ESTRUTURA_MATRIZ_PADRAO
from app.services.empresas_plano_contas_service import empresas_plano_service
from app.services.cnpj_service import consultar_dados_cnpj
from app.services.security_middleware import SecurityHeadersMiddleware, verificar_token_acesso
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI(
    title="API de Análise de Demonstrações Financeiras & Acionistas",
    description="Motor de cálculo de Balanço Patrimonial, DRE, Índices Financeiros e Integração JEV TypeSafe",
    version="1.0.0"
)

# Monta diretório de arquivos estáticos (imagens, ícones e assets)
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Origens permitidas estritas para CORS (Ambiente Local + Nuvem Render)
origens_permitidas = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://painel-demonstracoes-financeiras.onrender.com"
]

# Permite adicionar novas origens por variável de ambiente sem alterar código
origens_custom = os.getenv("CORS_ALLOWED_ORIGINS", "")
if origens_custom:
    origens_permitidas.extend([o.strip() for o in origens_custom.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Adiciona Middleware de Headers OWASP e Rate Limiting
app.add_middleware(SecurityHeadersMiddleware)

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

ultimo_documento_ativo = None

@app.get("/", response_class=HTMLResponse)
def painel_principal():
    """
    Entrega o Painel Visual Executivo Completo com React, Tailwind e JEV integrado.
    Garante que o navegador nunca sirva versão em cache antigo.
    """
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            conteudo = f.read()
            return HTMLResponse(
                content=conteudo,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    return HTMLResponse("<h1>Painel Financeiro Online</h1>")

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "sistema": "Painel de Balanço e DRE para Acionistas",
        "versao": "1.0.0"
    }

@app.get("/api/status-jev")
def status_jev():
    ativo = jev_service.esta_ativo()
    return {
        "jev_habilitado": ativo,
        "icone": "⚡🧠",
        "badge": "⚡🧠 JEV Decision Engine",
        "mensagem": "JEV TypeSafe configurado e pronto para uso" if ativo else "Chave JEV não informada no .env (utilizando fallback determinístico)"
    }

from pydantic import BaseModel

class RegraDeParaRequest(BaseModel):
    termo_origem: str
    conta_matriz_id: str
    conta_matriz_nome: str
    observacao: str = ""

@app.get("/api/matriz-empresa")
def obter_matriz_empresa():
    """
    Retorna a DRE Conglutinada na Matriz Corporativa da Empresa com os valores padrão da imagem.
    """
    return conglutinador_jev.conglutinar_dados_na_matriz([])

@app.get("/api/matriz-empresa/estrutura")
def obter_estrutura_matriz():
    """
    Retorna a estrutura pura da árvore da matriz de contas corporativas.
    """
    return {"estrutura": ESTRUTURA_MATRIZ_PADRAO}

@app.get("/api/regras-depara")
def listar_regras_depara():
    """
    Lista todas as regras de conglutinação semântica e De-Para cadastradas para o JEV.
    """
    return {"regras": conglutinador_jev.listar_regras_depara()}

@app.post("/api/regras-depara")
def cadastrar_regra_depara(req: RegraDeParaRequest):
    """
    Cadastra uma nova regra de De-Para / Particularidade para o motor JEV aprender.
    """
    regra = conglutinador_jev.adicionar_regra_depara(
        termo_origem=req.termo_origem,
        conta_matriz_id=req.conta_matriz_id,
        conta_matriz_nome=req.conta_matriz_nome,
        observacao=req.observacao
    )
    return {"status": "sucesso", "mensagem": "Regra cadastrada com sucesso no JEV!", "regra": regra}

@app.delete("/api/regras-depara/{regra_id}")
def remover_regra_depara(regra_id: str):
    """
    Remove uma regra de De-Para cadastrada.
    """
    removido = conglutinador_jev.remover_regra_depara(regra_id)
    return {"status": "sucesso" if removido else "erro", "removido": removido}

@app.get("/api/modelo-planilha")
def baixar_modelo_planilha():
    """
    Retorna o modelo de planilha Excel (.xlsx) contendo abas estruturadas de Balanço e DRE.
    """
    conteudo_bytes = gerar_modelo_planilha_exemplo()
    return Response(
        content=conteudo_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Modelo_Balanco_DRE_Acionistas.xlsx"}
    )

@app.get("/api/modelo-pdf")
def baixar_modelo_pdf():
    """
    Retorna o modelo executivo em PDF de alta fidelidade contendo
    Balanço Patrimonial e DRE para testes e auditoria.
    """
    conteudo_bytes = gerar_modelo_pdf_exemplo()
    return Response(
        content=conteudo_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Modelo_Balanco_DRE_Acionistas.pdf"}
    )

def _criar_documento_zerado_limpo() -> dict:
    """
    Gera a estrutura contábil 100% zerada e limpa para todos os exercícios (2026, 2025, 2024, 2023),
    garantindo que o banco de dados em memória nunca inicie com valores fantasmas ou resíduos não autorizados.
    """
    from app.services.calculos_indices import CalculadoraIndicesFinanceiros
    anos_padrao = ["2026", "2025", "2024", "2023"]
    matriz_vazia = conglutinador_jev.conglutinar_dados_na_matriz([])
    balanco_vazio = {
        "ativo_circulante": 0.0,
        "ativo_nao_circulante": 0.0,
        "ativo_total": 0.0,
        "passivo_circulante": 0.0,
        "passivo_nao_circulante": 0.0,
        "patrimonio_liquido": 0.0,
        "passivo_total": 0.0,
        "disponibilidades": 0.0
    }
    dre_vazio = {"receita_bruta": 0.0, "lucro_liquido": 0.0}
    indices_vazios = CalculadoraIndicesFinanceiros.calcular_todos_indices(
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    )
    parecer_vazio = jev_service.gerar_solucoes_gestao_jev(
        indices=indices_vazios,
        totais_balanco=balanco_vazio,
        totais_dre=dre_vazio
    )

    return {
        "arquivo": "Base_Limpa_Corporativa",
        "formato": "Sessão Limpa (Aguardando Importação)",
        "tipo_documento": "Balanço & DRE Completo",
        "aba_sugerida": "matriz",
        "somente_dre": False,
        "total_linhas_lidas": 0,
        "balanco_equilibrado": True,
        "diferenca_balanco": 0.0,
        "totais_balanco": dict(balanco_vazio),
        "totais_balanco_por_ano": {a: dict(balanco_vazio) for a in anos_padrao},
        "totais_dre": dict(dre_vazio),
        "totais_dre_por_ano": {a: dict(dre_vazio) for a in anos_padrao},
        "indices_financeiros": dict(indices_vazios),
        "indicadores_por_ano": {a: dict(indices_vazios) for a in anos_padrao},
        "indicadores_por_periodo": {p: dict(indices_vazios) for p in ["1T", "2T", "3T", "4T", "anual"]},
        "anos_disponiveis": list(anos_padrao),
        "ano_ativo": "2026",
        "trimestres_autorizados": ["1T", "2T", "3T", "4T"],
        "parecer_gestao_jev": parecer_vazio,
        "dre_matriz_empresa": matriz_vazia,
        "dre_matriz_por_ano": {a: conglutinador_jev.conglutinar_dados_na_matriz([]) for a in anos_padrao},
        "contas_detalhadas": [],
        "itens_dre": [],
        "destaques_acionistas": [],
        "motor_ia": {
            "icone": "⚡🧠",
            "nome": "TypeSafe JEV (System 1 Decision Engine)",
            "status": "Base de Dados Limpa e Pronta para Importação"
        }
    }

@app.get("/api/dados-demonstracao-padrao")
def obter_dados_padrao(_auth: bool = Depends(verificar_token_acesso)):
    """
    Retorna o documento ativo atual (último arquivo importado) ou a estrutura limpa zerada.
    Preserva rigorosamente os estados de zeramento e os anos disponíveis.
    """
    global ultimo_documento_ativo
    if ultimo_documento_ativo is None:
        ultimo_documento_ativo = _criar_documento_zerado_limpo()

    # Garante que os anos padrão nunca sumam da lista
    anos_atuais = set(ultimo_documento_ativo.get("anos_disponiveis", []))
    anos_atuais.update(["2026", "2025", "2024", "2023"])
    ultimo_documento_ativo["anos_disponiveis"] = sorted(list(anos_atuais), reverse=True)
    return ultimo_documento_ativo

@app.post("/api/banco-dados/expurgar-tudo")
def expurgar_banco_dados_completo():
    """
    Varre o banco de dados em memória e exclui/zera absolutamente todos os valores
    de todos os anos e trimestres, deixando a base 100% limpa.
    """
    global ultimo_documento_ativo
    ultimo_documento_ativo = _criar_documento_zerado_limpo()
    return {
        "status": "sucesso",
        "mensagem": "Varredura concluída: todos os valores de todos os anos e trimestres foram excluídos do banco de dados!",
        "dados_atualizados": ultimo_documento_ativo
    }

@app.post("/api/resetar-dados-padrao")
def resetar_dados_padrao():
    """
    Carrega os dados da planilha modelo de demonstração para fins de teste/homologação.
    """
    global ultimo_documento_ativo
    conteudo_bytes = gerar_modelo_planilha_exemplo()
    ultimo_documento_ativo = processar_demonstracoes_com_jev(conteudo_bytes, "Demonstracoes_Exemplo_Acionistas.xlsx")
    return ultimo_documento_ativo

@app.get("/api/dados-demonstracao-pdf-padrao")
def obter_dados_pdf_padrao():
    """
    Carrega e processa instantaneamente o conjunto padrão a partir do PDF executivo.
    """
    global ultimo_documento_ativo
    conteudo_bytes = gerar_modelo_pdf_exemplo()
    ultimo_documento_ativo = processar_pdf_demonstracoes_com_jev(conteudo_bytes, "Modelo_Balanco_DRE_Acionistas.pdf")
    return ultimo_documento_ativo

class LimparDadosRequest(BaseModel):
    trimestre: str  # "1T", "2T", "3T", "4T" ou "todos"
    ano: Optional[str] = None

@app.post("/api/limpar-dados")
def limpar_dados_demonstracao(req: LimparDadosRequest):
    """
    Zera individualmente um trimestre (1T, 2T, 3T, 4T) ou todos os trimestres/contas na sessão ativa.
    Suporta tanto anos específicos quanto 'todos_anos' (global), recalculando instantaneamente
    a matriz DRE de cada exercício, balanços patrimoniais, indicadores e totais consolidados.
    """
    global ultimo_documento_ativo
    if ultimo_documento_ativo is None:
        ultimo_documento_ativo = _criar_documento_zerado_limpo()

    trim = req.trimestre.upper()
    eh_todos_anos = (not req.ano) or (req.ano == "todos_anos")
    
    # Se limpou TUDO em todos os anos, faz expurgo completo imediato!
    if eh_todos_anos and trim == "TODOS":
        ultimo_documento_ativo = _criar_documento_zerado_limpo()
        return {
            "status": "sucesso",
            "mensagem": "Todos os dados e trimestres de TODOS OS EXERCÍCIOS foram zerados e excluídos com sucesso!",
            "dados_atualizados": ultimo_documento_ativo
        }

    anos_disponiveis = ultimo_documento_ativo.get("anos_disponiveis", ["2026", "2025", "2024", "2023"])
    anos_afetados = list(anos_disponiveis) if eh_todos_anos else [req.ano]
    
    contas = ultimo_documento_ativo.get("contas_detalhadas", []) + ultimo_documento_ativo.get("itens_dre", [])

    if trim == "TODOS":
        for c in contas:
            if "saldos_anuais" in c:
                for ano in anos_afetados:
                    c["saldos_anuais"][ano] = 0.0
            
            if eh_todos_anos or (ultimo_documento_ativo.get("ano_ativo") in anos_afetados):
                if "saldos_trimestrais" in c:
                    c["saldos_trimestrais"]["1T"] = 0.0
                    c["saldos_trimestrais"]["2T"] = 0.0
                    c["saldos_trimestrais"]["3T"] = 0.0
                    c["saldos_trimestrais"]["4T"] = 0.0
                    c["saldos_trimestrais"]["anual"] = 0.0
                c["saldo_atual"] = 0.0
                
            if "saldos_trimestrais_por_ano" in c:
                for ano in anos_afetados:
                    c["saldos_trimestrais_por_ano"][ano] = {"1T": 0.0, "2T": 0.0, "3T": 0.0, "4T": 0.0, "anual": 0.0}

    elif trim in ["1T", "2T", "3T", "4T"]:
        for c in contas:
            if "saldos_trimestrais" in c:
                c["saldos_trimestrais"][trim] = 0.0
                soma_recalc = (
                    c["saldos_trimestrais"].get("1T", 0.0) +
                    c["saldos_trimestrais"].get("2T", 0.0) +
                    c["saldos_trimestrais"].get("3T", 0.0) +
                    c["saldos_trimestrais"].get("4T", 0.0)
                )
                c["saldos_trimestrais"]["anual"] = soma_recalc
                if eh_todos_anos or (ultimo_documento_ativo.get("ano_ativo") in anos_afetados):
                    c["saldo_atual"] = soma_recalc
                
            if "saldos_anuais" in c:
                for ano in anos_afetados:
                    if "saldos_trimestrais_por_ano" in c and ano in c["saldos_trimestrais_por_ano"]:
                        c["saldos_trimestrais_por_ano"][ano][trim] = 0.0
                        c["saldos_anuais"][ano] = sum(c["saldos_trimestrais_por_ano"][ano].get(t, 0.0) for t in ["1T", "2T", "3T", "4T"])
                    elif eh_todos_anos or ano == ultimo_documento_ativo.get("ano_ativo"):
                        c["saldos_anuais"][ano] = c.get("saldos_trimestrais", {}).get("anual", 0.0)

    def _classificar_grupo(c):
        cod = str(c.get("codigo", "")).strip()
        g = c.get("grupo", "").lower()
        desc = c.get("conta", "").lower()
        if cod.startswith(("2.03", "2.3", "2.04", "2.4", "3")): return "patrimonio_liquido"
        if any(w in desc for w in ['patrimônio líquido', 'patrimonio liquido', 'capital social', 'reserva', 'lucro acumulado', 'lucros acumulados']): return "patrimonio_liquido"
        if cod.startswith(("1.01", "1.1")): return "ativo_circulante"
        if cod.startswith(("1.02", "1.2", "1.03", "1.3")): return "ativo_nao_circulante"
        if cod.startswith(("2.01", "2.1")): return "passivo_circulante"
        if cod.startswith(("2.02", "2.2")): return "passivo_nao_circulante"
        if cod.startswith("2"): return "passivo_circulante"
        if "ativo circulante" in g: return "ativo_circulante"
        if "ativo não circulante" in g or "ativo nao circulante" in g: return "ativo_nao_circulante"
        if "passivo circulante" in g: return "passivo_circulante"
        if "passivo não circulante" in g or "passivo nao circulante" in g: return "passivo_nao_circulante"
        if "patrimônio líquido" in g or "patrimonio liquido" in g: return "patrimonio_liquido"
        return "ativo_circulante"

    from app.services.calculos_indices import CalculadoraIndicesFinanceiros

    if "dre_matriz_por_ano" not in ultimo_documento_ativo:
        ultimo_documento_ativo["dre_matriz_por_ano"] = {}
    if "totais_dre_por_ano" not in ultimo_documento_ativo:
        ultimo_documento_ativo["totais_dre_por_ano"] = {}
    if "totais_balanco_por_ano" not in ultimo_documento_ativo:
        ultimo_documento_ativo["totais_balanco_por_ano"] = {}
    if "indicadores_por_ano" not in ultimo_documento_ativo:
        ultimo_documento_ativo["indicadores_por_ano"] = {}

    contas_balanco = ultimo_documento_ativo.get("contas_detalhadas", [])

    for ano_k in anos_afetados:
        contas_ano = []
        for c in contas:
            c_copia = dict(c)
            c_copia["saldo_atual"] = c.get("saldos_anuais", {}).get(ano_k, (c.get("saldo_atual", 0.0) if ano_k == ultimo_documento_ativo.get("ano_ativo") else 0.0))
            if ano_k == ultimo_documento_ativo.get("ano_ativo"):
                c_copia["saldos_trimestrais"] = c.get("saldos_trimestrais", {})
            else:
                c_copia["saldos_trimestrais"] = c.get("saldos_trimestrais_por_ano", {}).get(ano_k, {"1T": 0.0, "2T": 0.0, "3T": 0.0, "4T": 0.0, "anual": c_copia["saldo_atual"]})
            contas_ano.append(c_copia)

        matriz_recalc = conglutinador_jev.conglutinar_dados_na_matriz(contas_ano)
        ultimo_documento_ativo["dre_matriz_por_ano"][ano_k] = matriz_recalc

        rec_bruta = matriz_recalc["resumo_executivo"]["receita_bruta_anual"]
        lucro_liq = matriz_recalc["resumo_executivo"]["lucro_liquido_anual"]
        ultimo_documento_ativo["totais_dre_por_ano"][ano_k] = {
            "receita_bruta": rec_bruta,
            "lucro_liquido": lucro_liq
        }

        ac_k = sum(c.get("saldos_anuais", {}).get(ano_k, 0.0) for c in contas_balanco if _classificar_grupo(c) == "ativo_circulante")
        anc_k = sum(c.get("saldos_anuais", {}).get(ano_k, 0.0) for c in contas_balanco if _classificar_grupo(c) == "ativo_nao_circulante")
        disp_k = sum(c.get("saldos_anuais", {}).get(ano_k, 0.0) for c in contas_balanco if "disponib" in c.get("grupo", "").lower() or any(w in c.get("conta", "").lower() for w in ['caixa', 'banco', 'aplica']))
        est_k = sum(c.get("saldos_anuais", {}).get(ano_k, 0.0) for c in contas_balanco if "estoque" in c.get("grupo", "").lower() or "estoque" in c.get("conta", "").lower())
        pc_k = sum(c.get("saldos_anuais", {}).get(ano_k, 0.0) for c in contas_balanco if _classificar_grupo(c) == "passivo_circulante")
        pnc_k = sum(c.get("saldos_anuais", {}).get(ano_k, 0.0) for c in contas_balanco if _classificar_grupo(c) == "passivo_nao_circulante")
        pl_k = sum(c.get("saldos_anuais", {}).get(ano_k, 0.0) for c in contas_balanco if _classificar_grupo(c) == "patrimonio_liquido")

        totais_b_novo = {
            "ativo_circulante": ac_k,
            "ativo_nao_circulante": anc_k,
            "ativo_total": ac_k + anc_k,
            "passivo_circulante": pc_k,
            "passivo_nao_circulante": pnc_k,
            "patrimonio_liquido": pl_k,
            "passivo_total": pc_k + pnc_k + pl_k if (pc_k + pnc_k + pl_k) > 0 else 0.0,
            "disponibilidades": disp_k
        }
        ultimo_documento_ativo["totais_balanco_por_ano"][ano_k] = totais_b_novo

        indices_novos = CalculadoraIndicesFinanceiros.calcular_todos_indices(
            ativo_circulante=ac_k,
            ativo_nao_circulante=anc_k,
            disponibilidades=disp_k,
            estoques=est_k,
            passivo_circulante=pc_k,
            passivo_nao_circulante=pnc_k,
            patrimonio_liquido=pl_k,
            receita_liquida=rec_bruta * 0.88,
            lucro_bruto=rec_bruta * 0.45,
            ebitda=lucro_liq * 1.45,
            lucro_liquido=lucro_liq
        )
        ultimo_documento_ativo["indicadores_por_ano"][ano_k] = indices_novos

    ano_principal = ultimo_documento_ativo.get("ano_ativo", "2026")
    if ano_principal in ultimo_documento_ativo["dre_matriz_por_ano"]:
        ultimo_documento_ativo["dre_matriz_empresa"] = ultimo_documento_ativo["dre_matriz_por_ano"][ano_principal]
    if ano_principal in ultimo_documento_ativo["totais_dre_por_ano"]:
        ultimo_documento_ativo["totais_dre"] = ultimo_documento_ativo["totais_dre_por_ano"][ano_principal]
    if ano_principal in ultimo_documento_ativo["totais_balanco_por_ano"]:
        ultimo_documento_ativo["totais_balanco"] = ultimo_documento_ativo["totais_balanco_por_ano"][ano_principal]
    if ano_principal in ultimo_documento_ativo["indicadores_por_ano"]:
        ultimo_documento_ativo["indices_financeiros"] = ultimo_documento_ativo["indicadores_por_ano"][ano_principal]

    if eh_todos_anos:
        msg = "Todos os dados e trimestres de TODOS OS EXERCÍCIOS foram zerados com sucesso!" if trim == "TODOS" else f"Os dados do {trim} foram limpos e recalculados em todos os exercícios!"
    else:
        msg = f"Todos os dados do exercício {req.ano} foram zerados com sucesso!" if trim == "TODOS" else f"Os dados do {trim} no exercício {req.ano} foram limpos e recalculados!"
    
    return {
        "status": "sucesso",
        "mensagem": msg,
        "dados_atualizados": ultimo_documento_ativo
    }

@app.post("/api/upload-demonstracao")
async def upload_demonstracao(
    file: UploadFile = File(...),
    ano_destino: Optional[str] = Form(None),
    trimestres_autorizados: Optional[str] = Form(None)
):
    """
    Recebe um arquivo (Excel, CSV ou PDF) enviado pelo usuário,
    valida obrigatoriedade de ano contábil e seleção de trimestres,
    executa a extração estruturada, classificação com JEV, conglutinação na matriz e cálculo dos índices.
    Mescla (Merge) os dados do ano importado com os demais exercícios já existentes na sessão,
    impedindo que outros anos desapareçam ou sejam perdidos!
    """
    global ultimo_documento_ativo
    from fastapi.responses import JSONResponse
    import json

    try:
        # REGRA DE GOVERNANÇA CONTÁBIL: Restringe a importação de movimentação/saldos somente se
        # o Plano de Contas e a estrutura da DRE já estiverem cadastrados no sistema!
        prontidao = empresas_plano_service.verificar_prontidao_importacao()
        if not prontidao.get("liberado", False):
            return JSONResponse(
                status_code=400,
                content={
                    "erro": True,
                    "bloqueado": True,
                    "bloqueio_cadastro": True,
                    "prontidao_importacao": prontidao,
                    "mensagem": prontidao.get(
                        "motivo",
                        "🚫 Importação Bloqueada: Não é permitido importar Balanço ou DRE sem que o Plano de Contas esteja previamente cadastrado! Acesse a aba '📑 Plano de Contas'."
                    ),
                    "detalhe": "Plano de Contas ou DRE não cadastrado"
                }
            )

        ano_limpo = (ano_destino or "").strip()
        if not ano_limpo:
            ano_limpo = "2026"

        trimestres_lista = []
        if trimestres_autorizados:
            try:
                trimestres_lista = json.loads(trimestres_autorizados)
            except Exception:
                trimestres_lista = [t.strip().upper() for t in trimestres_autorizados.split(",") if t.strip()]

        if not trimestres_lista:
            trimestres_lista = ["1T", "2T", "3T", "4T"]

        nome_lower = (file.filename or "").lower()
        extensoes_permitidas = (".xlsx", ".xls", ".csv", ".pdf")
        if not any(nome_lower.endswith(ext) for ext in extensoes_permitidas):
            return JSONResponse(
                status_code=400,
                content={
                    "erro": True,
                    "mensagem": "Formato de arquivo não suportado. Envie arquivos .xlsx, .xls, .csv ou .pdf.",
                    "detalhe": "Formato inválido"
                }
            )

        MAX_FILE_SIZE = 25 * 1024 * 1024
        conteudo = await file.read()
        if len(conteudo) > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "erro": True,
                    "mensagem": "O arquivo enviado excede o limite máximo permitido de 25 MB.",
                    "detalhe": "Payload Too Large"
                }
            )

        # ---------------------------------------------------------------------------------
        # REGRA DE GOVERNANÇA CONTÁBIL ZERO TRUST:
        # É TERMINANTEMENTE PROIBIDO IMPORTAR BALANÇO E DRE SE NÃO EXISTIR UM PLANO DE CONTAS CADASTRADO!
        # ---------------------------------------------------------------------------------
        prontidao = empresas_plano_service.verificar_prontidao_importacao()
        if not prontidao.get("liberado"):
            return JSONResponse(
                status_code=400,
                content={
                    "erro": True,
                    "bloqueado": True,
                    "mensagem": (
                        "🚫 Importação Bloqueada: Não é permitido importar Balanço ou DRE sem que o "
                        "Plano de Contas corporativo esteja previamente cadastrado! "
                        "Acesse a aba '📑 Plano de Contas' para cadastrar ou importar a estrutura de contas primeiro."
                    ),
                    "detalhe": prontidao.get("motivo"),
                    "prontidao_importacao": prontidao
                }
            )

        if ultimo_documento_ativo is None:
            ultimo_documento_ativo = _criar_documento_zerado_limpo()

        if nome_lower.endswith(".pdf") or file.content_type == "application/pdf":
            resultado = processar_pdf_demonstracoes_com_jev(
                conteudo,
                file.filename,
                ano_destino=ano_limpo,
                trimestres_permitidos=trimestres_lista
            )
        else:
            resultado = processar_demonstracoes_com_jev(
                conteudo,
                file.filename,
                ano_destino=ano_limpo,
                trimestres_permitidos=trimestres_lista
            )

        # FUSÃO MULTI-EXERCÍCIO E MULTI-DEMONSTRAÇÃO (Preserva 2026, 2025, 2024, 2023 sem jamais apagar outros anos!)
        anos_unificados = set(ultimo_documento_ativo.get("anos_disponiveis", []))
        anos_unificados.update(resultado.get("anos_disponiveis", []))
        anos_unificados.update(["2026", "2025", "2024", "2023", ano_limpo])
        resultado["anos_disponiveis"] = sorted(
            [a for a in anos_unificados if str(a).isdigit() and 2020 <= int(a) <= 2035],
            reverse=True
        )
        resultado["ano_ativo"] = ano_limpo

        eh_somente_dre = bool(resultado.get("somente_dre")) or (len(resultado.get("itens_dre", [])) > 0 and len(resultado.get("contas_detalhadas", [])) == 0)
        eh_somente_balanco = len(resultado.get("contas_detalhadas", [])) > 0 and len(resultado.get("itens_dre", [])) == 0

        # 1. Preserva os dicionários por ano dos outros exercícios (e preserva Balanço se subiu só DRE, ou DRE se subiu só Balanço)
        for dict_key in ["dre_matriz_por_ano", "totais_balanco_por_ano", "totais_dre_por_ano", "indicadores_por_ano"]:
            antigo_map = ultimo_documento_ativo.get(dict_key, {})
            novo_map = resultado.get(dict_key, {})
            for ano_ant, val_ant in antigo_map.items():
                if ano_ant != ano_limpo:
                    novo_map[ano_ant] = val_ant
                else:
                    # Mesmo ano: se subiu somente DRE, preserva o Balanço que já estava carregado para este ano
                    if eh_somente_dre and dict_key == "totais_balanco_por_ano" and val_ant.get("ativo_total", 0) > 0:
                        novo_map[ano_ant] = val_ant
                    # Mesmo ano: se subiu somente Balanço, preserva a DRE que já estava carregada para este ano
                    elif eh_somente_balanco and dict_key in ("dre_matriz_por_ano", "totais_dre_por_ano"):
                        novo_map[ano_ant] = val_ant
            resultado[dict_key] = novo_map

        # 2. Mescla saldos_anuais em itens_dre e contas_detalhadas para que todas as abas mantenham 2023, 2024, 2025 e 2026
        if eh_somente_dre and not resultado.get("contas_detalhadas") and ultimo_documento_ativo.get("contas_detalhadas"):
            resultado["contas_detalhadas"] = ultimo_documento_ativo["contas_detalhadas"]
            resultado["totais_balanco"] = ultimo_documento_ativo.get("totais_balanco", resultado.get("totais_balanco"))
        elif eh_somente_balanco and not resultado.get("itens_dre") and ultimo_documento_ativo.get("itens_dre"):
            resultado["itens_dre"] = ultimo_documento_ativo["itens_dre"]
            resultado["totais_dre"] = ultimo_documento_ativo.get("totais_dre", resultado.get("totais_dre"))
            resultado["dre_matriz_empresa"] = ultimo_documento_ativo.get("dre_matriz_empresa", resultado.get("dre_matriz_empresa"))

        # Preserva saldos_anuais de outros anos dentro de itens_dre
        antigos_dre_map = {
            f"{it.get('codigo', '')}_{it.get('conta', '')}": it
            for it in ultimo_documento_ativo.get("itens_dre", [])
        }
        for it_novo in resultado.get("itens_dre", []):
            chave_it = f"{it_novo.get('codigo', '')}_{it_novo.get('conta', '')}"
            saldos_anuais_it = it_novo.setdefault("saldos_anuais", {})
            for a_fixo in resultado["anos_disponiveis"]:
                saldos_anuais_it.setdefault(a_fixo, 0.0)
            if chave_it in antigos_dre_map:
                ant_saldos = antigos_dre_map[chave_it].get("saldos_anuais", {})
                for a_ant, v_ant in ant_saldos.items():
                    if a_ant != ano_limpo and v_ant != 0:
                        saldos_anuais_it[a_ant] = v_ant

        ultimo_documento_ativo = resultado
        return resultado
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "erro": True,
                "mensagem": f"Erro ao processar '{file.filename}': {str(e)}",
                "detalhe": str(e)
            }
        )

# --------------------------------------------------------------------------------------
# ROTAS DE CADASTRO DE EMPRESAS (MATRIZ & FILIAIS) E PLANO DE CONTAS MULTI-EMPRESAS
# --------------------------------------------------------------------------------------
class EmpresaCreateRequest(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = ""
    cnpj: Optional[str] = ""
    tipo: Optional[str] = "MATRIZ"
    tipo_unidade: Optional[str] = "MATRIZ"  # "MATRIZ" ou "FILIAL"
    matriz_id: Optional[str] = None
    codigo_empresa: Optional[str] = ""
    cidade: Optional[str] = ""
    uf: Optional[str] = "SP"
    cidade_uf: Optional[str] = ""
    regime_tributario: Optional[str] = "Lucro Real"

class ContaPlanoCreateRequest(BaseModel):
    codigo_contabil: str
    nome_conta: str
    codigo_reduzido: Optional[str] = ""
    ref: Optional[str] = ""
    demonstracao: Optional[str] = "DRE"
    tipo_demonstracao: Optional[str] = "DRE"  # "DRE" ou "BALANCO"
    natureza: Optional[str] = "CREDORA"
    tipo_conta: Optional[str] = "ANALITICA"
    grupo_contabil: Optional[str] = "RECEITA"
    conta_destino_matriz_id: str = "vendas_mercadorias"
    conta_destino_matriz_nome: Optional[str] = ""
    escopo: Optional[str] = "MATRIZ"
    empresa_id: Optional[str] = "MATRIZ_GLOBAL"
    propagar_filiais: bool = True

class MascaraPlanoRequest(BaseModel):
    mascara: str

@app.get("/api/empresas-plano")
def listar_empresas_e_plano_contas(empresa_id: Optional[str] = None):
    """
    Retorna todas as empresas cadastradas (Matriz e Filiais), o Plano de Contas unificado,
    a máscara de classificação contábil e o status de prontidão para importação.
    """
    contas_efetivas = empresas_plano_service.obter_plano_contas_efetivo_empresa(empresa_id)
    return {
        "empresas": empresas_plano_service.listar_empresas(),
        "plano_contas": contas_efetivas,
        "mascara_plano": empresas_plano_service.obter_mascara(),
        "prontidao_importacao": empresas_plano_service.verificar_prontidao_importacao(),
        "plano_efetivo_empresa": {
            "empresa_id": empresa_id or "CONSOLIDADO",
            "contas_efetivas": contas_efetivas
        }
    }

@app.post("/api/plano-contas/mascara")
def atualizar_mascara_plano_endpoint(req: MascaraPlanoRequest):
    """
    Atualiza a máscara de classificação do Plano de Contas (ex: #.#.#.##.###).
    """
    mascara = empresas_plano_service.atualizar_mascara(req.mascara)
    return {
        "status": "sucesso",
        "mensagem": f"Máscara do Plano de Contas atualizada para '{mascara}'!",
        "mascara_plano": mascara,
        "mascara_ativa": mascara
    }

@app.get("/api/consultar-cnpj/{cnpj}")
def consultar_cnpj_endpoint(cnpj: str):
    """
    Recupera os dados cadastrais da empresa diretamente da Receita Federal
    a partir do CNPJ informado (Razão Social, Nome Fantasia, Cidade, UF, Matriz/Filial).
    """
    resultado = consultar_dados_cnpj(cnpj)
    if not resultado.get("sucesso"):
        return JSONResponse(status_code=400, content=resultado)
    return resultado

@app.post("/api/empresas")
def cadastrar_empresa_endpoint(req: EmpresaCreateRequest):
    """
    Cadastra uma nova Empresa (Matriz ou Filial).
    Se for Filial, herda imediatamente todas as contas do Plano de Contas da Matriz!
    """
    tipo_escolhido = req.tipo if req.tipo and req.tipo != "MATRIZ" else (req.tipo_unidade or "MATRIZ")
    emp = empresas_plano_service.cadastrar_empresa(
        razao_social=req.razao_social,
        nome_fantasia=req.nome_fantasia or req.razao_social,
        cnpj=req.cnpj or "",
        tipo_unidade=tipo_escolhido,
        matriz_id=req.matriz_id,
        codigo_empresa=req.codigo_empresa or "",
        cidade_uf=req.cidade_uf or "",
        regime_tributario=req.regime_tributario or "Lucro Real",
        cidade=req.cidade or "",
        uf=req.uf or "SP"
    )
    return {
        "status": "sucesso",
        "mensagem": f"{emp['tipo_unidade']} '{emp['nome_fantasia']}' cadastrada com sucesso! ({emp['total_contas_ativas']} contas vinculadas)",
        "empresa": emp,
        "empresas": empresas_plano_service.listar_empresas()
    }

@app.delete("/api/empresas/{empresa_id}")
def excluir_empresa_endpoint(empresa_id: str):
    removido = empresas_plano_service.remover_empresa(empresa_id)
    return {
        "status": "sucesso" if removido else "erro",
        "removido": removido,
        "empresas": empresas_plano_service.listar_empresas()
    }

@app.post("/api/plano-contas")
def cadastrar_conta_plano_endpoint(req: ContaPlanoCreateRequest):
    """
    Cadastra uma conta no Plano de Contas Corporativo.
    Quando cadastrada na Matriz (ou Global), surte efeito imediato em todas as Filiais
    e recalcula automaticamente a Matriz DRE da sessão ativa!
    """
    global ultimo_documento_ativo
    dem_escolhida = req.demonstracao or req.tipo_demonstracao or "DRE"
    escopo_escolhido = req.escopo or req.empresa_id or "MATRIZ"
    nova_conta = empresas_plano_service.cadastrar_conta_plano(
        codigo_contabil=req.codigo_contabil,
        nome_conta=req.nome_conta,
        tipo_demonstracao=dem_escolhida,
        grupo_contabil=req.grupo_contabil or "RECEITA",
        conta_destino_matriz_id=req.conta_destino_matriz_id,
        conta_destino_matriz_nome=req.conta_destino_matriz_nome or req.conta_destino_matriz_id,
        empresa_id=req.empresa_id or "MATRIZ_GLOBAL",
        propagar_filiais=req.propagar_filiais,
        escopo=escopo_escolhido,
        demonstracao=dem_escolhida,
        codigo_reduzido=req.codigo_reduzido or "",
        ref=req.ref or ""
    )

    # Se houver documento ativo carregado, re-conglutina imediatamente para surtir efeito na hora!
    if ultimo_documento_ativo is not None:
        contas_todas = ultimo_documento_ativo.get("itens_dre", []) + ultimo_documento_ativo.get("contas_detalhadas", [])
        if contas_todas:
            ano_at = ultimo_documento_ativo.get("ano_ativo", "2026")
            matriz_nova = conglutinador_jev.conglutinar_dados_na_matriz(contas_todas)
            ultimo_documento_ativo["dre_matriz_empresa"] = matriz_nova
            if "dre_matriz_por_ano" in ultimo_documento_ativo:
                ultimo_documento_ativo["dre_matriz_por_ano"][ano_at] = matriz_nova

    return {
        "status": "sucesso",
        "mensagem": f"Conta '{nova_conta['codigo_contabil']} - {nova_conta['nome_conta']}' cadastrada na Matriz e propagada automaticamente para todas as Filiais!",
        "conta": nova_conta,
        "plano_contas": empresas_plano_service.obter_plano_contas_efetivo_empresa(),
        "prontidao_importacao": empresas_plano_service.verificar_prontidao_importacao()
    }

@app.delete("/api/plano-contas/{conta_id}")
def excluir_conta_plano_endpoint(conta_id: str):
    removido = empresas_plano_service.remover_conta_plano(conta_id)
    return {
        "status": "sucesso" if removido else "erro",
        "removido": removido,
        "plano_contas": empresas_plano_service.obter_plano_contas_efetivo_empresa(),
        "prontidao_importacao": empresas_plano_service.verificar_prontidao_importacao()
    }

@app.post("/api/plano-contas/limpar-tudo")
def limpar_plano_contas_endpoint():
    """
    Remove todas as contas cadastradas do Plano de Contas / DRE para permitir um novo cadastro limpo do zero.
    """
    res = empresas_plano_service.limpar_plano_contas_completo()
    return {
        **res,
        "empresas": empresas_plano_service.listar_empresas()
    }

@app.post("/api/plano-contas/importar-estrutura")
async def importar_estrutura_plano_contas_endpoint(
    file: UploadFile = File(...),
    escopo: Optional[str] = Form("MATRIZ"),
    tipo_forcar: Optional[str] = Form("AUTO"),
    limpar_anterior: Optional[str] = Form("false")
):
    """
    Importa e cadastra automaticamente as contas a partir de uma planilha (.xlsx, .xls, .csv) ou PDF:
    1. Identifica automaticamente a peça contábil ('PLANO_DE_CONTAS', 'DRE' ou 'BALANCO_PATRIMONIAL');
    2. Higieniza (limpa) todos os saldos numéricos, datas, percentuais e cabeçalhos para deixar a estrutura 100% enxuta;
    3. Cadastra na Matriz e propaga automaticamente para todas as Filiais e motor JEV.
    """
    global ultimo_documento_ativo
    from fastapi.responses import JSONResponse

    nome_lower = (file.filename or "").lower()
    if not any(nome_lower.endswith(ext) for ext in (".xlsx", ".xls", ".csv", ".pdf")):
        return JSONResponse(
            status_code=400,
            content={
                "erro": True,
                "mensagem": "Formato inválido. Envie uma planilha (.xlsx, .xls, .csv) ou arquivo .pdf para importar a estrutura de contas."
            }
        )

    conteudo = await file.read()
    flag_limpar = str(limpar_anterior or "false").strip().lower() in ("true", "1", "sim", "yes")
    res = empresas_plano_service.importar_estrutura_contas_enxuta(
        conteudo_arquivo=conteudo,
        nome_arquivo=file.filename or "estrutura.xlsx",
        escopo=(escopo or "MATRIZ").strip().upper(),
        tipo_forcar=(tipo_forcar or "AUTO").strip().upper(),
        limpar_anterior=flag_limpar
    )
    if res.get("erro"):
        return JSONResponse(status_code=400, content=res)

    # Se houver documento ativo carregado, re-conglutina imediatamente com o novo Plano de Contas!
    if ultimo_documento_ativo is not None:
        contas_todas = ultimo_documento_ativo.get("itens_dre", []) + ultimo_documento_ativo.get("contas_detalhadas", [])
        if contas_todas:
            ano_at = ultimo_documento_ativo.get("ano_ativo", "2026")
            matriz_nova = conglutinador_jev.conglutinar_dados_na_matriz(contas_todas)
            ultimo_documento_ativo["dre_matriz_empresa"] = matriz_nova
            if "dre_matriz_por_ano" in ultimo_documento_ativo:
                ultimo_documento_ativo["dre_matriz_por_ano"][ano_at] = matriz_nova

    return res

@app.post("/api/classificar-conta")
def classificar_conta(conta: str, descricao: str, saldo: float = None):
    """
    Endpoint de classificação individual de conta com JEV.
    """
    return jev_service.classificar_conta_contabil(conta=conta, descricao=descricao, saldo=saldo)

class ChatAgenteRequest(BaseModel):
    mensagem: str
    thread_id: Optional[str] = "sessao_acionista_padrao"
    ano: Optional[str] = "2026"
    trimestre: Optional[str] = "1T"
    contexto_financeiro: Optional[dict] = None

@app.post("/api/chat/agente-financeiro")
def chat_agente_financeiro(req: ChatAgenteRequest, _auth: bool = Depends(verificar_token_acesso)):

    """
    Endpoint de Conversação com o Agente Cognitivo LangGraph:
    Mantém memória de curto prazo (buffer), sumarização progressiva ativa (Context Engineering)
    e persistência de longo prazo (Raw State / Checkpointer).
    Alimenta o agente com os dados contábeis reais da sessão ativa.
    """
    global ultimo_documento_ativo
    dados_reais = req.contexto_financeiro or ultimo_documento_ativo
    if not dados_reais:
        dados_reais = obter_dados_padrao()

    return agente_langgraph.conversar(
        mensagem_usuario=req.mensagem,
        thread_id=req.thread_id or "sessao_acionista_padrao",
        ano=req.ano or dados_reais.get("ano_ativo", "2026"),
        trimestre=req.trimestre or "1T",
        dados_contabeis=dados_reais
    )

@app.delete("/api/chat/sessao/{thread_id}")
def limpar_sessao_chat(thread_id: str):
    """
    Reseta a sessão do acionista no LangGraph Checkpointer (Nova Conversa).
    """
    sucesso = agente_langgraph.limpar_sessao(thread_id)
    return {"status": "sucesso" if sucesso else "erro", "thread_id": thread_id, "limpo": sucesso}

# --------------------------------------------------------------------------------------
# ROTAS DE AUTENTICAÇÃO E CONTROLE DE ACESSO (ZERO TRUST)
# --------------------------------------------------------------------------------------
class LoginAcessoRequest(BaseModel):
    token: str

@app.get("/api/auth/status-protecao")
def status_protecao_autenticacao():
    """
    Informa ao frontend se a aplicação requer PIN/Chave de Acesso para visualização.
    """
    token_configurado = os.getenv("PAINEL_ACCESS_TOKEN", "").strip()
    return {
        "autenticacao_ativa": bool(token_configurado),
        "mensagem": "Autenticação requerida por PIN/Chave de Acesso" if token_configurado else "Modo aberto local"
    }

@app.post("/api/auth/verificar-acesso")
def verificar_acesso_acionista(req: LoginAcessoRequest):
    """
    Valida a chave de acesso do acionista contra a variável de ambiente segura.
    """
    token_esperado = os.getenv("PAINEL_ACCESS_TOKEN", "").strip()
    if not token_esperado:
        return {"valido": True, "mensagem": "Autenticação desativada no servidor."}

    if req.token.strip() == token_esperado:
        return {"valido": True, "mensagem": "Acesso concedido com sucesso ao Painel!"}
    
    return JSONResponse(
        status_code=401,
        content={"valido": False, "mensagem": "Chave de Acesso incorreta. Verifique o PIN cadastrado."}
    )





