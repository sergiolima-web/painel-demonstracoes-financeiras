import io
import re
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from app.services.jev_service import jev_service
from app.services.calculos_indices import CalculadoraIndicesFinanceiros
from app.services.matriz_empresa_service import conglutinador_jev

def _limpar_valor_numerico_universal(texto: Any) -> float:
    """
    Converte valores contábeis brasileiros e internacionais para float de forma universal.
    Exemplos: '4.800.000,00' -> 4800000.0, '(580.000,00)' -> -580000.0, '-240.000,00' -> -240000.0, '-' -> 0.0
    """
    if isinstance(texto, pd.Series):
        if texto.empty:
            return 0.0
        texto = texto.iloc[0]
    elif isinstance(texto, (list, tuple)):
        if not texto:
            return 0.0
        texto = texto[0]

    if texto is None or (isinstance(texto, float) and pd.isna(texto)):
        return 0.0
    if isinstance(texto, (int, float)):
        return float(texto)
    
    s = str(texto).strip()
    if not s or s in ['-', '—', '–', 'N/A', 'n/a', '.', 'None', 'null', 'R$', 'R$ -']:
        return 0.0

    negativo = False
    if s.startswith('(') and s.endswith(')'):
        negativo = True
        s = s[1:-1].strip()
    elif s.startswith('-'):
        negativo = True
        s = s[1:].strip()
    elif s.endswith('-'):
        negativo = True
        s = s[:-1].strip()

    # Remove símbolos de moeda e espaços
    s = re.sub(r'[R$\s]', '', s)

    # Identificar formato brasileiro (pontos nos milhares e vírgula no decimal)
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            # 1.234.567,89
            s = s.replace('.', '').replace(',', '.')
        else:
            # 1,234,567.89
            s = s.replace(',', '')
    elif ',' in s:
        partes = s.split(',')
        if len(partes) == 2 and len(partes[1]) in [1, 2]:
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')

    try:
        val = float(s)
        return -val if negativo else val
    except ValueError:
        return 0.0

def _normalizar_texto(texto: str) -> str:
    """Normaliza strings removendo acentos e convertendo para minúsculas para comparações resilientes."""
    s = str(texto or '').lower().strip()
    s = s.replace('ç', 'c').replace('ã', 'a').replace('á', 'a').replace('à', 'a').replace('é', 'e').replace('ê', 'e')
    s = s.replace('í', 'i').replace('ó', 'o').replace('ô', 'o').replace('õ', 'o').replace('ú', 'u')
    return s

def _detectar_anos_relatorio(dfs_por_aba: Dict[str, pd.DataFrame], nome_arquivo: str) -> List[str]:
    """
    Varre dinamicamente cabeçalhos, títulos de relatórios, colunas e nomes de abas
    para identificar todos os exercícios (anos contábeis) presentes no documento (ex.: 2026, 2025, 2024).
    """
    anos_encontrados = set()
    for sheet_name, df_raw in dfs_por_aba.items():
        for m in re.findall(r'\b(19\d\d|20\d\d)\b', sheet_name):
            if 1990 <= int(m) <= 2040:
                anos_encontrados.add(m)
        for r in range(min(15, len(df_raw))):
            for val in df_raw.iloc[r].values:
                if pd.notna(val):
                    for m in re.findall(r'\b(19\d\d|20\d\d)\b', str(val)):
                        if 1990 <= int(m) <= 2040:
                            anos_encontrados.add(m)
    for m in re.findall(r'\b(19\d\d|20\d\d)\b', nome_arquivo):
        if 1990 <= int(m) <= 2040:
            anos_encontrados.add(m)

    if anos_encontrados:
        return sorted(list(anos_encontrados), reverse=True)
    return ["2026", "2025"]

def _detectar_e_dividir_blocos_horizontais(df_raw: pd.DataFrame) -> List[Tuple[str, pd.DataFrame]]:
    """
    Scanner Multibloco JEV:
    Detecta quando uma mesma aba do Excel possui 2 ou mais Demonstrações Financeiras / DREs
    posicionadas lado a lado em colunas diferentes (ex.: Bloco 1 = 1º Trimestre, Bloco 2 = 2º Trimestre).
    Identifica com precisão as colunas onde recomeçam cabeçalhos contábeis (Conta, Código, Empresa, etc.).
    """
    num_cols = df_raw.shape[1]
    if num_cols < 4:
        return [("auto", df_raw)]

    # Procura colunas onde recomeçam cabeçalhos contábeis de blocos independentes
    pontos_inicio = []
    for c in range(num_cols):
        col_vals = [_normalizar_texto(v) for v in df_raw.iloc[:12, c].values if pd.notna(v)]
        texto_col = " ".join(col_vals)
        if any(w in texto_col for w in ["conta", "codigo", "cod.", "empresa:", "demonstracao de resultado", "demonstracao do resultado", "balanco patrimonial"]):
            if not pontos_inicio or (c - pontos_inicio[-1]) >= 2:
                pontos_inicio.append(c)

    if len(pontos_inicio) < 2:
        return [("auto", df_raw)]

    blocos: List[Tuple[str, pd.DataFrame]] = []
    for i, start_col in enumerate(pontos_inicio):
        end_col = pontos_inicio[i + 1] if i + 1 < len(pontos_inicio) else num_cols
        sub = df_raw.iloc[:, start_col:end_col].dropna(how="all", axis=1)

        # Identificar o trimestre nas primeiras 12 linhas do bloco
        cabecalho_bloco = " ".join([_normalizar_texto(v) for v in df_raw.iloc[:12, start_col:end_col].values.flatten() if pd.notna(v)])
        tag = None
        if re.search(r'1[ºo]?\s*trim(?:estre)?|1t\b|primeiro\s*trim', cabecalho_bloco):
            tag = "1T"
        elif re.search(r'2[ºo]?\s*trim(?:estre)?|2t\b|segundo\s*trim', cabecalho_bloco):
            tag = "2T"
        elif re.search(r'3[ºo]?\s*trim(?:estre)?|3t\b|terceiro\s*trim', cabecalho_bloco):
            tag = "3T"
        elif re.search(r'4[ºo]?\s*trim(?:estre)?|4t\b|quarto\s*trim', cabecalho_bloco):
            tag = "4T"
        else:
            tag = f"{i + 1}T"

        blocos.append((tag, sub))

    return blocos if len(blocos) >= 2 else [("auto", df_raw)]

def _encontrar_cabecalho_e_colunas(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, str, str, str, Optional[str], Dict[str, str], Dict[str, str]]:
    """
    Localiza dinamicamente a linha real de cabeçalho contábil da planilha e mapeia
    as colunas de Código, Descrição da Conta, Saldo Atual, Saldo Anterior e Trimestres (1T, 2T, 3T, 4T).
    Garante que 'Conta' e 'Descrição' não sejam trocadas com colunas de valor e que colunas de '%' sejam ignoradas como valor.
    """
    colunas_raw = [str(c) for c in df_raw.columns]
    colunas_raw_norm = [_normalizar_texto(c) for c in colunas_raw]
    ja_tem_cabecalho = (
        any(any(k in cn for k in ['conta', 'descri', 'denomin', 'rubrica', 'especifica']) for cn in colunas_raw_norm)
        and not any(c.startswith('Unnamed: 0') or c.startswith('Col_0') for c in colunas_raw[:1])
    )

    if ja_tem_cabecalho:
        df = df_raw.copy()
    else:
        header_idx = -1
        palavras_cabecalho = [
            'conta', 'descri', 'denomin', 'rubrica', 'especifica', 'historico', 
            'codigo', 'cod', 'saldo', 'valor', '202', '201', 'atual', 'anterior',
            'exercicio', 'debito', 'credito', 'movimento'
        ]

        for idx in range(min(15, len(df_raw))):
            linha_valores = [_normalizar_texto(c) for c in df_raw.iloc[idx].values if pd.notna(c) and str(c).strip()]
            linha_texto = " ".join(linha_valores)

            # Ignora linhas que são apenas títulos institucionais
            if any(m in linha_texto for m in ['tipo de saldo', 'demonstracao de resultado', 'demonstracao do resultado', 'balanco patrimonial', 'empresa:']):
                continue

            acertos = sum(1 for p in palavras_cabecalho if p in linha_texto)
            tem_conta_ou_desc = any(p in linha_texto for p in ['conta', 'descri', 'denomin', 'rubrica', 'especifica', 'historico', 'item', 'titulo'])
            tem_valor_ou_cod = any(p in linha_texto for p in ['cod', 'classif', 'saldo', 'valor', 'atual', 'anterior', 'movimento', 'r$'])

            if (tem_conta_ou_desc and tem_valor_ou_cod) or acertos >= 2:
                header_idx = idx
                break

        if header_idx >= 0:
            novas_colunas = [str(c).strip() if pd.notna(c) else f"Col_{i}" for i, c in enumerate(df_raw.iloc[header_idx].values)]
            df = df_raw.iloc[header_idx + 1:].copy()
            df.columns = novas_colunas
        else:
            df = df_raw.copy()

    col_codigo = ""
    col_desc = ""
    col_atual = ""
    col_anterior = ""
    cols_trimestrais = {}
    cols_anos = {}

    colunas = list(df.columns)
    colunas_norm = [_normalizar_texto(c) for c in colunas]

    # Verifica se há par 'Conta' e 'Descrição' lado a lado
    tem_conta = any("conta" in cn for cn in colunas_norm)
    tem_desc = any(any(k in cn for k in ["descri", "denomin", "historico", "nome da conta", "especifica"]) for cn in colunas_norm)

    if tem_conta and tem_desc:
        for orig, norm in zip(colunas, colunas_norm):
            if "conta" in norm and not col_codigo:
                col_codigo = orig
            elif any(k in norm for k in ["descri", "denomin", "historico", "nome", "especifica"]) and not col_desc:
                col_desc = orig
    else:
        for orig, norm in zip(colunas, colunas_norm):
            if any(k in norm for k in ['cod', 'classif', 'estrut', 'rubrica contabil']) and not col_codigo:
                col_codigo = orig
            elif any(k in norm for k in ['conta', 'descri', 'denomin', 'rubrica', 'especifica', 'historico']) and not col_desc:
                col_desc = orig

    if not col_desc:
        for c in colunas:
            if c != col_codigo:
                valores_texto = df[c].dropna().astype(str)
                if any(len(v) > 3 and not re.match(r'^[\d\.,\(\)\s-]+$', v) for v in valores_texto.head(10)):
                    col_desc = c
                    break
        if not col_desc and colunas:
            col_desc = colunas[0] if len(colunas) == 1 else colunas[1]

    # Identifica colunas de trimestres explícitos
    for orig, norm in zip(colunas, colunas_norm):
        if orig in [col_codigo, col_desc]:
            continue
        if re.search(r'(?:^|[\s_])(1t|1q|trimestre\s*1|1o\s*trimestre|1º\s*trimestre)(?:$|[\s_])', norm):
            cols_trimestrais['1T'] = orig
        elif re.search(r'(?:^|[\s_])(2t|2q|trimestre\s*2|2o\s*trimestre|2º\s*trimestre)(?:$|[\s_])', norm):
            cols_trimestrais['2T'] = orig
        elif re.search(r'(?:^|[\s_])(3t|3q|trimestre\s*3|3o\s*trimestre|3º\s*trimestre)(?:$|[\s_])', norm):
            cols_trimestrais['3T'] = orig
        elif re.search(r'(?:^|[\s_])(4t|4q|trimestre\s*4|4o\s*trimestre|4º\s*trimestre)(?:$|[\s_])', norm):
            cols_trimestrais['4T'] = orig

    # Identifica coluna de valor principal, anterior e anos específicos (excluindo qualquer coluna de percentual %)
    for orig, norm in zip(colunas, colunas_norm):
        if orig in [col_codigo, col_desc] or orig in cols_trimestrais.values():
            continue
        if any(p in norm for p in ['%', 'av', 'ah', 'part.', 'part ']):
            continue

        # Mapeia colunas com anos explícitos (ex: 2026, 2025, 2024, 2023)
        m_ano = re.search(r'\b(19\d\d|20\d\d)\b', norm)
        if m_ano:
            cols_anos[m_ano.group(1)] = orig

        if any(v in norm for v in ['anterior', 'ano anterior', 'exercicio anterior', 'saldo anterior', 'periodo anterior', 'total_ano_anterior']):
            col_anterior = orig
        elif not col_atual and any(v in norm for v in ['valor', 'saldo', 'total', 'trimestre', 'atual', 'r$', 'saldo atual', 'total_ano_atual']):
            col_atual = orig

    if not col_atual:
        for orig, norm in zip(colunas, colunas_norm):
            if orig not in [col_codigo, col_desc, col_anterior] and orig not in cols_trimestrais.values() and not any(p in norm for p in ['%', 'av', 'ah']):
                col_atual = orig
                break

    return df, col_codigo, col_desc, col_atual, col_anterior, cols_trimestrais, cols_anos

def _identificar_tipo_demonstracao(itens: List[Dict[str, Any]]) -> str:
    """
    Identifica de forma semântica se uma lista de contas pertence à DRE ou ao Balanço Patrimonial.
    """
    pontos_dre = 0
    pontos_balanco = 0

    palavras_dre = [
        'receita', 'venda', 'faturamento', 'deducao', 'imposto', 'custo', 'cpv', 'csv',
        'despesa', 'comercial', 'marketing', 'administrativa', 'ebitda', 'lucro operacional',
        'resultado financeiro', 'juros', 'lucro liquido', 'csll', 'irpj', 'servico'
    ]
    palavras_balanco = [
        'caixa', 'banco', 'aplicacao', 'cliente', 'estoque', 'imobilizado', 'investimento',
        'intangivel', 'ativo circulante', 'passivo circulante', 'fornecedor', 'emprestimo',
        'financiamento', 'capital social', 'patrimonio liquido', 'reserva de lucro'
    ]

    for item in itens:
        t = _normalizar_texto(item.get("conta", "") + " " + item.get("codigo", ""))
        if any(w in t for w in palavras_dre) or str(item.get("codigo", "")).startswith(('4.', '3.02')):
            pontos_dre += 1
        if any(w in t for w in palavras_balanco) or str(item.get("codigo", "")).startswith(('1.', '2.', '3.01')):
            pontos_balanco += 1

    return "DRE" if pontos_dre >= pontos_balanco else "Balanco"

def gerar_modelo_planilha_exemplo() -> bytes:
    """Gera planilha Excel modelo com abas estruturadas de Balanço e DRE contendo 4 Trimestres e Totais."""
    balanco_data = [
        {
            "Codigo": "1.01.01", "Conta": "Caixa e Equivalentes de Caixa",
            "1T_2024": 340000.0, "2T_2024": 380000.0, "3T_2024": 410000.0, "4T_2024": 450000.0,
            "Total_Ano_Atual": 450000.0, "Total_Ano_Anterior": 320000.0
        },
        {
            "Codigo": "1.01.02", "Conta": "Aplicações Financeiras de Curto Prazo",
            "1T_2024": 430000.0, "2T_2024": 490000.0, "3T_2024": 550000.0, "4T_2024": 600000.0,
            "Total_Ano_Atual": 600000.0, "Total_Ano_Anterior": 400000.0
        },
        {
            "Codigo": "1.01.03", "Conta": "Contas a Receber de Clientes",
            "1T_2024": 740000.0, "2T_2024": 780000.0, "3T_2024": 820000.0, "4T_2024": 850000.0,
            "Total_Ano_Atual": 850000.0, "Total_Ano_Anterior": 720000.0
        },
        {
            "Codigo": "1.01.04", "Conta": "Estoques de Mercadorias e Produtos",
            "1T_2024": 490000.0, "2T_2024": 510000.0, "3T_2024": 505000.0, "4T_2024": 520000.0,
            "Total_Ano_Atual": 520000.0, "Total_Ano_Anterior": 480000.0
        },
        {
            "Codigo": "1.02.01", "Conta": "Investimentos e Participações",
            "1T_2024": 200000.0, "2T_2024": 200000.0, "3T_2024": 200000.0, "4T_2024": 200000.0,
            "Total_Ano_Atual": 200000.0, "Total_Ano_Anterior": 200000.0
        },
        {
            "Codigo": "1.02.02", "Conta": "Imobilizado (Máquinas, Veículos e Equipamentos)",
            "1T_2024": 1320000.0, "2T_2024": 1350000.0, "3T_2024": 1380000.0, "4T_2024": 1400000.0,
            "Total_Ano_Atual": 1400000.0, "Total_Ano_Anterior": 1300000.0
        },
        {
            "Codigo": "1.02.03", "Conta": "Intangível e Softwares",
            "1T_2024": 155000.0, "2T_2024": 160000.0, "3T_2024": 170000.0, "4T_2024": 180000.0,
            "Total_Ano_Atual": 180000.0, "Total_Ano_Anterior": 150000.0
        },
        {
            "Codigo": "2.01.01", "Conta": "Fornecedores Nacionais e Estrangeiros",
            "1T_2024": 420000.0, "2T_2024": 440000.0, "3T_2024": 460000.0, "4T_2024": 480000.0,
            "Total_Ano_Atual": 480000.0, "Total_Ano_Anterior": 410000.0
        },
        {
            "Codigo": "2.01.02", "Conta": "Empréstimos e Financiamentos de Curto Prazo",
            "1T_2024": 300000.0, "2T_2024": 310000.0, "3T_2024": 315000.0, "4T_2024": 320000.0,
            "Total_Ano_Atual": 320000.0, "Total_Ano_Anterior": 290000.0
        },
        {
            "Codigo": "2.01.03", "Conta": "Obrigações Trabalhistas e Previdenciárias",
            "1T_2024": 165000.0, "2T_2024": 170000.0, "3T_2024": 175000.0, "4T_2024": 180000.0,
            "Total_Ano_Atual": 180000.0, "Total_Ano_Anterior": 160000.0
        },
        {
            "Codigo": "2.01.04", "Conta": "Impostos e Tributos a Recolher",
            "1T_2024": 125000.0, "2T_2024": 130000.0, "3T_2024": 135000.0, "4T_2024": 140000.0,
            "Total_Ano_Atual": 140000.0, "Total_Ano_Anterior": 120000.0
        },
        {
            "Codigo": "2.02.01", "Conta": "Financiamentos Bancários de Longo Prazo",
            "1T_2024": 820000.0, "2T_2024": 800000.0, "3T_2024": 780000.0, "4T_2024": 750000.0,
            "Total_Ano_Atual": 750000.0, "Total_Ano_Anterior": 850000.0
        },
        {
            "Codigo": "2.02.02", "Conta": "Provisões para Riscos Fiscais/Cíveis",
            "1T_2024": 105000.0, "2T_2024": 110000.0, "3T_2024": 115000.0, "4T_2024": 120000.0,
            "Total_Ano_Atual": 120000.0, "Total_Ano_Anterior": 100000.0
        },
        {
            "Codigo": "3.01.01", "Conta": "Capital Social Subscrito e Integralizado",
            "1T_2024": 1500000.0, "2T_2024": 1500000.0, "3T_2024": 1500000.0, "4T_2024": 1500000.0,
            "Total_Ano_Atual": 1500000.0, "Total_Ano_Anterior": 1200000.0
        },
        {
            "Codigo": "3.01.02", "Conta": "Reservas de Lucros e Contingências",
            "1T_2024": 340000.0, "2T_2024": 380000.0, "3T_2024": 420000.0, "4T_2024": 450000.0,
            "Total_Ano_Atual": 450000.0, "Total_Ano_Anterior": 300000.0
        },
        {
            "Codigo": "3.01.03", "Conta": "Lucros ou Prejuízos Acumulados",
            "1T_2024": 170000.0, "2T_2024": 200000.0, "3T_2024": 230000.0, "4T_2024": 260000.0,
            "Total_Ano_Atual": 260000.0, "Total_Ano_Anterior": 140000.0
        }
    ]
    dre_data = [
        {
            "Codigo": "4.01.01", "Conta": "Receita Bruta de Vendas e Serviços",
            "1T_2024": 1050000.0, "2T_2024": 1150000.0, "3T_2024": 1250000.0, "4T_2024": 1350000.0,
            "Total_Ano_Atual": 4800000.0, "Total_Ano_Anterior": 3950000.0
        },
        {
            "Codigo": "4.01.02", "Conta": "Deduções da Receita Bruta (Impostos e Devoluções)",
            "1T_2024": -125000.0, "2T_2024": -140000.0, "3T_2024": -150000.0, "4T_2024": -165000.0,
            "Total_Ano_Atual": -580000.0, "Total_Ano_Anterior": -470000.0
        },
        {
            "Codigo": "4.02.01", "Conta": "Custos dos Produtos e Serviços Vendidos (CPV/CSV)",
            "1T_2024": -515000.0, "2T_2024": -560000.0, "3T_2024": -610000.0, "4T_2024": -665000.0,
            "Total_Ano_Atual": -2350000.0, "Total_Ano_Anterior": -1980000.0
        },
        {
            "Codigo": "4.03.01", "Conta": "Despesas com Vendas e Marketing",
            "1T_2024": -85000.0, "2T_2024": -92000.0, "3T_2024": -98000.0, "4T_2024": -105000.0,
            "Total_Ano_Atual": -380000.0, "Total_Ano_Anterior": -310000.0
        },
        {
            "Codigo": "4.03.02", "Conta": "Despesas Gerais e Administrativas",
            "1T_2024": -120000.0, "2T_2024": -128000.0, "3T_2024": -134000.0, "4T_2024": -138000.0,
            "Total_Ano_Atual": -520000.0, "Total_Ano_Anterior": -450000.0
        },
        {
            "Codigo": "4.03.03", "Conta": "Outras Receitas e Despesas Operacionais",
            "1T_2024": 10000.0, "2T_2024": 11000.0, "3T_2024": 12000.0, "4T_2024": 12000.0,
            "Total_Ano_Atual": 45000.0, "Total_Ano_Anterior": 30000.0
        },
        {
            "Codigo": "4.04.01", "Conta": "Receitas Financeiras",
            "1T_2024": 18000.0, "2T_2024": 21000.0, "3T_2024": 22000.0, "4T_2024": 24000.0,
            "Total_Ano_Atual": 85000.0, "Total_Ano_Anterior": 65000.0
        },
        {
            "Codigo": "4.04.02", "Conta": "Despesas Financeiras e Juros",
            "1T_2024": -32000.0, "2T_2024": -34000.0, "3T_2024": -36000.0, "4T_2024": -38000.0,
            "Total_Ano_Atual": -140000.0, "Total_Ano_Anterior": -130000.0
        },
        {
            "Codigo": "4.05.01", "Conta": "Provisão para IRPJ e CSLL",
            "1T_2024": -52000.0, "2T_2024": -58000.0, "3T_2024": -63000.0, "4T_2024": -67000.0,
            "Total_Ano_Atual": -240000.0, "Total_Ano_Anterior": -195000.0
        }
    ]
    # Enriquecimento com colunas explícitas para demonstrar suporte Multi-Ano (2024, 2023, 2022)
    for row in balanco_data:
        row["2024"] = row.get("Total_Ano_Atual", 0.0)
        row["2023"] = row.get("Total_Ano_Anterior", 0.0)
        row["2022"] = round(row.get("Total_Ano_Anterior", 0.0) * 0.9, 2)
    for row in dre_data:
        row["2024"] = row.get("Total_Ano_Atual", 0.0)
        row["2023"] = row.get("Total_Ano_Anterior", 0.0)
        row["2022"] = round(row.get("Total_Ano_Anterior", 0.0) * 0.88, 2)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(balanco_data).to_excel(writer, sheet_name='Balanco_Patrimonial', index=False)
        pd.DataFrame(dre_data).to_excel(writer, sheet_name='DRE', index=False)
    output.seek(0)
    return output.getvalue()

def processar_demonstracoes_com_jev(
    conteudo_arquivo: bytes,
    nome_arquivo: str,
    ano_destino: Optional[str] = None,
    trimestres_permitidos: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Motor Universal de Ingestão Contábil:
    Lê qualquer estrutura de planilha (Excel ou CSV), detecta cabeçalhos, extrai códigos,
    nomes de contas, saldos anuais e trimestrais (1T, 2T, 3T, 4T) filtrando estritamente pelos trimestres e ano autorizados.
    """
    # 1. Carregamento dos dados brutos (Excel ou CSV)
    dfs_por_aba = {}
    nome_lower = (nome_arquivo or '').lower()

    if nome_lower.endswith('.csv'):
        df_csv = None
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df_csv = pd.read_csv(io.BytesIO(conteudo_arquivo), sep=None, engine='python', encoding=enc)
                break
            except Exception:
                continue
        if df_csv is None:
            df_csv = pd.read_csv(io.BytesIO(conteudo_arquivo), sep=';', encoding='latin-1')
        dfs_por_aba['CSV_Principal'] = df_csv
    else:
        lido_com_sucesso = False
        # Tentativa 1: ExcelFile padrão (detecta openpyxl ou xlrd)
        try:
            excel_file = pd.ExcelFile(io.BytesIO(conteudo_arquivo))
            for sheet in excel_file.sheet_names:
                dfs_por_aba[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
            lido_com_sucesso = bool(dfs_por_aba)
        except Exception:
            pass

        # Tentativa 2: openpyxl explícito (.xlsx moderno)
        if not lido_com_sucesso:
            try:
                excel_file = pd.ExcelFile(io.BytesIO(conteudo_arquivo), engine='openpyxl')
                for sheet in excel_file.sheet_names:
                    dfs_por_aba[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
                lido_com_sucesso = bool(dfs_por_aba)
            except Exception:
                pass

        # Tentativa 3: xlrd explícito (Excel 97-2003 .xls clássico)
        if not lido_com_sucesso:
            try:
                excel_file = pd.ExcelFile(io.BytesIO(conteudo_arquivo), engine='xlrd')
                for sheet in excel_file.sheet_names:
                    dfs_por_aba[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
                lido_com_sucesso = bool(dfs_por_aba)
            except Exception:
                pass

        # Tentativa 4: HTML disfarçado de XLS (padrão de exportação de sistemas contábeis como Domínio/Senior/Totvs)
        if not lido_com_sucesso:
            try:
                tabelas_html = pd.read_html(io.BytesIO(conteudo_arquivo))
                if tabelas_html:
                    for idx, tbl in enumerate(tabelas_html):
                        dfs_por_aba[f'Tabela_{idx+1}'] = tbl
                    lido_com_sucesso = True
            except Exception:
                pass

        # Tentativa 5: Fallback CSV/Texto com delimitadores universais
        if not lido_com_sucesso:
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df_fallback = pd.read_csv(io.BytesIO(conteudo_arquivo), sep=None, engine='python', encoding=enc)
                    dfs_por_aba['Planilha_Importada'] = df_fallback
                    lido_com_sucesso = True
                    break
                except Exception:
                    continue

        if not dfs_por_aba:
            raise ValueError(f"Não foi possível abrir o arquivo '{nome_arquivo}'. O formato de dados não pôde ser interpretado.")

    # 2. Extração Estruturada por Aba e Detecção de Exercício / Anos
    anos_relatorio = _detectar_anos_relatorio(dfs_por_aba, nome_arquivo)
    
    # Se ano_destino foi fornecido pelo usuário/cadastro, prevalece com autoridade máxima
    if ano_destino and str(ano_destino).strip():
        ano_principal = str(ano_destino).strip()
    elif anos_relatorio:
        ano_principal = anos_relatorio[0]
    else:
        ano_principal = "2026"

    ano_secundario = anos_relatorio[1] if len(anos_relatorio) > 1 and anos_relatorio[1] != ano_principal else str(int(ano_principal) - 1)

    # Validação estrita de trimestres autorizados (Regra de Governança do Usuário)
    # Se o usuário não escolheu trimestres, a importação é bloqueada e nada sobe!
    if trimestres_permitidos is not None and len(trimestres_permitidos) == 0:
        raise ValueError("Nenhum trimestre foi selecionado para importação. A importação foi cancelada por segurança.")

    trim_permitidos_set = set(trimestres_permitidos) if trimestres_permitidos else {"1T", "2T", "3T", "4T"}

    contas_balanco_brutas = []
    itens_dre_brutos = []

    for sheet_name, df_raw in dfs_por_aba.items():
        if df_raw.empty:
            continue

        blocos = _detectar_e_dividir_blocos_horizontais(df_raw)
        linhas_aba = []

        if len(blocos) > 1:
            # Planilha com 2 ou mais DREs/Demonstrações lado a lado (ex.: 1º Trimestre e 2º Trimestre)
            mapa_contas_unificadas: Dict[str, Dict[str, Any]] = {}

            for trim_tag, sub_df in blocos:
                # Se o bloco for de um trimestre não autorizado pelo usuário, pula completamente!
                if trim_tag in ["1T", "2T", "3T", "4T"] and trim_tag not in trim_permitidos_set:
                    continue

                sub_df_limpo, col_cod, col_desc, col_atual, col_anterior, cols_trim, cols_anos = _encontrar_cabecalho_e_colunas(sub_df)
                if not col_desc:
                    continue

                for _, row in sub_df_limpo.iterrows():
                    desc_raw = str(row.get(col_desc, '')).strip()
                    if not desc_raw or desc_raw.lower() in ['nan', 'none', 'null', 'total', 'totais']:
                        continue

                    codigo_str = str(row.get(col_cod, '')).strip() if col_cod else ''
                    if codigo_str.lower() in ['nan', 'none', 'null', '-', '.']:
                        codigo_str = ''
                    if not codigo_str:
                        match_cod = re.match(r'^([\d\.]+)\s*[-–]?\s*(.*)', desc_raw)
                        if match_cod:
                            codigo_str = match_cod.group(1).strip()
                            desc_raw = match_cod.group(2).strip()

                    if any(h in _normalizar_texto(desc_raw) for h in ['descricao', 'especificacao', 'nome da conta', 'conta contabil']):
                        continue

                    saldo_bloco = _limpar_valor_numerico_universal(row.get(col_atual)) if col_atual else 0.0
                    saldo_ant_bloco = _limpar_valor_numerico_universal(row.get(col_anterior)) if col_anterior else 0.0

                    chave_conta = f"{codigo_str}_{_normalizar_texto(desc_raw)}" if codigo_str else _normalizar_texto(desc_raw)
                    if not chave_conta or len(desc_raw) < 2:
                        continue

                    if chave_conta not in mapa_contas_unificadas:
                        mapa_contas_unificadas[chave_conta] = {
                            "codigo": codigo_str,
                            "conta": desc_raw,
                            "saldo_atual": 0.0,
                            "saldo_anterior": saldo_ant_bloco,
                            "saldos_trimestrais": {
                                "1T": 0.0,
                                "2T": 0.0,
                                "3T": 0.0,
                                "4T": 0.0,
                                "anual": 0.0
                            },
                            "saldos_anuais": {ano_principal: 0.0, ano_secundario: 0.0 if ano_destino else saldo_ant_bloco}
                        }

                    # Aloca o saldo estritamente no trimestre autorizado
                    if trim_tag in trim_permitidos_set:
                        mapa_contas_unificadas[chave_conta]["saldos_trimestrais"][trim_tag] = saldo_bloco
                    elif trim_tag not in ["1T", "2T", "3T", "4T"]:
                        # Bloco genérico só entra no primeiro trimestre permitido
                        for t_cand in ["1T", "2T", "3T", "4T"]:
                            if t_cand in trim_permitidos_set and mapa_contas_unificadas[chave_conta]["saldos_trimestrais"][t_cand] == 0:
                                mapa_contas_unificadas[chave_conta]["saldos_trimestrais"][t_cand] = saldo_bloco
                                break

                    if saldo_ant_bloco != 0 and not ano_destino:
                        mapa_contas_unificadas[chave_conta]["saldo_anterior"] = saldo_ant_bloco
                        mapa_contas_unificadas[chave_conta]["saldos_anuais"][ano_secundario] = saldo_ant_bloco

            for conta_unif in mapa_contas_unificadas.values():
                # Zera qualquer trimestre que não esteja nos permitidos
                for t in ["1T", "2T", "3T", "4T"]:
                    if t not in trim_permitidos_set:
                        conta_unif["saldos_trimestrais"][t] = 0.0

                soma_trim = (
                    conta_unif["saldos_trimestrais"]["1T"] +
                    conta_unif["saldos_trimestrais"]["2T"] +
                    conta_unif["saldos_trimestrais"]["3T"] +
                    conta_unif["saldos_trimestrais"]["4T"]
                )
                conta_unif["saldo_atual"] = soma_trim
                conta_unif["saldos_trimestrais"]["anual"] = soma_trim
                conta_unif["saldos_anuais"][ano_principal] = soma_trim
                linhas_aba.append(conta_unif)

        else:
            # Planilha Convencional (Bloco único vertical)
            df, col_cod, col_desc, col_atual, col_anterior, cols_trim, cols_anos = _encontrar_cabecalho_e_colunas(df_raw)
            if not col_desc:
                continue

            for _, row in df.iterrows():
                desc_raw = str(row.get(col_desc, '')).strip()
                if not desc_raw or desc_raw.lower() in ['nan', 'none', 'null', 'total', 'totais']:
                    continue

                codigo_str = str(row.get(col_cod, '')).strip() if col_cod else ''
                if codigo_str.lower() in ['nan', 'none', 'null', '-', '.']:
                    codigo_str = ''
                if not codigo_str:
                    match_cod = re.match(r'^([\d\.]+)\s*[-–]?\s*(.*)', desc_raw)
                    if match_cod:
                        codigo_str = match_cod.group(1).strip()
                        desc_raw = match_cod.group(2).strip()

                if any(h in _normalizar_texto(desc_raw) for h in ['descricao', 'especificacao', 'nome da conta', 'conta contabil']):
                    continue

                saldo_atual = _limpar_valor_numerico_universal(row.get(col_atual)) if col_atual else 0.0
                saldo_ant = _limpar_valor_numerico_universal(row.get(col_anterior)) if col_anterior else 0.0

                # Extração de Trimestres reais das colunas
                s_1t = _limpar_valor_numerico_universal(row.get(cols_trim.get('1T'))) if ('1T' in cols_trim and '1T' in trim_permitidos_set) else 0.0
                s_2t = _limpar_valor_numerico_universal(row.get(cols_trim.get('2T'))) if ('2T' in cols_trim and '2T' in trim_permitidos_set) else 0.0
                s_3t = _limpar_valor_numerico_universal(row.get(cols_trim.get('3T'))) if ('3T' in cols_trim and '3T' in trim_permitidos_set) else 0.0
                s_4t = _limpar_valor_numerico_universal(row.get(cols_trim.get('4T'))) if ('4T' in cols_trim and '4T' in trim_permitidos_set) else 0.0

                # Se a planilha não possuía colunas de trimestres, mas tinha uma única coluna de saldo atual,
                # e há trimestres permitidos, alocamos no primeiro trimestre autorizado para manter amarração 100% fiel
                if not cols_trim and saldo_atual != 0.0:
                    if len(trim_permitidos_set) >= 1:
                        t_unico = sorted(list(trim_permitidos_set))[0]
                        if t_unico == '1T': s_1t = saldo_atual
                        elif t_unico == '2T': s_2t = saldo_atual
                        elif t_unico == '3T': s_3t = saldo_atual
                        elif t_unico == '4T': s_4t = saldo_atual
                    else:
                        s_1t = 0.0
                        s_2t = 0.0
                        s_3t = 0.0
                        s_4t = 0.0

                s_1t = s_1t or 0.0
                s_2t = s_2t or 0.0
                s_3t = s_3t or 0.0
                s_4t = s_4t or 0.0

                soma_trim_vert = s_1t + s_2t + s_3t + s_4t
                if soma_trim_vert != 0.0:
                    saldo_final = soma_trim_vert
                else:
                    saldo_final = saldo_atual

                # Extração de Saldos Multi-Ano com Isolamento Estrito por ano_destino
                saldos_anuais = {a: 0.0 for a in ["2026", "2025", "2024", "2023"]}
                if ano_destino and str(ano_destino).strip():
                    # Se o usuário escolheu explicitamente o ano_destino (ex: 2026),
                    # APENAS o ano escolhido recebe o saldo importado! Nenhum outro ano é contaminado!
                    saldos_anuais[ano_principal] = saldo_final
                else:
                    if cols_anos:
                        for ano_k, col_ano_k in cols_anos.items():
                            val_k = _limpar_valor_numerico_universal(row.get(col_ano_k))
                            if val_k is not None:
                                saldos_anuais[ano_k] = val_k
                    saldos_anuais[ano_principal] = saldo_final
                    if ano_secundario not in saldos_anuais or saldos_anuais[ano_secundario] == 0.0:
                        saldos_anuais[ano_secundario] = saldo_ant

                if len(desc_raw) >= 2:
                    linhas_aba.append({
                        "codigo": codigo_str,
                        "conta": desc_raw,
                        "saldo_atual": saldo_final,
                        "saldo_anterior": saldo_ant,
                        "saldos_trimestrais": {
                            "1T": s_1t,
                            "2T": s_2t,
                            "3T": s_3t,
                            "4T": s_4t,
                            "anual": saldo_final
                        },
                        "saldos_anuais": saldos_anuais
                    })

        if not linhas_aba:
            continue

        nome_aba_norm = _normalizar_texto(sheet_name)
        if any(w in nome_aba_norm for w in ['dre', 'resultado']):
            itens_dre_brutos.extend(linhas_aba)
        elif any(w in nome_aba_norm for w in ['balanco', 'bp', 'patrimonio']):
            contas_balanco_brutas.extend(linhas_aba)
        else:
            tipo = _identificar_tipo_demonstracao(linhas_aba)
            if tipo == "DRE":
                itens_dre_brutos.extend(linhas_aba)
            else:
                contas_balanco_brutas.extend(linhas_aba)

    somente_dre = len(itens_dre_brutos) > 0 and len(contas_balanco_brutas) == 0
    somente_balanco = len(contas_balanco_brutas) > 0 and len(itens_dre_brutos) == 0

    # 3. Processamento e Classificação JEV para o Balanço
    contas_processadas = []
    for c in contas_balanco_brutas:
        s_atual = c["saldo_atual"]
        s_ant = c["saldo_anterior"]
        var_pct = ((s_atual - s_ant) / abs(s_ant) * 100) if s_ant != 0 else 0.0

        decisao = jev_service.classificar_conta_contabil(
            conta=f"{c['codigo']} - {c['conta']}" if c['codigo'] else c['conta'],
            descricao=f"Balanço Patrimonial. Saldo Atual: R$ {s_atual:,.2f}",
            saldo=s_atual
        )

        contas_processadas.append({
            "codigo": c["codigo"],
            "conta": c["conta"],
            "tipo": "Balanco",
            "saldo_atual": s_atual,
            "saldo_anterior": s_ant,
            "saldos_trimestrais": c["saldos_trimestrais"],
            "saldos_anuais": c.get("saldos_anuais", {}),
            "variacao_nominal": s_atual - s_ant,
            "variacao_percentual": round(var_pct, 2),
            "grupo": decisao["grupo_escolhido"],
            "confianca_ia": decisao["confianca_classificacao"],
            "score_relevancia": decisao["score_relevancia"],
            "probabilidade_anomalia": decisao["probabilidade_anomalia"],
            "badge_ia": decisao["badge"]
        })

    todos_codigos_bp = [str(c.get("codigo", "")).strip().rstrip(".") for c in contas_processadas if str(c.get("codigo", "")).strip()]

    def _eh_conta_sintetica_bp(c: Dict[str, Any]) -> bool:
        cod = str(c.get("codigo", "")).strip().rstrip(".")
        desc_norm = _normalizar_texto(c.get("conta", ""))
        # 1. Se o código for pai de outra conta presente no balanço (ex: '1' é pai de '1.1', '1.1' é pai de '1.1.01')
        if cod:
            for outro in todos_codigos_bp:
                if outro != cod and outro.startswith(cod + "."):
                    return True
        # 2. Títulos totalizadores sintéticos clássicos
        titulos_sinteticos = {
            "ativo", "ativo total", "total do ativo", "total ativo",
            "ativo circulante", "total do ativo circulante",
            "ativo nao circulante", "total do ativo nao circulante",
            "passivo", "passivo total", "total do passivo", "total passivo",
            "passivo e patrimonio liquido", "total do passivo e patrimonio liquido",
            "passivo circulante", "total do passivo circulante",
            "passivo nao circulante", "total do passivo nao circulante",
            "patrimonio liquido", "total do patrimonio liquido"
        }
        if desc_norm in titulos_sinteticos and len(contas_processadas) > 6:
            return True
        return False

    def _classificar_grupo_balanco(c):
        cod = str(c.get("codigo", "")).strip()
        g = _normalizar_texto(c.get("grupo", ""))
        desc = _normalizar_texto(c.get("conta", ""))

        # Prioridade 1: Patrimônio Líquido (Códigos 2.03, 2.3, 2.04, 2.4, 3.x ou termos de PL)
        if cod.startswith(("2.03", "2.3", "2.04", "2.4", "3")):
            return "patrimonio_liquido"
        if any(w in desc for w in ['patrimonio liquido', 'capital social', 'reserva de', 'reservas de', 'lucros acumulados', 'prejuizos acumulados', 'ajuste de avaliacao']):
            return "patrimonio_liquido"

        # Prioridade 2: Códigos estruturados de Ativo e Passivo
        if cod.startswith(("1.01", "1.1")): return "ativo_circulante"
        if cod.startswith(("1.02", "1.2", "1.03", "1.3")): return "ativo_nao_circulante"
        if cod.startswith(("2.01", "2.1")): return "passivo_circulante"
        if cod.startswith(("2.02", "2.2")): return "passivo_nao_circulante"

        # Prioridade 3: Descrição semântica explícita antes de cair em grupo genérico
        if any(w in desc for w in ['fornecedor', 'emprestimo', 'financiamento', 'obrigacoes', 'salarios a pagar', 'tributos a recolher', 'impostos a pagar', 'contas a pagar', 'provisao', 'dividendos a pagar']):
            if any(w in desc for w in ['longo prazo', 'nao circulante']):
                return "passivo_nao_circulante"
            return "passivo_circulante"
        if any(w in desc for w in ['imobilizado', 'intangivel', 'investimento', 'realizavel a longo prazo', 'depreciacao acumulada', 'amortizacao acumulada']):
            return "ativo_nao_circulante"

        # Prioridade 4: Se começa com 2, JAMAIS pode cair em ativo!
        if cod.startswith("2"):
            if "nao circulante" in desc or "longo prazo" in desc:
                return "passivo_nao_circulante"
            return "passivo_circulante"
        if cod.startswith("1"):
            if "nao circulante" in desc or "longo prazo" in desc:
                return "ativo_nao_circulante"
            return "ativo_circulante"

        # Prioridade 5: Classificação do JEV
        if "patrimonio liquido" in g: return "patrimonio_liquido"
        if "passivo nao circulante" in g: return "passivo_nao_circulante"
        if "passivo circulante" in g or "passivo" in g: return "passivo_circulante"
        if "ativo nao circulante" in g: return "ativo_nao_circulante"
        return "ativo_circulante"

    # Filtra apenas contas analíticas (folhas) para jamais duplicar somando conta sintética mãe + filhas
    contas_analiticas_bp = [c for c in contas_processadas if not _eh_conta_sintetica_bp(c)]
    if not contas_analiticas_bp:
        contas_analiticas_bp = contas_processadas

    ativo_circulante = sum(c["saldo_atual"] for c in contas_analiticas_bp if _classificar_grupo_balanco(c) == "ativo_circulante")
    ativo_nao_circulante = sum(c["saldo_atual"] for c in contas_analiticas_bp if _classificar_grupo_balanco(c) == "ativo_nao_circulante")
    ativo_total = ativo_circulante + ativo_nao_circulante

    passivo_circulante = sum(c["saldo_atual"] for c in contas_analiticas_bp if _classificar_grupo_balanco(c) == "passivo_circulante")
    passivo_nao_circulante = sum(c["saldo_atual"] for c in contas_analiticas_bp if _classificar_grupo_balanco(c) == "passivo_nao_circulante")
    patrimonio_liquido = sum(c["saldo_atual"] for c in contas_analiticas_bp if _classificar_grupo_balanco(c) == "patrimonio_liquido")
    passivo_total = passivo_circulante + passivo_nao_circulante + patrimonio_liquido

    disponibilidades = sum(c["saldo_atual"] for c in contas_analiticas_bp if "disponib" in c.get("grupo", "").lower() or any(w in c.get("conta", "").lower() for w in ['caixa', 'banco', 'aplica']))
    estoques = sum(c["saldo_atual"] for c in contas_analiticas_bp if "estoque" in c.get("grupo", "").lower() or "estoque" in c.get("conta", "").lower())
    realizavel_longo_prazo = sum(
        c["saldo_atual"] for c in contas_analiticas_bp 
        if ("realizavel" in _normalizar_texto(c.get("conta", "")) or "longo prazo" in _normalizar_texto(c.get("conta", "")) or c.get("codigo", "").startswith("1.02.01") or c.get("codigo", "").startswith("1.2.1"))
        and "passivo" not in _normalizar_texto(c.get("grupo", ""))
    )

    # 4. Processamento da DRE
    itens_dre = []
    for item in itens_dre_brutos:
        s_atual = item["saldo_atual"]
        s_ant = item["saldo_anterior"]
        var_pct = ((s_atual - s_ant) / abs(s_ant) * 100) if s_ant != 0 else 0.0

        itens_dre.append({
            "codigo": item["codigo"],
            "conta": item["conta"],
            "saldo_atual": s_atual,
            "saldo_anterior": s_ant,
            "saldos_trimestrais": item["saldos_trimestrais"],
            "saldos_anuais": item.get("saldos_anuais", {}),
            "variacao_percentual": round(var_pct, 2)
        })

    def _extrair_metricas_reais_dre(itens_dre_lista: List[Dict[str, Any]], chave_periodo: Optional[str] = None) -> Tuple[float, float, float, float, float]:
        def _obter_val(item: Dict[str, Any]) -> float:
            if chave_periodo and chave_periodo in item.get("saldos_trimestrais", {}):
                return item["saldos_trimestrais"].get(chave_periodo, 0.0)
            return item.get("saldo_atual", 0.0)

        # 1. Receita Bruta
        rec_bruta_itens = [abs(_obter_val(i)) for i in itens_dre_lista if any(w in _normalizar_texto(i["conta"]) for w in ['receita operacional bruta', 'receita bruta', 'faturamento bruto', 'vendas bruta'])]
        if not rec_bruta_itens:
            rec_bruta_itens = [abs(_obter_val(i)) for i in itens_dre_lista if any(w in _normalizar_texto(i["conta"]) for w in ['receita', 'faturamento', 'vendas']) and _obter_val(i) != 0]
        rec_b = max(rec_bruta_itens) if rec_bruta_itens else 0.0

        # 2. Receita Líquida
        rec_liq_itens = [abs(_obter_val(i)) for i in itens_dre_lista if any(w in _normalizar_texto(i["conta"]) for w in ['receita liquida', 'receita operacional liquida', 'receita liq'])]
        if rec_liq_itens:
            rec_l = rec_liq_itens[0]
        else:
            deducoes = sum(abs(_obter_val(i)) for i in itens_dre_lista if any(w in _normalizar_texto(i["conta"]) for w in ['deduc', 'impostos sobre', 'tributos sobre', 'devoluc', 'abatimento']))
            rec_l = (rec_b - deducoes) if deducoes > 0 else rec_b

        # 3. Lucro Bruto
        lucro_bruto_itens = [_obter_val(i) for i in itens_dre_lista if any(w in _normalizar_texto(i["conta"]) for w in ['lucro bruto', 'resultado bruto'])]
        if lucro_bruto_itens:
            l_bruto = lucro_bruto_itens[0]
        else:
            custos = sum(abs(_obter_val(i)) for i in itens_dre_lista if any(w in _normalizar_texto(i["conta"]) for w in ['custo', 'cmv', 'cpv', 'csp']))
            l_bruto = (rec_l - custos) if custos > 0 else rec_l

        # 4. Lucro Líquido
        lucro_liq_itens = [_obter_val(i) for i in itens_dre_lista if any(w in _normalizar_texto(i["conta"]) for w in ['lucro liquido', 'resultado liquido', 'lucro do exercicio'])]
        if lucro_liq_itens:
            l_liq = lucro_liq_itens[0]
        else:
            l_liq = sum(_obter_val(i) for i in itens_dre_lista if _obter_val(i) != 0)

        # 5. EBITDA
        ebitda_itens = [_obter_val(i) for i in itens_dre_lista if any(w in _normalizar_texto(i["conta"]) for w in ['ebitda', 'lajida'])]
        if ebitda_itens:
            ebitda_v = ebitda_itens[0]
        else:
            depreciacao = sum(abs(_obter_val(i)) for i in itens_dre_lista if any(w in _normalizar_texto(i["conta"]) for w in ['depreciac', 'amortizac']))
            ebitda_v = l_liq + depreciacao if depreciacao > 0 else l_liq

        return rec_b, rec_l, l_bruto, ebitda_v, l_liq

    receita_bruta, receita_liquida, lucro_bruto, ebitda, lucro_liquido = _extrair_metricas_reais_dre(itens_dre)

    # 5. Cálculo dos Índices Financeiros Anuais e por Trimestre com métricas reais
    indices_anual = CalculadoraIndicesFinanceiros.calcular_todos_indices(
        ativo_circulante=ativo_circulante,
        ativo_nao_circulante=ativo_nao_circulante,
        disponibilidades=disponibilidades,
        estoques=estoques,
        passivo_circulante=passivo_circulante,
        passivo_nao_circulante=passivo_nao_circulante,
        patrimonio_liquido=patrimonio_liquido,
        receita_liquida=receita_liquida,
        lucro_bruto=lucro_bruto,
        ebitda=ebitda,
        lucro_liquido=lucro_liquido,
        realizavel_longo_prazo=realizavel_longo_prazo
    )

    # Indicadores individuais por trimestre (1T, 2T, 3T, 4T)
    indicadores_por_periodo = {"anual": indices_anual}
    for t_key in ["1T", "2T", "3T", "4T"]:
        rec_b_t, rec_l_t, l_bruto_t, ebitda_t, lucro_t = _extrair_metricas_reais_dre(itens_dre, chave_periodo=t_key)

        indicadores_por_periodo[t_key] = CalculadoraIndicesFinanceiros.calcular_todos_indices(
            ativo_circulante=ativo_circulante if trimestres_permitidos is None or t_key in trimestres_permitidos else 0.0,
            ativo_nao_circulante=ativo_nao_circulante if trimestres_permitidos is None or t_key in trimestres_permitidos else 0.0,
            disponibilidades=disponibilidades if trimestres_permitidos is None or t_key in trimestres_permitidos else 0.0,
            estoques=estoques if trimestres_permitidos is None or t_key in trimestres_permitidos else 0.0,
            passivo_circulante=passivo_circulante if trimestres_permitidos is None or t_key in trimestres_permitidos else 0.0,
            passivo_nao_circulante=passivo_nao_circulante if trimestres_permitidos is None or t_key in trimestres_permitidos else 0.0,
            patrimonio_liquido=patrimonio_liquido if trimestres_permitidos is None or t_key in trimestres_permitidos else 0.0,
            receita_liquida=rec_l_t,
            lucro_bruto=l_bruto_t,
            ebitda=ebitda_t,
            lucro_liquido=lucro_t,
            realizavel_longo_prazo=realizavel_longo_prazo if trimestres_permitidos is None or t_key in trimestres_permitidos else 0.0
        )

    # 5.1 Identificação e Cálculo de Múltiplos Anos (Exercícios Financeiros)
    # Garante sempre a presença dos exercícios base (2026, 2025, 2024, 2023) para que nenhum ano suma ao importar
    anos_set = {"2026", "2025", "2024", "2023"}
    if ano_principal:
        anos_set.add(str(ano_principal))
    if ano_secundario:
        anos_set.add(str(ano_secundario))
    for c in contas_processadas:
        anos_set.update(c.get("saldos_anuais", {}).keys())
    for it in itens_dre:
        anos_set.update(it.get("saldos_anuais", {}).keys())
    if anos_relatorio:
        anos_set.update(anos_relatorio)

    anos_disponiveis = sorted(list(anos_set), reverse=True)
    if ano_principal not in anos_disponiveis:
        anos_disponiveis = [ano_principal] + [a for a in anos_disponiveis if a != ano_principal]

    diferenca_balanco = round(abs(ativo_total - passivo_total), 2)
    balanco_equilibrado = diferenca_balanco < 100.0 or somente_dre

    # 6. Soluções e Parecer de Gestão Confiáveis do JEV
    totais_balanco = {
        "ativo_circulante": ativo_circulante,
        "ativo_nao_circulante": ativo_nao_circulante,
        "ativo_total": ativo_total,
        "passivo_circulante": passivo_circulante,
        "passivo_nao_circulante": passivo_nao_circulante,
        "patrimonio_liquido": patrimonio_liquido,
        "passivo_total": passivo_total,
        "disponibilidades": disponibilidades
    }
    totais_dre = {
        "receita_bruta": receita_bruta,
        "lucro_liquido": lucro_liquido
    }

    parecer_gestao_jev = jev_service.gerar_solucoes_gestao_jev(
        indices=indices_anual,
        totais_balanco=totais_balanco,
        totais_dre=totais_dre
    )

    # 7. Destaques Estratégicos para Acionistas
    destaques_acionistas = []
    if contas_analiticas_bp:
        destaques_acionistas = sorted(
            [c for c in contas_analiticas_bp if c["score_relevancia"] >= 1.5 or c["probabilidade_anomalia"] > 0.4],
            key=lambda x: x["score_relevancia"],
            reverse=True
        )[:5]
    elif itens_dre:
        destaques_dre = sorted(itens_dre, key=lambda x: abs(x["saldo_atual"]), reverse=True)[:5]
        for it in destaques_dre:
            destaques_acionistas.append({
                "codigo": it["codigo"],
                "conta": it["conta"],
                "tipo": "DRE",
                "saldo_atual": it["saldo_atual"],
                "saldo_anterior": it["saldo_anterior"],
                "saldos_trimestrais": it["saldos_trimestrais"],
                "variacao_nominal": it["saldo_atual"] - it["saldo_anterior"],
                "variacao_percentual": it["variacao_percentual"],
                "grupo": "DRE - Resultado Estratégico",
                "confianca_ia": 0.98,
                "score_relevancia": 8.5,
                "probabilidade_anomalia": 0.0,
                "badge_ia": "⚡🧠 Destaque DRE"
            })

    # 8. Conglutinação Inteligente na Matriz DRE da Empresa e Totais por Exercício/Ano
    dre_matriz_por_ano = {}
    totais_balanco_por_ano = {}
    totais_dre_por_ano = {}
    indicadores_por_ano = {}

    for ano_k in anos_disponiveis:
        # 8.1 Ajusta as contas para o ano_k específico
        contas_k = []
        for c in (itens_dre + contas_analiticas_bp):
            s_k = c.get("saldos_anuais", {}).get(ano_k, (c.get("saldo_atual", 0.0) if ano_k == ano_principal else 0.0))
            c_copia = dict(c)
            c_copia["saldo_atual"] = s_k
            if ano_k == ano_principal:
                c_copia["saldos_trimestrais"] = c.get("saldos_trimestrais", {})
            else:
                # Exercícios anteriores sem trimestres detalhados ou com saldos próprios
                c_copia["saldos_trimestrais"] = c.get("saldos_trimestrais_por_ano", {}).get(ano_k, {"1T": 0.0, "2T": 0.0, "3T": 0.0, "4T": 0.0, "anual": s_k})
            contas_k.append(c_copia)

        # 8.2 Matriz DRE para o ano_k
        dre_matriz_por_ano[ano_k] = conglutinador_jev.conglutinar_dados_na_matriz(
            contas_k,
            trimestres_permitidos=list(trim_permitidos_set) if ano_k == ano_principal and trimestres_permitidos else None
        )

        # 8.3 Totais de Balanço para o ano_k (estritamente sobre contas analíticas deduplicadas!)
        ac_k = sum(c.get("saldos_anuais", {}).get(ano_k, (c.get("saldo_atual", 0.0) if ano_k == ano_principal else 0.0)) for c in contas_analiticas_bp if _classificar_grupo_balanco(c) == "ativo_circulante")
        anc_k = sum(c.get("saldos_anuais", {}).get(ano_k, (c.get("saldo_atual", 0.0) if ano_k == ano_principal else 0.0)) for c in contas_analiticas_bp if _classificar_grupo_balanco(c) == "ativo_nao_circulante")
        disp_k = sum(c.get("saldos_anuais", {}).get(ano_k, (c.get("saldo_atual", 0.0) if ano_k == ano_principal else 0.0)) for c in contas_analiticas_bp if "disponib" in c.get("grupo", "").lower() or any(w in c.get("conta", "").lower() for w in ['caixa', 'banco', 'aplica']))
        est_k = sum(c.get("saldos_anuais", {}).get(ano_k, (c.get("saldo_atual", 0.0) if ano_k == ano_principal else 0.0)) for c in contas_analiticas_bp if "estoque" in c.get("grupo", "").lower() or "estoque" in c.get("conta", "").lower())
        pc_k = sum(c.get("saldos_anuais", {}).get(ano_k, (c.get("saldo_atual", 0.0) if ano_k == ano_principal else 0.0)) for c in contas_analiticas_bp if _classificar_grupo_balanco(c) == "passivo_circulante")
        pnc_k = sum(c.get("saldos_anuais", {}).get(ano_k, (c.get("saldo_atual", 0.0) if ano_k == ano_principal else 0.0)) for c in contas_analiticas_bp if _classificar_grupo_balanco(c) == "passivo_nao_circulante")
        pl_k = sum(c.get("saldos_anuais", {}).get(ano_k, (c.get("saldo_atual", 0.0) if ano_k == ano_principal else 0.0)) for c in contas_analiticas_bp if _classificar_grupo_balanco(c) == "patrimonio_liquido")

        totais_balanco_por_ano[ano_k] = {
            "ativo_circulante": ac_k,
            "ativo_nao_circulante": anc_k,
            "ativo_total": ac_k + anc_k,
            "passivo_circulante": pc_k,
            "passivo_nao_circulante": pnc_k,
            "patrimonio_liquido": pl_k,
            "passivo_total": (pc_k + pnc_k + pl_k) if (pc_k + pnc_k + pl_k) > 0 else (pc_k + pnc_k),
            "disponibilidades": disp_k
        }

        # 8.4 Totais de DRE para o ano_k
        rec_k = dre_matriz_por_ano[ano_k]["resumo_executivo"]["receita_bruta_anual"]
        lucro_k = dre_matriz_por_ano[ano_k]["resumo_executivo"]["lucro_liquido_anual"]
        totais_dre_por_ano[ano_k] = {
            "receita_bruta": rec_k,
            "lucro_liquido": lucro_k
        }

        # 8.5 Indicadores Financeiros para o ano_k com métricas reais
        resumo_k = dre_matriz_por_ano[ano_k].get("resumo_executivo", {})
        rec_liq_k = resumo_k.get("receita_liquida_anual", rec_k)
        l_bruto_k = resumo_k.get("resultado_bruto_anual", rec_liq_k)
        ebitda_k = lucro_k

        indicadores_por_ano[ano_k] = CalculadoraIndicesFinanceiros.calcular_todos_indices(
            ativo_circulante=ac_k,
            ativo_nao_circulante=anc_k,
            disponibilidades=disp_k,
            estoques=est_k,
            passivo_circulante=pc_k,
            passivo_nao_circulante=pnc_k,
            patrimonio_liquido=pl_k,
            receita_liquida=rec_liq_k,
            lucro_bruto=l_bruto_k,
            ebitda=ebitda_k,
            lucro_liquido=lucro_k
        )

    dre_matriz_empresa = dre_matriz_por_ano.get(ano_principal) or conglutinador_jev.conglutinar_dados_na_matriz(
        itens_dre + contas_processadas,
        trimestres_permitidos=list(trim_permitidos_set) if trimestres_permitidos else None
    )

    return {
        "arquivo": nome_arquivo,
        "formato": "Excel / Planilha",
        "tipo_documento": "DRE" if somente_dre else ("Balanço Patrimonial" if somente_balanco else "Balanço & DRE Completo"),
        "aba_sugerida": "dre" if somente_dre else "acionistas",
        "somente_dre": somente_dre,
        "total_linhas_lidas": len(contas_processadas) + len(itens_dre),
        "balanco_equilibrado": balanco_equilibrado,
        "diferenca_balanco": diferenca_balanco,
        "totais_balanco": totais_balanco_por_ano.get(ano_principal, totais_balanco),
        "totais_balanco_por_ano": totais_balanco_por_ano,
        "totais_dre": totais_dre_por_ano.get(ano_principal, totais_dre),
        "totais_dre_por_ano": totais_dre_por_ano,
        "indices_financeiros": indicadores_por_ano.get(ano_principal, indices_anual),
        "indicadores_por_ano": indicadores_por_ano,
        "indicadores_por_periodo": indicadores_por_periodo,
        "anos_disponiveis": anos_disponiveis,
        "ano_ativo": ano_principal,
        "trimestres_autorizados": list(trim_permitidos_set),
        "indicadores_por_ano": indicadores_por_ano,
        "parecer_gestao_jev": parecer_gestao_jev,
        "dre_matriz_empresa": dre_matriz_empresa,
        "dre_matriz_por_ano": dre_matriz_por_ano,
        "contas_detalhadas": contas_processadas,
        "itens_dre": itens_dre,
        "destaques_acionistas": destaques_acionistas,
        "motor_ia": {
            "icone": "⚡🧠",
            "nome": "TypeSafe JEV (System 1 Decision Engine)",
            "status": "Operacional - Reconhecimento Universal & Gestão Concluído"
        }
    }


