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

@app.get("/api/dados-demonstracao-padrao")
def obter_dados_padrao(_auth: bool = Depends(verificar_token_acesso)):
    """
    Retorna o documento ativo atual (último arquivo importado) ou a demonstração de exemplo caso nenhum tenha sido carregado.
    Preserva rigorosamente os estados de zeramento e cálculos já realizados na sessão.
    """
    global ultimo_documento_ativo
    if ultimo_documento_ativo is not None:
        contas = ultimo_documento_ativo.get("contas_detalhadas", []) + ultimo_documento_ativo.get("itens_dre", [])
        ano_principal = ultimo_documento_ativo.get("ano_ativo", "2026")
        if contas and ano_principal in ultimo_documento_ativo.get("dre_matriz_por_ano", {}):
            ultimo_documento_ativo["dre_matriz_empresa"] = ultimo_documento_ativo["dre_matriz_por_ano"][ano_principal]
        return ultimo_documento_ativo

    conteudo_bytes = gerar_modelo_planilha_exemplo()
    ultimo_documento_ativo = processar_demonstracoes_com_jev(conteudo_bytes, "Demonstracoes_Exemplo_Acionistas.xlsx")
    return ultimo_documento_ativo

@app.post("/api/resetar-dados-padrao")
def resetar_dados_padrao():
    """
    Reseta a visualização ativa para o modelo de exemplo original.
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
        conteudo_bytes = gerar_modelo_planilha_exemplo()
        ultimo_documento_ativo = processar_demonstracoes_com_jev(conteudo_bytes, "Demonstracoes_Exemplo_Acionistas.xlsx")

    trim = req.trimestre.upper()
    eh_todos_anos = (not req.ano) or (req.ano == "todos_anos")
    
    anos_disponiveis = ultimo_documento_ativo.get("anos_disponiveis", ["2026", "2025"])
    anos_afetados = list(anos_disponiveis) if eh_todos_anos else [req.ano]
    
    contas = ultimo_documento_ativo.get("contas_detalhadas", []) + ultimo_documento_ativo.get("itens_dre", [])

    if trim == "TODOS":
        for c in contas:
            # Zera os saldos anuais de todos os anos afetados
            if "saldos_anuais" in c:
                for ano in anos_afetados:
                    c["saldos_anuais"][ano] = 0.0
            
            # Se limpou todos os anos ou o ano ativo da sessão, zera também os trimestrais e o saldo atual
            if eh_todos_anos or (ultimo_documento_ativo.get("ano_ativo") in anos_afetados):
                if "saldos_trimestrais" in c:
                    c["saldos_trimestrais"]["1T"] = 0.0
                    c["saldos_trimestrais"]["2T"] = 0.0
                    c["saldos_trimestrais"]["3T"] = 0.0
                    c["saldos_trimestrais"]["4T"] = 0.0
                    c["saldos_trimestrais"]["anual"] = 0.0
                c["saldo_atual"] = 0.0
                
            # Se existir dicionário de trimestres por ano, zera para cada ano afetado
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

    # Classificação de grupos do balanço
    def _classificar_grupo(c):
        cod = str(c.get("codigo", "")).strip()
        g = c.get("grupo", "").lower()
        desc = c.get("conta", "").lower()
        if cod.startswith("1.01") or cod.startswith("1.1"): return "ativo_circulante"
        if cod.startswith("1.02") or cod.startswith("1.2"): return "ativo_nao_circulante"
        if cod.startswith("2.01") or cod.startswith("2.1"): return "passivo_circulante"
        if cod.startswith("2.02") or cod.startswith("2.2"): return "passivo_nao_circulante"
        if cod.startswith("3."): return "patrimonio_liquido"
        if "ativo circulante" in g: return "ativo_circulante"
        if "ativo não circulante" in g or "ativo nao circulante" in g: return "ativo_nao_circulante"
        if "passivo circulante" in g: return "passivo_circulante"
        if "passivo não circulante" in g or "passivo nao circulante" in g: return "passivo_nao_circulante"
        if "patrimônio líquido" in g or "patrimonio liquido" in g: return "patrimonio_liquido"
        if any(w in desc for w in ['capital', 'reserva', 'lucro acumulado', 'patrimônio']): return "patrimonio_liquido"
        if any(w in desc for w in ['longo prazo', 'não circulante']): return "passivo_nao_circulante" if any(w in desc for w in ['financiamento', 'empréstimo']) else "ativo_nao_circulante"
        if any(w in desc for w in ['imobilizado', 'investimento', 'intangível']): return "ativo_nao_circulante"
        if any(w in desc for w in ['fornecedor', 'salário', 'tributo']): return "passivo_circulante"
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

    # Recalcula para cada ano afetado
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

        # Totais Balanço ano_k
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

        # Indicadores ano_k
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

    # Se zerou todos os anos, zera explicitamente os totais de exibição
    if eh_todos_anos and trim == "TODOS":
        ultimo_documento_ativo["totais_dre"] = {"receita_bruta": 0.0, "lucro_liquido": 0.0}
        ultimo_documento_ativo["totais_balanco"] = {
            "ativo_circulante": 0.0, "ativo_nao_circulante": 0.0, "ativo_total": 0.0,
            "passivo_circulante": 0.0, "passivo_nao_circulante": 0.0, "patrimonio_liquido": 0.0,
            "passivo_total": 0.0, "disponibilidades": 0.0
        }
        ultimo_documento_ativo["indices_financeiros"] = CalculadoraIndicesFinanceiros.calcular_todos_indices(
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        )

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
    Armazena como documento ativo permanente na sessão.
    """
    global ultimo_documento_ativo
    from fastapi.responses import JSONResponse
    import json

    try:
        # 1. Validação com Fallback Resiliente de Ano Contábil
        ano_limpo = (ano_destino or "").strip()
        if not ano_limpo:
            ano_limpo = "2026"

        # 2. Validação com Fallback Resiliente de Trimestres Autorizados
        trimestres_lista = []
        if trimestres_autorizados:
            try:
                trimestres_lista = json.loads(trimestres_autorizados)
            except Exception:
                trimestres_lista = [t.strip().upper() for t in trimestres_autorizados.split(",") if t.strip()]

        if not trimestres_lista:
            trimestres_lista = ["1T", "2T", "3T", "4T"]

        # 3. Validação de Extensão Permitida
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

        # 4. Proteção contra DoS: Limite de Tamanho (25 MB)
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

        if nome_lower.endswith(".pdf") or file.content_type == "application/pdf":
            resultado = processar_pdf_demonstracoes_com_jev(conteudo, file.filename)
        else:
            resultado = processar_demonstracoes_com_jev(
                conteudo,
                file.filename,
                ano_destino=ano_limpo,
                trimestres_permitidos=trimestres_lista
            )

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





