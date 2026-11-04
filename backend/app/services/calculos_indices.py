from typing import Dict, Any

class CalculadoraIndicesFinanceiros:
    @staticmethod
    def calcular_todos_indices(
        ativo_circulante: float,
        ativo_nao_circulante: float,
        disponibilidades: float,
        estoques: float,
        passivo_circulante: float,
        passivo_nao_circulante: float,
        patrimonio_liquido: float,
        receita_liquida: float,
        lucro_bruto: float,
        ebitda: float,
        lucro_liquido: float,
        ebit: float = 0.0,
        despesas_financeiras: float = 0.0,
        realizavel_longo_prazo: float = 0.0
    ) -> Dict[str, Any]:
        ativo_total = ativo_circulante + ativo_nao_circulante
        passivo_exigivel = passivo_circulante + passivo_nao_circulante

        # 1. Indicadores de Liquidez e Capital de Giro
        liquidez_corrente = round(ativo_circulante / passivo_circulante, 2) if passivo_circulante > 0 else 0.0
        liquidez_seca = round((ativo_circulante - estoques) / passivo_circulante, 2) if passivo_circulante > 0 else 0.0
        liquidez_imediata = round(disponibilidades / passivo_circulante, 2) if passivo_circulante > 0 else 0.0
        
        # Liquidez Geral conforme NBC TG / Normas Contábeis Oficiais: (Ativo Circulante + RLP) / Passivo Exigível
        rlp_efetivo = realizavel_longo_prazo if realizavel_longo_prazo > 0 else 0.0
        liquidez_geral = round((ativo_circulante + rlp_efetivo) / passivo_exigivel, 2) if passivo_exigivel > 0 else 0.0
        
        # Capital Circulante Líquido (Folga Financeira)
        ccl = round(ativo_circulante - passivo_circulante, 2)

        # 2. Indicadores de Rentabilidade e Margens
        ebit_calculado = ebit if ebit != 0.0 else ebitda
        margem_bruta = round((lucro_bruto / receita_liquida) * 100, 2) if receita_liquida > 0 else 0.0
        margem_operacional = round((ebit_calculado / receita_liquida) * 100, 2) if receita_liquida > 0 else 0.0
        margem_ebitda = round((ebitda / receita_liquida) * 100, 2) if receita_liquida > 0 else 0.0
        margem_liquida = round((lucro_liquido / receita_liquida) * 100, 2) if receita_liquida > 0 else 0.0
        roe = round((lucro_liquido / patrimonio_liquido) * 100, 2) if patrimonio_liquido != 0 else 0.0
        roa = round((lucro_liquido / ativo_total) * 100, 2) if ativo_total > 0 else 0.0
        
        # Retorno sobre Capital Investido (ROIC: NOPAT aproximado / Capital Total Empregado)
        capital_investido = patrimonio_liquido + passivo_nao_circulante
        roic = round((lucro_liquido / capital_investido) * 100, 2) if capital_investido > 0 else 0.0

        # 3. Indicadores de Eficiência e Operação
        giro_ativo = round(receita_liquida / ativo_total, 2) if ativo_total > 0 else 0.0

        # 4. Indicadores de Endividamento, Cobertura e Solvência
        endividamento_geral = round((passivo_exigivel / ativo_total) * 100, 2) if ativo_total > 0 else 0.0
        composicao_endividamento = round((passivo_circulante / passivo_exigivel) * 100, 2) if passivo_exigivel > 0 else 0.0
        imobilizacao_pl = round((ativo_nao_circulante / patrimonio_liquido) * 100, 2) if patrimonio_liquido != 0 else 0.0
        
        # Solvência Geral
        solvencia_geral = round(ativo_total / passivo_exigivel, 2) if passivo_exigivel > 0 else 0.0

        # Cobertura de Juros
        desp_fin_positiva = abs(despesas_financeiras)
        cobertura_juros = round(ebit_calculado / desp_fin_positiva, 2) if desp_fin_positiva > 0 else (99.0 if ebit_calculado > 0 else 0.0)

        return {
            'estrutura': {
                'ativo_total': ativo_total,
                'passivo_exigivel': passivo_exigivel,
                'patrimonio_liquido': patrimonio_liquido,
                'ccl': ccl
            },
            'liquidez': {
                'liquidez_corrente': liquidez_corrente,
                'liquidez_seca': liquidez_seca,
                'liquidez_imediata': liquidez_imediata,
                'liquidez_geral': liquidez_geral,
                'ccl': ccl
            },
            'rentabilidade': {
                'margem_bruta_pct': margem_bruta,
                'margem_operacional_pct': margem_operacional,
                'margem_ebitda_pct': margem_ebitda,
                'margem_liquida_pct': margem_liquida,
                'roe_pct': roe,
                'roa_pct': roa,
                'roic_pct': roic
            },
            'eficiencia': {
                'giro_ativo': giro_ativo
            },
            'endividamento': {
                'endividamento_geral_pct': endividamento_geral,
                'composicao_divida_curto_prazo_pct': composicao_endividamento,
                'imobilizacao_pl_pct': imobilizacao_pl,
                'solvencia_geral': solvencia_geral,
                'cobertura_juros': cobertura_juros
            }
        }
