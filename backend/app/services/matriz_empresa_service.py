import os
import re
import json
import uuid
import threading
from typing import Dict, Any, List, Optional

# Estrutura base da Matriz da Empresa extraída da especificação
ESTRUTURA_MATRIZ_PADRAO = [
    {
        "id": "rec_bruta",
        "codigo": "1",
        "conta": "RECEITA OPERACIONAL BRUTA",
        "tipo": "totalizador",
        "marcador": "",
        "estilo": "destaque_laranja",
        "sinonimos": ["receita operacional bruta", "receita bruta", "faturamento bruto"],
        "filhos": [
            {
                "id": "vendas_mercadorias",
                "codigo": "1.01",
                "conta": "VENDAS DE MERCADORIAS",
                "tipo": "analitica",
                "marcador": "",
                "sinonimos": ["vendas de mercadoria", "venda de mercadorias", "vendas mercadorias", "faturamento de vendas", "venda de produtos", "receita de vendas", "receitas de vendas", "receita bruta de vendas", "receitas bruta de vendas", "receitas brutas de vendas", "receitas bruta"]
            }
        ]
    },
    {
        "id": "deducoes_rec",
        "codigo": "2",
        "conta": "(-) DEDUÇÕES DA RECEITA BRUTA",
        "tipo": "grupo",
        "marcador": "(-)",
        "estilo": "destaque_amarelo",
        "sinonimos": ["deducoes da receita bruta", "deducoes da receita", "tributos sobre vendas", "impostos sobre vendas"],
        "filhos": [
            {
                "id": "vendas_canceladas",
                "codigo": "2.01",
                "conta": "(-) Vendas Canceladas e Devoluções",
                "tipo": "analitica",
                "marcador": "(-)",
                "sinonimos": ["vendas canceladas e devolucoes", "vendas canceladas e devolucoes", "vendas canceladas", "devolucoes de vendas", "devolucao de mercadorias", "cancelamento de vendas", "abatimentos"]
            },
            {
                "id": "imposto_incidente",
                "codigo": "2.02",
                "conta": "(-) Imposto Incidente Sobre Vendas",
                "tipo": "analitica",
                "marcador": "(-)",
                "sinonimos": ["impostos incidentes sobre as vendas", "imposto incidente sobre as vendas", "imposto incidente sobre vendas", "impostos s/ vendas", "tributos s/ vendas"]
            },
            {
                "id": "icms_vendas",
                "codigo": "2.03",
                "conta": "(-) ICMS Sobre Vendas",
                "tipo": "analitica",
                "marcador": "(-)",
                "sinonimos": ["icms sobre vendas", "icms s/ vendas", "icms faturamento", "icms s/ faturamento", "icms"]
            },
            {
                "id": "pis_vendas",
                "codigo": "2.04",
                "conta": "(-) PIS Sobre Vendas",
                "tipo": "analitica",
                "marcador": "(-)",
                "sinonimos": ["pis sobre vendas", "pis s/ vendas", "pis faturamento", "pis s/ faturamento", "pis"]
            },
            {
                "id": "cofins_vendas",
                "codigo": "2.05",
                "conta": "(-) COFINS Sobre Vendas",
                "tipo": "analitica",
                "marcador": "(-)",
                "sinonimos": ["cofins sobre vendas", "cofins s/ vendas", "cofins faturamento", "cofins s/ faturamento", "cofins"]
            }
        ]
    },
    {
        "id": "rec_liquida",
        "codigo": "3",
        "conta": "(=) RECEITA OPERACIONAL LÍQUIDA",
        "tipo": "subtotal",
        "marcador": "(=)",
        "estilo": "destaque_verde_menta",
        "formula": "rec_bruta - deducoes_rec"
    },
    {
        "id": "cmv",
        "codigo": "4",
        "conta": "(-) CUSTO OPERACIONAL BRUTO (CMV)",
        "tipo": "grupo",
        "marcador": "(-)",
        "estilo": "destaque_verde",
        "sinonimos": ["custo operacional bruto", "cmv", "custo das mercadorias vendidas", "custo dos produtos vendidos", "cpv", "csv"],
        "filhos": [
            {
                "id": "custo_mercadoria",
                "codigo": "4.01",
                "conta": "(-) Custo de Mercadoria Vendida",
                "tipo": "analitica",
                "marcador": "(-)",
                "sinonimos": ["custo de mercadoria vendida", "custo mercadorias", "custo das mercadorias", "custo de vendas", "cmv"]
            }
        ]
    },
    {
        "id": "resultado_bruto",
        "codigo": "5",
        "conta": "(=) RESULTADO OPERACIONAL BRUTO",
        "tipo": "subtotal",
        "marcador": "(=)",
        "estilo": "destaque_amarelo",
        "formula": "rec_liquida - cmv"
    },
    {
        "id": "despesas_operacionais",
        "codigo": "6",
        "conta": "(-) DESPESAS OPERACIONAIS E ADMINIST.",
        "tipo": "super_grupo",
        "marcador": "(-)",
        "estilo": "destaque_cinza",
        "subgrupos": [
            {
                "id": "desp_pessoal",
                "codigo": "6.01",
                "conta": "(-) DESPESAS COM PESSOAL",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "salarios", "conta": "(-) Salários e Ordenados", "sinonimos": ["salarios e ordenados", "salario e ordenado", "salarios", "ordenados", "folha de pagamento", "vencimentos", "remuneracao", "pro labore"]},
                    {"id": "gratificacoes", "conta": "(-) Gratificações", "sinonimos": ["gratificacoes", "gratificacao", "bonificacao funcional"]},
                    {"id": "ferias", "conta": "(-) Férias", "sinonimos": ["ferias", "provisao de ferias", "ferias e 1/3", "1/3 de ferias"]},
                    {"id": "decimo_terceiro", "conta": "(-) 13º Salário", "sinonimos": ["13º salarios", "13o salarios", "13 salarios", "13º salario", "13o salario", "13 salario", "decimo terceiro", "provisao 13", "13º", "13o"]},
                    {"id": "rescisao", "conta": "(-) Rescisões", "sinonimos": ["rescisoes", "rescisao", "rescisao contratual", "verbas rescisorias", "rescisao de contrato"]},
                    {"id": "horas_extras", "conta": "(-) Horas Extras", "sinonimos": ["hora extra", "horas extras", "adicional hora extra", "horas extra"]},
                    {"id": "dsr", "conta": "(-) DSR", "sinonimos": ["dsr", "descanso semanal remunerado", "d.s.r."]},
                    {"id": "adicional_noturno", "conta": "(-) Adicional Noturno", "sinonimos": ["adicional noturno", "adicional de turno", "noturno"]},
                    {"id": "comissao", "conta": "(-) Comissão", "sinonimos": ["comissao", "comissoes", "comissoes s/ vendas"]},
                    {"id": "estagio", "conta": "(-) Estágio", "sinonimos": ["estagio", "bolsa estagio", "estagiarios", "bolsa de estagio"]},
                    {"id": "quebra_caixa", "conta": "(-) Quebra de Caixa", "sinonimos": ["quebra de caixa", "adicional quebra de caixa"]},
                    {"id": "quinquenio", "conta": "(-) Quinquênio", "sinonimos": ["quinquenio", "adicional por tempo de servico", "anuenio", "trienio"]},
                    {"id": "outras_pessoal", "conta": "(-) Outras Despesas com Pessoal", "sinonimos": ["falta de caixa", "outras despesas com pessoal", "despesas com pessoal diversas"]},
                    {"id": "insalubridade", "conta": "(-) Insalubridade", "sinonimos": ["insalubridade", "adicional de insalubridade"]},
                    {"id": "periculosidade", "conta": "(-) Periculosidade", "sinonimos": ["periculosidade", "adicional de periculosidade"]},
                    {"id": "aviso_previo", "conta": "(-) Aviso Prévio Indenizado", "sinonimos": ["aviso previo", "aviso previo indenizado", "rescisao aviso"]},
                    {"id": "premio_assiduidade", "conta": "(-) Prêmio Assiduidade", "sinonimos": ["premio assiduidade", "assiduidade", "premio"]},
                    {"id": "atestado_medico", "conta": "(-) Atestado Médico", "sinonimos": ["atestado medico", "atestados", "licenca medica"]}
                ]
            },
            {
                "id": "encargos_sociais",
                "codigo": "6.02",
                "conta": "(-) ENCARGOS SOCIAIS E TRABALHISTAS",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "inss", "conta": "(-) INSS", "sinonimos": ["inss", "inss patronal", "previdencia social"]},
                    {"id": "fgts", "conta": "(-) FGTS", "sinonimos": ["fgts", "fgts folha", "multa fgts"]},
                    {"id": "acoes_trabalhistas", "conta": "(-) Ações Trabalhistas", "sinonimos": ["acoes trabalhistas", "processos trabalhistas", "indenizacoes trabalhistas"]}
                ]
            },
            {
                "id": "beneficios",
                "codigo": "6.03",
                "conta": "(-) BENEFÍCIOS",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "vale_transporte", "conta": "(-) Vale Transporte", "sinonimos": ["vale transporte", "vt", "transporte funcionarios"]},
                    {"id": "assist_medica", "conta": "(-) Assistência Médica e Odontológica Convale", "sinonimos": ["assistencia medica", "plano de saude", "convale", "odontologico", "convenio medico"]},
                    {"id": "uniforme", "conta": "(-) Uniforme", "sinonimos": ["uniforme", "uniformes", "fardamento", "epi"]},
                    {"id": "treinamento", "conta": "(-) Cursos e Treinamentos", "sinonimos": ["cursos", "treinamento", "capacitacao", "treinamentos"]},
                    {"id": "auxilio_alimentacao", "conta": "(-) Auxílio Alimentação", "sinonimos": ["auxilio alimentacao", "vale refeicao", "vale alimentacao", "refeitorio", "refeicoes"]}
                ]
            },
            {
                "id": "material_manutencao",
                "codigo": "6.04",
                "conta": "(-) MATERIAL E MANUTENÇÃO",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "mat_escritorio", "conta": "(-) Material de Escritório", "sinonimos": ["material de escritorio", "papelaria", "impressos"]},
                    {"id": "mat_limpeza", "conta": "(-) Material de Limpeza", "sinonimos": ["material de limpeza", "produtos de limpeza", "higiene"]},
                    {"id": "mat_informatica", "conta": "(-) Material de Informática", "sinonimos": ["material de informatica", "toner", "perifericos"]},
                    {"id": "mat_uso_consumo", "conta": "(-) Material de Uso e Consumo", "sinonimos": ["material de uso e consumo", "uso e consumo", "consumo geral"]},
                    {"id": "mat_diverso", "conta": "(-) Material Diverso (Óleo)", "sinonimos": ["material diverso", "oleo", "lubrificantes"]},
                    {"id": "mat_uso_crucial", "conta": "(-) Material de Uso Crucial", "sinonimos": ["material de uso crucial", "insumos criticos"]},
                    {"id": "mat_embalagem", "conta": "(-) Material de Embalagem", "sinonimos": ["material de embalagem", "embalagens", "sacolas", "caixas de papelao"]},
                    {"id": "manut_equipamentos", "conta": "(-) Manutenção de Equipamentos", "sinonimos": ["manutencao de equipamentos", "manutencao maquinas", "reparos equipamentos"]},
                    {"id": "manut_informatica", "conta": "(-) Manutenção de Informática", "sinonimos": ["manutencao de informatica", "suporte ti", "reparos ti"]}
                ]
            },
            {
                "id": "desp_veiculos",
                "codigo": "6.05",
                "conta": "(-) DESPESAS COM VEÍCULOS",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "manut_veiculos", "conta": "(-) Manutenção de Veículos", "sinonimos": ["manutencao de veiculos", "oficina veiculos", "revisoes frota"]},
                    {"id": "combustivel", "conta": "(-) Combustível", "sinonimos": ["combustivel", "gasolina", "diesel", "etanol", "abastecimento"]}
                ]
            },
            {
                "id": "viagem_hospedagem",
                "codigo": "6.06",
                "conta": "(-) VIAGEM E HOSPEDAGEM",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "viagem_func", "conta": "(-) Funcionários", "sinonimos": ["viagem funcionarios", "passagens funcionarios", "diarias de viagem"]},
                    {"id": "viagem_terceiros", "conta": "(-) Terceiros", "sinonimos": ["viagem terceiros", "passagens terceiros"]},
                    {"id": "hospedagem", "conta": "(-) Hospedagem", "sinonimos": ["hospedagem", "hotel", "estadia"]}
                ]
            },
            {
                "id": "demais_administrativas",
                "codigo": "6.07",
                "conta": "(-) DEMAIS DESPESAS ADMINISTRATIVAS",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "energia", "conta": "(-) Energia", "sinonimos": ["energia", "energia eletrica", "luz", "cemig", "enel", "cpfl"]},
                    {"id": "telefonia", "conta": "(-) Telefonia", "sinonimos": ["telefonia", "telefone", "celular corporativo"]},
                    {"id": "agua_esgoto", "conta": "(-) Água e Esgoto", "sinonimos": ["agua e esgoto", "agua", "copasa", "sabesp", "saneamento"]},
                    {"id": "aluguel_cofre", "conta": "(-) Aluguel Cofre", "sinonimos": ["aluguel cofre", "cofre inteligente", "guarda valores"]},
                    {"id": "correios", "conta": "(-) Correios e Malote", "sinonimos": ["correios", "malote", "sedex", "fretes administrativos"]},
                    {"id": "internet", "conta": "(-) Internet", "sinonimos": ["internet", "link dedicado", "provedor internet"]},
                    {"id": "publicidade", "conta": "(-) Publicidade / Redes Sociais", "sinonimos": ["publicidade", "propaganda", "redes sociais", "marketing", "anuncios"]},
                    {"id": "lanches", "conta": "(-) Lanches e Refeições", "sinonimos": ["lanches e refeicoes", "lanches", "refeicoes diretoria"]},
                    {"id": "festas_motivacional", "conta": "(-) Festas Anuais e Motivacional", "sinonimos": ["festas anuais", "motivacional", "confraternizacao", "eventos internos"]},
                    {"id": "servicos_graficos", "conta": "(-) Serviços Gráficos", "sinonimos": ["servicos graficos", "grafica", "banners"]},
                    {"id": "seguro", "conta": "(-) Seguro", "sinonimos": ["seguro", "seguros predial", "seguro empresarial"]},
                    {"id": "licencas_software", "conta": "(-) Licenças/Software", "sinonimos": ["licencas de software", "software", "erp", "sistemas ti", "totvs", "sap"]},
                    {"id": "copa_cozinha", "conta": "(-) Copa e Cozinha", "sinonimos": ["copa e cozinha", "cafe", "itens de copa"]},
                    {"id": "farmacia", "conta": "(-) Farmácia", "sinonimos": ["farmacia", "medicamentos primeiros socorros"]},
                    {"id": "condominio", "conta": "(-) Condomínio RMC", "sinonimos": ["condominio", "condominio rmc", "taxa condominial"]},
                    {"id": "alvara", "conta": "(-) Alvará", "sinonimos": ["alvara", "taxa de alvara", "licenca funcionamento"]},
                    {"id": "custas_judiciais", "conta": "(-) Custas Judiciais", "sinonimos": ["custas judiciais", "emolumentos", "taxas judiciarias"]},
                    {"id": "depreciacao", "conta": "(-) Depreciação Acumulada", "sinonimos": ["depreciacao", "depreciacao do exercicio", "amortizacao"]},
                    {"id": "taxas_cartorio", "conta": "(-) Taxas Cartório", "sinonimos": ["taxas cartorio", "cartorio", "autenticacoes"]},
                    {"id": "campanhas_promocionais", "conta": "(-) Campanhas Promocionais", "sinonimos": ["campanhas promocionais", "promocoes", "encartes"]},
                    {"id": "mensalidade_rede", "conta": "(-) Mensalidade da Rede Brasil", "sinonimos": ["mensalidade da rede", "rede brasil", "associacao de rede", "taxa de rede"]},
                    {"id": "aluguel_predial", "conta": "(-) Despesas c/ Aluguel Predial", "sinonimos": ["aluguel predial", "aluguel de imovel", "locacao predial", "alugueis"]},
                    {"id": "outras_administrativas", "conta": "(-) Outras Despesas Administrativas", "sinonimos": ["outras despesas administrativas", "despesas diversas", "miudezas"]},
                    {"id": "fianca_compra", "conta": "(-) Fiança - Compra Frango GP", "sinonimos": ["fianca", "fianca bancaria", "garantia compra"]},
                    {"id": "gratificacao_metas", "conta": "(-) Gratificação de Metas", "sinonimos": ["gratificacao de metas", "plr", "bonus metas"]}
                ]
            },
            {
                "id": "perdas_credito",
                "codigo": "6.08",
                "conta": "(-) PERDAS DE CRÉDITOS A RECEBER",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "pdd", "conta": "(-) Provisão para Devedores Duvidosos / Perdas", "sinonimos": ["perdas de creditos", "inadimplencia", "pdd", "perdas clientes", "perdas de creditos a receber"]}
                ]
            },
            {
                "id": "impostos_taxas",
                "codigo": "6.09",
                "conta": "(-) IMPOSTOS E TAXAS",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "iptu", "conta": "(-) IPTU", "sinonimos": ["iptu", "imposto predial e territorial"]},
                    {"id": "multas_mora_dedutivel", "conta": "(-) Multas de Mora Dedutível", "sinonimos": ["multas de mora dedutivel", "multa mora"]},
                    {"id": "juros_mora_dedutivel", "conta": "(-) Juros de Mora Dedutível", "sinonimos": ["juros de mora dedutivel", "juros mora"]},
                    {"id": "taxas_federais", "conta": "(-) Taxas Federais", "sinonimos": ["taxas federais", "taxa federal"]},
                    {"id": "taxas_estaduais", "conta": "(-) Taxas Estaduais", "sinonimos": ["taxas estaduais", "taxa estadual"]},
                    {"id": "taxas_municipais", "conta": "(-) Taxas Municipais", "sinonimos": ["taxas municipais", "taxa municipal", "tllf"]},
                    {"id": "issqn", "conta": "(-) ISSQN", "sinonimos": ["issqn", "iss", "imposto sobre servicos"]},
                    {"id": "siscomex", "conta": "(-) Siscomex", "sinonimos": ["siscomex", "taxa siscomex"]},
                    {"id": "icms_nao_recuperavel", "conta": "(-) ICMS não Recuperável", "sinonimos": ["icms nao recuperavel", "diferencial de aliquota icms"]}
                ]
            },
            {
                "id": "servicos_pj_pf",
                "codigo": "6.10",
                "conta": "(-) SERVIÇOS PRESTADOS PJ/PF",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "serv_pf", "conta": "(-) Serviço Pessoa Física", "sinonimos": ["servico pessoa fisica", "autonomos", "rpa"]},
                    {"id": "honorarios_adv", "conta": "(-) Honorários Advogatícios", "sinonimos": ["honorarios advocaticios", "advogados", "juridico"]},
                    {"id": "honorarios_contabeis", "conta": "(-) Honorários Contábeis", "sinonimos": ["honorarios contabeis", "contabilidade", "auditoria"]},
                    {"id": "consultoria_ti", "conta": "(-) Consultoria de Informática", "sinonimos": ["consultoria de informatica", "consultoria ti", "desenvolvimento"]},
                    {"id": "vigilancia_seguranca", "conta": "(-) Serviço de Vigilância e Segurança", "sinonimos": ["vigilancia", "seguranca patrimonial", "monitoramento"]},
                    {"id": "serv_diversos_pj", "conta": "(-) Serviço Diversos Pessoa Jurídica", "sinonimos": ["servicos diversos pj", "servicos de terceiros pj", "terceirizados"]},
                    {"id": "taxa_energia_renovavel", "conta": "(-) Taxa Serviço Energia Renovável", "sinonimos": ["taxa servico energia renovavel", "energia solar", "gestao energetica"]}
                ]
            },
            {
                "id": "resultado_financeiro_op",
                "codigo": "6.11",
                "conta": "(-/+) RESULTADO FINANCEIRO LÍQUIDO",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "juros_multas_pagos", "conta": "(-) Juros/Multas Pagos ou Incorridos", "sinonimos": ["juros pagos", "multas pagas", "juros bancarios"]},
                    {"id": "descontos_concedidos", "conta": "(-) Descontos Concedidos", "sinonimos": ["descontos concedidos", "descontos comerciais"]},
                    {"id": "tarifas_bancarias", "conta": "(-) Tarifas Bancárias", "sinonimos": ["tarifas bancarias", "despesas bancarias", "manutencao de conta"]},
                    {"id": "iof", "conta": "(-) IOF - S/Operações Financeiras", "sinonimos": ["iof", "imposto operacoes financeiras"]},
                    {"id": "tarifas_boletos", "conta": "(-) Tarifas Cobradas s/ Boletos", "sinonimos": ["tarifas cobradas s/ boletos", "taxa boleto", "emissao boletos"]},
                    {"id": "tarifas_cartao", "conta": "(-) Tarifas Cobradas s/ Cartão de Crédito", "sinonimos": ["tarifas cobradas s/ cartao", "taxa cartao", "adquirencia", "cielo", "rede", "stone"]},
                    {"id": "encargos_financeiros", "conta": "(-) Encargos Financeiros", "sinonimos": ["encargos financeiros", "juros de emprestimos"]},
                    {"id": "tarifa_cofre", "conta": "(-) Tarifa Cofre", "sinonimos": ["tarifa cofre", "manutencao cofre"]}
                ]
            },
            {
                "id": "despesas_indedutiveis",
                "codigo": "6.12",
                "conta": "(-) DESPESAS INDEDUTÍVEIS",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "juros_indedutiveis", "conta": "(-) Juros e Multas s/ Indedutíveis", "sinonimos": ["juros e multas indedutiveis", "multas punitivas"]},
                    {"id": "auto_infracao", "conta": "(-) Auto de Infração", "sinonimos": ["auto de infracao", "autuacoes fiscais"]},
                    {"id": "parcelamento_tributo", "conta": "(-) Parcelamento Tributo Estadual", "sinonimos": ["parcelamento tributo estadual", "refis", "parcelamento fiscal"]}
                ]
            }
        ]
    },
    {
        "id": "lucro_operacional_liq",
        "codigo": "7",
        "conta": "(=) LUCRO OPERACIONAL LÍQUIDO",
        "tipo": "subtotal",
        "marcador": "(=)",
        "estilo": "destaque_amarelo",
        "formula": "resultado_bruto - despesas_operacionais"
    },
    {
        "id": "resultado_nao_operacional",
        "codigo": "8",
        "conta": "(-/+) RESULTADO NÃO OPERACIONAL",
        "tipo": "super_grupo",
        "marcador": "(-/+)",
        "estilo": "destaque_cinza",
        "subgrupos": [
            {
                "id": "receitas_financeiras_nao_op",
                "codigo": "8.01",
                "conta": "(+) RECEITAS FINANCEIRAS",
                "tipo": "grupo",
                "marcador": "(+)",
                "filhos": [
                    {"id": "juros_selic_impostos", "conta": "(+) Juros Selic s/ Impostos a Recuperar", "sinonimos": ["juros selic s/ impostos a recuperar", "selic creditos tributarios"]},
                    {"id": "correcao_monetaria", "conta": "(+) Correção Monetária", "sinonimos": ["correcao monetaria", "atualizacao monetaria"]},
                    {"id": "descontos_obtidos", "conta": "(+) Descontos Obtidos", "sinonimos": ["descontos obtidos", "descontos financeiros obtidos"]},
                    {"id": "juros_recebidos", "conta": "(+) Juros Recebidos ou Auferidos", "sinonimos": ["juros recebidos", "juros ativos", "juros auferidos"]},
                    {"id": "rendimento_aplicacao", "conta": "(+) Rendimento de Aplicação Financeira", "sinonimos": ["rendimento de aplicacao financeira", "rendimentos cdb", "rendimento aplicacao"]}
                ]
            },
            {
                "id": "despesas_financeiras_nao_op",
                "codigo": "8.02",
                "conta": "(-) DESPESAS FINANCEIRAS",
                "tipo": "grupo",
                "marcador": "(-)",
                "filhos": [
                    {"id": "despesas_juros_despesas", "conta": "(-) Despesas Juros/Despesas", "sinonimos": ["despesas juros", "juros passivos nao operacionais"]}
                ]
            },
            {
                "id": "outras_receitas_nao_op",
                "codigo": "8.03",
                "conta": "(+) OUTRAS RECEITAS NÃO OPERACIONAIS",
                "tipo": "grupo",
                "marcador": "(+)",
                "estilo": "destaque_verde_menta",
                "filhos": [
                    {"id": "compensacoes_rf", "conta": "(+) Compensações de Processos - Transações RF", "sinonimos": ["compensacoes de processos", "transacoes rf", "receita federal transacao"]},
                    {"id": "bonificacoes_fornec", "conta": "(+) Bonificações Recebidas Fornecedores", "sinonimos": ["bonificacoes recebidas", "bonificacoes fornecedores", "bonificacao em mercadorias"]},
                    {"id": "brindes_fornec", "conta": "(+) Brindes Fornecedor", "sinonimos": ["brindes fornecedor", "brindes"]},
                    {"id": "sobra_caixa", "conta": "(+) Sobra de Caixa", "sinonimos": ["sobra de caixa", "sobras de caixa"]},
                    {"id": "acordos_promocionais", "conta": "(+) Acordos Promocionais", "sinonimos": ["acordos promocionais", "verba de cooperacao", "sell in"]},
                    {"id": "outras_rec_nao_op", "conta": "(+) Outras Receitas", "sinonimos": ["outras receitas", "ganho de capital", "venda ativo imobilizado"]},
                    {"id": "recuperacao_creditos", "conta": "(+) Recuperação de Créditos", "sinonimos": ["recuperacao de creditos", "recuperacao de despesas", "creditos recuperados"]},
                    {"id": "recarga_celulares", "conta": "(+) Intermediação - Recarga de Celulares", "sinonimos": ["intermediacao recarga de celulares", "recarga celular", "comissao recarga"]},
                    {"id": "verba_incentivos", "conta": "(+) Verba Recebidas Comp./Incentivos", "sinonimos": ["verba recebidas comp", "incentivos fornecedores", "verba trade"]},
                    {"id": "aluguel_loja", "conta": "(+) Aluguel Espaço - Loja", "sinonimos": ["aluguel espaco loja", "locacao espaco", "sublocacao"]}
                ]
            }
        ]
    },
    {
        "id": "resultado_antes_tributos",
        "codigo": "9",
        "conta": "(=) RESULTADO OPERACIONAL ANTES IRPJ/CSLL",
        "tipo": "subtotal",
        "marcador": "(=)",
        "estilo": "destaque_amarelo",
        "formula": "lucro_operacional_liq + resultado_nao_operacional"
    },
    {
        "id": "provisao_tributos",
        "codigo": "10",
        "conta": "(-) PROVISÃO IRPJ/CSLL",
        "tipo": "grupo",
        "marcador": "(-)",
        "estilo": "destaque_verde_menta",
        "filhos": [
            {"id": "prov_irpj", "codigo": "10.01", "conta": "(-) Provisão de IRPJ", "sinonimos": ["provisao de irpj", "irpj", "imposto de renda pj"]},
            {"id": "prov_csll", "codigo": "10.02", "conta": "(-) Provisão de CSLL", "sinonimos": ["provisao de csll", "csll", "contribuicao social s/ lucro"]}
        ]
    },
    {
        "id": "resultado_liquido_exercicio",
        "codigo": "11",
        "conta": "(=) RESULTADO LÍQUIDO DO EXERCÍCIO",
        "tipo": "total_final",
        "marcador": "(=)",
        "estilo": "destaque_ouro_neon",
        "formula": "resultado_antes_tributos - provisao_tributos"
    }
]

def _normalizar(texto: str) -> str:
    s = str(texto or '').lower().strip()
    s = s.replace('ç', 'c').replace('ã', 'a').replace('á', 'a').replace('à', 'a').replace('é', 'e').replace('ê', 'e')
    s = s.replace('í', 'i').replace('ó', 'o').replace('ô', 'o').replace('õ', 'o').replace('ú', 'u')
    s = re.sub(r'[\(\)\-\=\+\.\,\/]', ' ', s)
    return ' '.join(s.split())

import json
import os

class ConglutinadorJevService:
    """
    Motor Especializado de Conglutinação Semântica e Consolidação da DRE
    conforme a Matriz Corporativa da Empresa.
    Permite ensino ativo de novas particularidades e De-Para de contas.
    """

    def __init__(self):
        self.matriz_padrao = ESTRUTURA_MATRIZ_PADRAO
        self.regras_depara_path = os.path.join(os.path.dirname(__file__), "..", "data", "regras_depara.json")
        self._lock = threading.RLock()
        self.regras_personalizadas = self._carregar_regras_personalizadas()

    def _carregar_regras_personalizadas(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.regras_depara_path):
                with open(self.regras_depara_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _salvar_regras_personalizadas(self):
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.regras_depara_path), exist_ok=True)
                with open(self.regras_depara_path, "w", encoding="utf-8") as f:
                    json.dump(self.regras_personalizadas, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def listar_regras_depara(self) -> List[Dict[str, Any]]:
        return self.regras_personalizadas

    def adicionar_regra_depara(self, termo_origem: str, conta_matriz_id: str, conta_matriz_nome: str, observacao: str = "") -> Dict[str, Any]:
        """
        Cadastra uma nova particularidade de conta no motor semântico JEV.
        """
        termo_limpo = termo_origem.strip()
        nova_regra = {
            "id": f"regra_{uuid.uuid4().hex[:8]}",
            "termo_origem": termo_limpo,
            "termo_normalizado": _normalizar(termo_limpo),
            "conta_matriz_id": conta_matriz_id,
            "conta_matriz_nome": conta_matriz_nome,
            "observacao": observacao or "Particularidade cadastrada pelo usuário"
        }
        with self._lock:
            self.regras_personalizadas.append(nova_regra)
            self._salvar_regras_personalizadas()
        return nova_regra

    def remover_regra_depara(self, regra_id: str) -> bool:
        with self._lock:
            tam_inicial = len(self.regras_personalizadas)
            self.regras_personalizadas = [r for r in self.regras_personalizadas if r.get("id") != regra_id]
            if len(self.regras_personalizadas) < tam_inicial:
                self._salvar_regras_personalizadas()
                return True
        return False

    def conglutinar_dados_na_matriz(self, itens_contabeis: List[Dict[str, Any]], trimestres_permitidos: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Mapeia e conglutina qualquer lista de contas/balancete na estrutura exata da empresa.
        Calcula subtotais, análises verticais e tendências respeitando estritamente os trimestres autorizados.
        """
        trim_permitidos_set = set(trimestres_permitidos) if trimestres_permitidos else None

        # 1. Mapa de acumuladores para cada conta da matriz
        valores_por_id: Dict[str, Dict[str, float]] = {}

        def _inicializar_acumulador(node_id: str):
            if node_id not in valores_por_id:
                valores_por_id[node_id] = {"1T": 0.0, "2T": 0.0, "3T": 0.0, "4T": 0.0, "total": 0.0}

        # Inicializa todos os nós
        for item_pai in self.matriz_padrao:
            _inicializar_acumulador(item_pai["id"])
            if "filhos" in item_pai:
                for f in item_pai["filhos"]:
                    _inicializar_acumulador(f["id"])
            if "subgrupos" in item_pai:
                for sg in item_pai["subgrupos"]:
                    _inicializar_acumulador(sg["id"])
                    if "filhos" in sg:
                        for f in sg["filhos"]:
                            _inicializar_acumulador(f["id"])

        # Identificação prévia se a lista de contas importadas contém detalhamento analítico
        todas_desc = [_normalizar(c.get("conta", "")) for c in itens_contabeis]
        todos_codigos = [str(c.get("codigo", "")).strip().rstrip(".") for c in itens_contabeis if str(c.get("codigo", "")).strip()]

        tem_detalhe_impostos = any(any(k in d for k in ["icms", "pis", "cofins"]) for d in todas_desc)
        tem_detalhe_pessoal = sum(1 for d in todas_desc if any(k in d for k in ["salarios", "ferias", "13", "gratificac", "rescis", "hora extra", "dsr", "estagio", "quinquenio"])) >= 2

        # Verifica para cada grupo/subgrupo da matriz se existem contas analíticas filhas presentes na planilha
        grupos_com_filhas_presentes = set()
        nomes_exatos_grupos_pais = {}

        def _registrar_grupo_e_checar_filhas(node_grupo: Dict[str, Any]):
            g_id = node_grupo["id"]
            g_nome_norm = _normalizar(node_grupo["conta"])
            nomes_exatos_grupos_pais[g_nome_norm] = g_id
            for sin_g in node_grupo.get("sinonimos", []):
                nomes_exatos_grupos_pais[_normalizar(sin_g)] = g_id

            filhos_lista = node_grupo.get("filhos", [])
            # Conta quantas contas da planilha batem especificamente nas filhas (e não apenas no nome do grupo pai)
            matches_filhas = 0
            for f in filhos_lista:
                f_nome_norm = _normalizar(f["conta"])
                f_sins = [_normalizar(s) for s in f.get("sinonimos", []) if _normalizar(s) != g_nome_norm]
                for d in todas_desc:
                    if d == g_nome_norm:
                        continue
                    if d == f_nome_norm or any(s and s in d for s in f_sins):
                        matches_filhas += 1
                        break
            if matches_filhas >= 1:
                grupos_com_filhas_presentes.add(g_id)

        for item_pai in self.matriz_padrao:
            if "filhos" in item_pai:
                _registrar_grupo_e_checar_filhas(item_pai)
            if "subgrupos" in item_pai:
                nomes_exatos_grupos_pais[_normalizar(item_pai["conta"])] = item_pai["id"]
                for sg in item_pai["subgrupos"]:
                    _registrar_grupo_e_checar_filhas(sg)

        def _eh_codigo_pai_sintetico(cod_atual: str) -> bool:
            if not cod_atual:
                return False
            c_limpo = cod_atual.strip().rstrip(".")
            if not c_limpo:
                return False
            for outro in todos_codigos:
                if outro != c_limpo and outro.startswith(c_limpo + "."):
                    return True
            return False

        def _eh_subtotal_calculado(desc: str, cod: str = "") -> bool:
            if _eh_codigo_pai_sintetico(cod):
                return True
            d_norm = _normalizar(desc)
            if desc.strip().startswith("(=)") or desc.strip().startswith("( = )") or desc.strip().startswith("(= )") or desc.strip().startswith("( ="):
                return True
            termos_subtotais = [
                "receita liquida", "receita operacional liquida",
                "lucro bruto", "resultado operacional bruto", "resultado bruto",
                "lucro operacional", "lucro operacional liquido", "resultado operacional antes",
                "resultado liquido do exercicio", "lucro liquido", "resultado liquido",
                "deducao da receita bruta", "deducoes da receita bruta",
                "despesas operacionais", "despesas operacionais e administ",
                "resultado nao operacional", "encargos sociais e trabalhistas",
                "material e manutencao", "demais despesas administrativas",
                "servicos prestados pj pf", "resultado financeiro liquido",
                "despesas indedutiveis", "receitas financeiras", "despesas financeiras"
            ]
            for t in termos_subtotais:
                if d_norm == t or d_norm == f"total {t}" or d_norm == f"total de {t}" or d_norm == f"total da {t}":
                    return True
            # Se a descrição for exatamente o título de um grupo que já possui contas analíticas filhas na planilha,
            # ignora a linha sintética do grupo para jamais duplicar valores!
            if d_norm in nomes_exatos_grupos_pais:
                g_id = nomes_exatos_grupos_pais[d_norm]
                if g_id in grupos_com_filhas_presentes:
                    return True
            return False

        # 2. Varre as contas importadas e distribui por semântica JEV
        for conta_importada in itens_contabeis:
            desc_original = conta_importada.get("conta", "").strip()
            cod_original = str(conta_importada.get("codigo", "")).strip()
            desc_sem_cod_norm = _normalizar(desc_original)
            nome_norm = _normalizar(desc_original + " " + cod_original)

            # Se for uma linha sintética de subtotal ou grupo pai já detalhado na DRE, pula a conglutinação analítica
            if _eh_subtotal_calculado(desc_original, cod_original):
                continue

            # Se for a conta agregadora "Impostos Incidentes" e já temos detalhe de ICMS/PIS/COFINS, pula para não duplicar
            if tem_detalhe_impostos and any(w in _normalizar(desc_original) for w in ["impostos incidentes sobre", "imposto incidente sobre as vendas", "impostos incidentes"]):
                continue

            # Se for a conta agregadora "Despesas com Pessoal" e já temos detalhe de salários/férias, pula para não duplicar
            if tem_detalhe_pessoal and _normalizar(desc_original) in ["despesas com pessoal", "despesa com pessoal"]:
                continue

            s_atual = abs(conta_importada.get("saldo_atual", 0.0))
            s_trim = conta_importada.get("saldos_trimestrais", {})

            # Extração dos valores reais de cada trimestre
            v_1t = abs(s_trim.get("1T", 0.0) or 0.0)
            v_2t = abs(s_trim.get("2T", 0.0) or 0.0)
            v_3t = abs(s_trim.get("3T", 0.0) or 0.0)
            v_4t = abs(s_trim.get("4T", 0.0) or 0.0)

            # Se houver restrição de trimestres permitidos, zera os não autorizados
            if trim_permitidos_set is not None:
                if "1T" not in trim_permitidos_set: v_1t = 0.0
                if "2T" not in trim_permitidos_set: v_2t = 0.0
                if "3T" not in trim_permitidos_set: v_3t = 0.0
                if "4T" not in trim_permitidos_set: v_4t = 0.0

            soma_trimestres = v_1t + v_2t + v_3t + v_4t
            if soma_trimestres > 0:
                v_total = soma_trimestres
            elif trim_permitidos_set is not None:
                v_total = 0.0
            else:
                v_total = abs(s_atual)

            # 2.1 Verifica primeiro as regras personalizadas / Plano de Contas (Matriz & Filiais)
            encontrado = False
            for regra in self.regras_personalizadas:
                t_norm = regra.get("termo_normalizado", "")
                cod_regra = str(regra.get("codigo_origem", "")).strip()
                c_id = regra.get("conta_matriz_id", "")
                if c_id not in valores_por_id:
                    continue
                match_cod = bool(cod_regra and cod_original and cod_regra == cod_original)
                match_termo = bool(t_norm and (t_norm == desc_sem_cod_norm or t_norm in nome_norm or desc_sem_cod_norm in t_norm))
                if match_cod or match_termo:
                    valores_por_id[c_id]["1T"] += v_1t
                    valores_por_id[c_id]["2T"] += v_2t
                    valores_por_id[c_id]["3T"] += v_3t
                    valores_por_id[c_id]["4T"] += v_4t
                    valores_por_id[c_id]["total"] += v_total
                    encontrado = True
                    break

            if encontrado:
                continue

            # 2.2 Procura melhor correspondência semântica na matriz padrão (priorizando igualdade exata)
            candidatos = []
            for item_pai in self.matriz_padrao:
                if "filhos" in item_pai:
                    for f in item_pai["filhos"]:
                        sinonimos = [_normalizar(s) for s in f.get("sinonimos", [])]
                        conta_f_norm = _normalizar(f["conta"])
                        for sin in [conta_f_norm] + sinonimos:
                            if not sin:
                                continue
                            if desc_sem_cod_norm == sin or nome_norm == sin:
                                candidatos.append((1000 + len(sin), f["id"]))
                            elif sin in nome_norm:
                                candidatos.append((len(sin), f["id"]))
                if "subgrupos" in item_pai:
                    for sg in item_pai["subgrupos"]:
                        if "filhos" in sg:
                            for f in sg["filhos"]:
                                sinonimos = [_normalizar(s) for s in f.get("sinonimos", [])]
                                conta_f_norm = _normalizar(f["conta"])
                                for sin in [conta_f_norm] + sinonimos:
                                    if not sin:
                                        continue
                                    if desc_sem_cod_norm == sin or nome_norm == sin:
                                        candidatos.append((1000 + len(sin), f["id"]))
                                    elif sin in nome_norm:
                                        candidatos.append((len(sin), f["id"]))

            # Tratamento especial de alta precisão para termos clássicos
            if any(k in nome_norm for k in ["13 ", "13o", "13º", "decimo terceiro"]):
                melhor_id = "decimo_terceiro"
            elif candidatos:
                candidatos.sort(key=lambda x: x[0], reverse=True)
                melhor_id = candidatos[0][1]
            else:
                melhor_id = None

            if melhor_id and melhor_id in valores_por_id:
                valores_por_id[melhor_id]["1T"] += v_1t
                valores_por_id[melhor_id]["2T"] += v_2t
                valores_por_id[melhor_id]["3T"] += v_3t
                valores_por_id[melhor_id]["4T"] += v_4t
                valores_por_id[melhor_id]["total"] += v_total

        # 3. Conglutinação Hierárquica e Consolidação dos Subtotais
        # Soma os filhos nos grupos pais
        for item_pai in self.matriz_padrao:
            if "filhos" in item_pai:
                for per in ["1T", "2T", "3T", "4T", "total"]:
                    valores_por_id[item_pai["id"]][per] = sum(valores_por_id[f["id"]][per] for f in item_pai["filhos"])
            elif "subgrupos" in item_pai:
                for sg in item_pai["subgrupos"]:
                    if "filhos" in sg:
                        for per in ["1T", "2T", "3T", "4T", "total"]:
                            valores_por_id[sg["id"]][per] = sum(valores_por_id[f["id"]][per] for f in sg["filhos"])
                for per in ["1T", "2T", "3T", "4T", "total"]:
                    valores_por_id[item_pai["id"]][per] = sum(valores_por_id[sg["id"]][per] for sg in item_pai["subgrupos"])

        # Subtotais matemáticos
        for per in ["1T", "2T", "3T", "4T", "total"]:
            # Receita Líquida = Receita Bruta - Deduções
            valores_por_id["rec_liquida"][per] = valores_por_id["rec_bruta"][per] - valores_por_id["deducoes_rec"][per]
            # Resultado Bruto = Receita Líquida - CMV
            valores_por_id["resultado_bruto"][per] = valores_por_id["rec_liquida"][per] - valores_por_id["cmv"][per]
            # Lucro Operacional Líquido = Resultado Bruto - Despesas Operacionais
            valores_por_id["lucro_operacional_liq"][per] = valores_por_id["resultado_bruto"][per] - valores_por_id["despesas_operacionais"][per]
            # Resultado Antes Tributos = Lucro Op Liq + Não Operacional
            rec_nao_op = valores_por_id["receitas_financeiras_nao_op"][per] + valores_por_id["outras_receitas_nao_op"][per]
            desp_nao_op = valores_por_id["despesas_financeiras_nao_op"][per]
            valores_por_id["resultado_nao_operacional"][per] = rec_nao_op - desp_nao_op
            valores_por_id["resultado_antes_tributos"][per] = valores_por_id["lucro_operacional_liq"][per] + valores_por_id["resultado_nao_operacional"][per]
            # Resultado Líquido do Exercício = Antes Tributos - Provisão IRPJ/CSLL
            valores_por_id["resultado_liquido_exercicio"][per] = valores_por_id["resultado_antes_tributos"][per] - valores_por_id["provisao_tributos"][per]

        # 4. Montagem da Árvore Final para Renderização com Análise Vertical (% AV) e Tendências
        linhas_renderizaveis = []
        rec_bruta_1t = valores_por_id["rec_bruta"]["1T"]
        rec_bruta_2t = valores_por_id["rec_bruta"]["2T"]
        rec_bruta_3t = valores_por_id["rec_bruta"]["3T"]
        rec_bruta_4t = valores_por_id["rec_bruta"]["4T"]
        rec_bruta_total = valores_por_id["rec_bruta"]["total"]

        for item_pai in self.matriz_padrao:
            linhas_renderizaveis.append(self._formatar_linha(item_pai, valores_por_id[item_pai["id"]], rec_bruta_1t, rec_bruta_2t, rec_bruta_3t, rec_bruta_4t, rec_bruta_total, nivel=0))

            if "filhos" in item_pai:
                for f in item_pai["filhos"]:
                    linhas_renderizaveis.append(self._formatar_linha(f, valores_por_id[f["id"]], rec_bruta_1t, rec_bruta_2t, rec_bruta_3t, rec_bruta_4t, rec_bruta_total, nivel=1))

            if "subgrupos" in item_pai:
                for sg in item_pai["subgrupos"]:
                    linhas_renderizaveis.append(self._formatar_linha(sg, valores_por_id[sg["id"]], rec_bruta_1t, rec_bruta_2t, rec_bruta_3t, rec_bruta_4t, rec_bruta_total, nivel=1))
                    if "filhos" in sg:
                        for f in sg["filhos"]:
                            linhas_renderizaveis.append(self._formatar_linha(f, valores_por_id[f["id"]], rec_bruta_1t, rec_bruta_2t, rec_bruta_3t, rec_bruta_4t, rec_bruta_total, nivel=2))

        return {
            "titulo": "DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO - DRE GERENCIAL CONGLUTINADA",
            "empresa_modelo": "Estrutura Corporativa Padrão da Empresa (JEV Conglutinated)",
            "colunas": ["Estrutura Gerencial de Contas", "1º Trim", "% (AV)", "2º Trim", "% (AV)", "3º Trim", "% (AV)", "4º Trim", "% (AV)", "Consolidado", "% (AV)"],
            "linhas": linhas_renderizaveis,
            "resumo_executivo": {
                "receita_bruta_anual": valores_por_id["rec_bruta"]["total"],
                "receita_liquida_anual": valores_por_id["rec_liquida"]["total"],
                "resultado_bruto_anual": valores_por_id["resultado_bruto"]["total"],
                "cmv_anual": valores_por_id["cmv"]["total"],
                "despesas_op_anual": valores_por_id["despesas_operacionais"]["total"],
                "lucro_liquido_anual": valores_por_id["resultado_liquido_exercicio"]["total"],
                "margem_liquida_anual": round((valores_por_id["resultado_liquido_exercicio"]["total"] / valores_por_id["rec_bruta"]["total"]) * 100, 2) if valores_por_id["rec_bruta"]["total"] > 0 else 0.0
            }
        }

    def _formatar_linha(self, node: Dict[str, Any], valores: Dict[str, float], rb_1t: float, rb_2t: float, rb_3t: float, rb_4t: float, rb_tot: float, nivel: int) -> Dict[str, Any]:
        v_1t = valores["1T"]
        v_2t = valores["2T"]
        v_3t = valores["3T"]
        v_4t = valores["4T"]
        v_tot = valores["total"]

        pct_1t = round((v_1t / rb_1t) * 100, 2) if rb_1t > 0 else 0.0
        pct_2t = round((v_2t / rb_2t) * 100, 2) if rb_2t > 0 else 0.0
        pct_3t = round((v_3t / rb_3t) * 100, 2) if rb_3t > 0 else 0.0
        pct_4t = round((v_4t / rb_4t) * 100, 2) if rb_4t > 0 else 0.0
        pct_tot = round((v_tot / rb_tot) * 100, 2) if rb_tot > 0 else 0.0

        td_1t = "▲" if pct_1t > 15 else ("▼" if pct_1t > 0 else "-")
        td_2t = "▲" if pct_2t > 15 else ("▼" if pct_2t > 0 else "-")
        td_3t = "▲" if pct_3t > 15 else ("▼" if pct_3t > 0 else "-")
        td_4t = "▲" if pct_4t > 15 else ("▼" if pct_4t > 0 else "-")

        return {
            "id": node["id"],
            "codigo": node.get("codigo", ""),
            "conta": node["conta"],
            "marcador": node.get("marcador", ""),
            "tipo": node.get("tipo", "analitica"),
            "estilo": node.get("estilo", ""),
            "nivel": nivel,
            "val_1t": v_1t,
            "pct_1t": pct_1t,
            "td_1t": td_1t,
            "val_2t": v_2t,
            "pct_2t": pct_2t,
            "td_2t": td_2t,
            "val_3t": v_3t,
            "pct_3t": pct_3t,
            "td_3t": td_3t,
            "val_4t": v_4t,
            "pct_4t": pct_4t,
            "td_4t": td_4t,
            "val_total": v_tot,
            "pct_total": pct_tot
        }

    def _aplicar_dados_referencia_imagem(self, valores: Dict[str, Dict[str, float]]):
        """Método desativado permanentemente: nenhum valor fictício de 94 milhões ou 244 milhões é injetado."""
        pass

conglutinador_jev = ConglutinadorJevService()
