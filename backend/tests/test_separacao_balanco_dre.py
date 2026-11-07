"""
Teste automatizado para garantir que contas da DRE (Resultado) jamais
vazem para dentro do Balanço Patrimonial.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import io
from app.services.planilha_service import _classificar_linha_balanco_ou_dre, processar_demonstracoes_com_jev

def test_classificacao_linha_dre_vs_balanco():
    # Contas que devem ser estritamente DRE
    linhas_dre = [
        {"codigo": "310201000", "conta": "(-) Vendas Canceladas e devoluções"},
        {"codigo": "310203000", "conta": "(-) Impostos Incidentes sobre as vendas"},
        {"codigo": "", "conta": "ICMS sobre Vendas"},
        {"codigo": "", "conta": "PIS Faturamento"},
        {"codigo": "500000000", "conta": "(=) Lucro bruto"},
        {"codigo": "", "conta": "Salários e Ordenados"},
        {"codigo": "", "conta": "Gratificações"},
        {"codigo": "", "conta": "Férias"},
        {"codigo": "", "conta": "13º Salários"},
        {"codigo": "", "conta": "Rescisões"},
        {"codigo": "", "conta": "Hora Extra"},
        {"codigo": "", "conta": "DSR"},
        {"codigo": "", "conta": "Adicional Noturno"}
    ]

    for l in linhas_dre:
        assert _classificar_linha_balanco_ou_dre(l) == "DRE", f"A conta {l['conta']} deveria ser DRE!"

    # Contas que devem ser estritamente Balanço Patrimonial
    linhas_balanco = [
        {"codigo": "1.01.01.001", "conta": "Caixa Geral"},
        {"codigo": "1.01.02.001", "conta": "Banco Itaú"},
        {"codigo": "1.01.03.001", "conta": "Aplicações de Liquidez Imediata"},
        {"codigo": "1.01.04.001", "conta": "Clientes Diversos"},
        {"codigo": "2.01.01.001", "conta": "Fornecedores Nacionais"},
        {"codigo": "2.01.02.001", "conta": "Salários a Pagar"},
        {"codigo": "2.03.01.001", "conta": "Capital Social Subscrito"}
    ]

    for l in linhas_balanco:
        assert _classificar_linha_balanco_ou_dre(l) == "BALANCO", f"A conta {l['conta']} deveria ser BALANCO!"

def test_ingestao_planilha_mista_isola_dre_do_balanco():
    # Cria uma planilha com linhas misturadas de Balanço e DRE
    df = pd.DataFrame([
        {"Codigo": "1.01.01", "Conta": "Caixa e Bancos", "Saldo": 100000.0},
        {"Codigo": "2.01.01", "Conta": "Fornecedores", "Saldo": 50000.0},
        {"Codigo": "310201000", "Conta": "(-) Vendas Canceladas e devoluções", "Saldo": 15000.0},
        {"Codigo": "310203000", "Conta": "(-) Impostos Incidentes sobre as vendas", "Saldo": 8000.0},
        {"Codigo": "500000000", "Conta": "(=) Lucro bruto", "Saldo": 77000.0},
        {"Codigo": "410101", "Conta": "Salários e Ordenados", "Saldo": 25000.0}
    ])

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Balancete", index=False)
    conteudo = buf.getvalue()

    resultado = processar_demonstracoes_com_jev(conteudo, "balancete_misto.xlsx", ano_destino="2026")

    contas_balanco = resultado.get("contas_detalhadas", [])
    nomes_balanco = [c["conta"].lower() for c in contas_balanco]

    # Assegura que nenhuma conta de DRE entrou na lista de Balanço
    assert not any("vendas canceladas" in n for n in nomes_balanco)
    assert not any("lucro bruto" in n for n in nomes_balanco)
    assert not any("salários e ordenados" in n for n in nomes_balanco)

    # Assegura que as contas de Balanço estão presentes
    assert any("caixa e bancos" in n for n in nomes_balanco)
    assert any("fornecedores" in n for n in nomes_balanco)
