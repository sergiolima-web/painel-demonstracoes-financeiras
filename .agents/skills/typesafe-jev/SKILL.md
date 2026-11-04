---
name: typesafe-jev
description: Diretrizes de integração, padrões de código e boas práticas para utilização do modelo de decisão rápida JEV da TypeSafe AI (System 1 Decision Engine) no projeto de Demonstrações Financeiras.
---

# 🧠 Skill: Integração e Padrões TypeSafe JEV (System 1 Decision Engine)

Esta habilidade (Skill) padroniza a integração, uso e segurança do modelo **JEV** da **TypeSafe AI** no sistema de **Análise e Apresentação de Balanços e DRE**.

---

## 🎯 1. O que é o JEV e quando utilizar

O **Jev** é um modelo de decisão rápida (*System 1*), focado em julgamentos estruturados e previsíveis, e não em geração de textos longos.

### ✅ Casos de Uso no Projeto de Balanço & DRE:
* **Mapeamento e Classificação Contábil:** Identificar grupos de contas (*De-Para*) em Balanços e DREs importados.
* **Detecção de Anomalias e Alertas:** Avaliar se variações trimestrais de indicadores (Liquidez, ROE, Margens) exigem destaque para acionistas.
* **Roteamento de Decisões e Ferramentas:** Servir como decisão lógica inteligente (*smart if-statement*) em fluxos assíncronos.
* **Validação de Coerência Contábil:** Checagem rápida de estrutura sem alucinação de texto.

---

## 🛡️ 2. Segurança e Governança Zero Trust (Obrigatório)

* **Nunca expor no Frontend:** O cliente TypeSafe **sempre** é executado no Backend (Python/FastAPI). O frontend consome apenas a API do backend.
* **Armazenamento Seguro:** A chave TYPESAFE_API_KEY deve estar exclusivamente no .env do servidor e no .env.example apenas como referência.
* **Sanitização de Logs:** Nunca imprimir a chave TYPESAFE_API_KEY em logs, consoles ou respostas de erro HTTP.
* **Isolamento Criptográfico contra Injeção de Prompt (Ken Huang & Chris Hughes):** Todo texto e saldo recuperados de arquivos externos (planilhas e PDFs) devem passar por barreira de proteção ativa (`guardrails_seguranca`), sendo sanitizados e encapsulados em tags seguras com hash SHA-256 (`<untrusted_content>`) antes de formar o `state` do JEV.


---

## 💻 3. Padrão de Implementação em Python (	ypesafe-sdk)

### Instalação:
`ash
pip install typesafe-sdk
`

### Estrutura do Serviço (ackend/app/services/jev_service.py):
`python
import os
from typing import Dict, Any
from typesafe_sdk import TypeSafeClient, Choice, Score, Noul
from app.services.security_guardrails import guardrails_seguranca

class JevDecisionService:
    def __init__(self):
        self.api_key = os.getenv("TYPESAFE_API_KEY")

    def classificar_conta_contabil(self, conta: str, descricao: str) -> Dict[str, Any]:
        """
        Classifica contas de Balanço/DRE em grupos padronizados sob isolamento seguro (Ken Huang & Chris Hughes).
        """
        # 1. Barreira de Proteção Ativa e Isolamento Criptográfico
        bloco_protegido = guardrails_seguranca.encapsular_em_tags_seguras(
            f"Conta Contábil: {conta} | Detalhes: {descricao}",
            identificador_origem=f"conta_{conta}"
        )

        if not self.api_key:
            # Fallback determinístico seguro
            return {"grupo_balanco": "A Classificar", "relevancia": 5, "anomalia": False}

        # 2. Imposição de Nível de Sistema com Tags Seguras
        estado = f"{bloco_protegido['instrucao_sistema']}\n\n{bloco_protegido['bloco_seguro']}"

        with TypeSafeClient(api_key=self.api_key) as client:
            decisao = client.system_one(
                state=f"Conta Contábil: {conta} | Detalhes: {descricao}",
                questions={
                    "grupo_balanco": Choice(
                        instructions="Determine o grupo correto da demonstração financeira para esta conta.",
                        criteria={
                            "Ativo Circulante - Disponibilidades": "Caixa, bancos e aplicações de liquidez imediata",
                            "Ativo Circulante - Clientes/Estoques": "Contas a receber de clientes e mercadorias/produtos",
                            "Ativo Não Circulante - Imobilizado/Investimentos": "Bens duráveis, veículos, prédios ou participações",
                            "Passivo Circulante - Fornecedores/Obrigações": "Dívidas e contas a pagar de curto prazo (até 1 ano)",
                            "Passivo Não Circulante - Dívidas Longo Prazo": "Financiamentos e obrigações acima de 1 ano",
                            "Patrimônio Líquido - Capital e Reservas": "Capital social, lucros acumulados e reservas",
                            "DRE - Receita Bruta / Deduções": "Faturamento bruto de vendas ou serviços e deduções",
                            "DRE - Custos dos Serviços/Produtos": "Custos diretamente associados à produção ou venda",
                            "DRE - Despesas Operacionais / Administrativas": "Despesas com pessoal, aluguel, comercial e geral",
                            "DRE - Resultado Financeiro / Impostos": "Juros, receitas financeiras, IRPJ e CSLL"
                        }
                    ),
                    "relevancia_acionistas": Score(
                        instructions="Qual a relevância desta conta para destaque em apresentações aos acionistas?",
                        criteria=[
                            "Baixa relevância operacional",
                            "Média relevância (acompanhamento rotineiro)",
                            "Alta relevância estratégica para acionistas"
                        ]
                    ),
                    "risco_anomalia": Noul(
                        instructions="Esta linha apresenta características atípicas ou de alto risco financeiro?"
                    )
                }
            )
            return {
                "icone": "⚡🧠",
                "badge": "⚡🧠 JEV Decision Engine",
                "tag_ia": f"TypeSafe JEV ({decisao.model})",
                "grupo_escolhido": decisao.answers["grupo_balanco"].choice,
                "confianca_classificacao": decisao.answers["grupo_balanco"].confidence,
                "score_relevancia": decisao.answers["relevancia_acionistas"].score,
                "probabilidade_anomalia": decisao.answers["risco_anomalia"].noul
            }
```

---

## ⚡ 4. Identificação Visual e Transparência de IA
- **Ícone e Badge Padrão:** Toda resposta, insight, classificação ou decisão gerada pelo JEV deve conter o ícone **`⚡🧠`** e a tag/badge **`⚡🧠 JEV Engine`**.
- **Exibição no Frontend:** Nos componentes de tela, tabelas e relatórios, exibir o badge luminoso `⚡🧠 JEV` ao lado de campos classificados por IA para que o usuário identifique instantaneamente a atuação do modelo.

---

## ⚡ 5. Boas Práticas de Performance e Custos

1. **Cálculos matemáticos no Python:** Use pandas e numpy para somas, médias e fórmulas de índices. Chame o Jev apenas para classificação e tomada de decisão lógica.
2. **Contexto Conciso:** No parâmetro state, envie apenas os dados essenciais (nome da conta, saldo, variação %) para manter o consumo de tokens no mínimo.
3. **Fallback Resiliente:** Sempre implemente uma regra padrão (fallback) para o sistema continuar funcionando mesmo se a API do Jev estiver sem créditos ou offline temporariamente.

