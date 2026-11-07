import os
import io
import re
import json
import uuid
import threading
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from app.services.matriz_empresa_service import conglutinador_jev, _normalizar, ESTRUTURA_MATRIZ_PADRAO


class EmpresasPlanoContasService:
    """
    Serviço Corporativo de Gestão de Múltiplas Empresas (Matriz e Filiais)
    e Plano de Contas Unificado com Herança Automática:
    Toda conta contábil cadastrada na Matriz propaga e surte efeito automaticamente
    em todas as Filiais vinculadas e no motor de amarração JEV.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.db_path = os.path.join(self.data_dir, "empresas_plano_contas.json")
        self.estado = self._carregar_banco()
        self._sincronizar_plano_com_jev()

    def _estrutura_inicial(self) -> Dict[str, Any]:
        return {
            "mascara_plano": "#.#.#.##.###",
            "empresas": [
                {
                    "id": "emp_matriz_01",
                    "codigo_empresa": "001",
                    "razao_social": "Grupo Corporativo Matriz S.A.",
                    "nome_fantasia": "Matriz Principal (Sede)",
                    "cnpj": "00.000.000/0001-91",
                    "tipo": "MATRIZ",
                    "tipo_unidade": "MATRIZ",
                    "matriz_id": None,
                    "cidade": "São Paulo",
                    "uf": "SP",
                    "cidade_uf": "São Paulo/SP",
                    "regime_tributario": "Lucro Real",
                    "criado_em": "01/01/2026 08:00"
                }
            ],
            "plano_contas": [
                {
                    "id": "conta_padrao_01",
                    "codigo_contabil": "3.1.01.001",
                    "nome_conta": "Receita de Vendas de Mercadorias (Matriz & Filiais)",
                    "demonstracao": "DRE",
                    "tipo_demonstracao": "DRE",
                    "grupo_contabil": "RECEITA",
                    "conta_destino_matriz_id": "vendas_mercadorias",
                    "conta_destino_matriz_nome": "1.01 VENDAS DE MERCADORIAS",
                    "escopo": "MATRIZ",
                    "empresa_id": "MATRIZ_GLOBAL",
                    "escopo_label": "Corporativo Global (Matriz + Todas as Filiais)",
                    "propagar_filiais": True,
                    "criado_em": "01/01/2026 08:00"
                }
            ]
        }

    def _carregar_banco(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    if isinstance(dados, dict) and "empresas" in dados and "plano_contas" in dados:
                        return dados
        except Exception:
            pass
        return self._estrutura_inicial()

    def _salvar_banco(self):
        with self._lock:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.estado, f, ensure_ascii=False, indent=2)

    def _sincronizar_plano_com_jev(self):
        """
        Garante que todas as contas do Plano de Contas da Matriz e Filiais
        estejam ativas nas regras de amarração do Conglutinador JEV.
        """
        with self._lock:
            regras_atuais = {r.get("id"): r for r in conglutinador_jev.listar_regras_depara()}
            alterou = False

            for conta in self.estado.get("plano_contas", []):
                if conta.get("tipo_demonstracao") == "DRE" and conta.get("conta_destino_matriz_id"):
                    regra_id = f"pc_{conta['id']}"
                    termo_busca = f"{conta.get('codigo_contabil', '')} {conta.get('nome_conta', '')}".strip()
                    if regra_id not in regras_atuais:
                        nova_regra = {
                            "id": regra_id,
                            "termo_origem": conta.get("nome_conta") or termo_busca,
                            "codigo_origem": conta.get("codigo_contabil", ""),
                            "termo_normalizado": _normalizar(conta.get("nome_conta", "")),
                            "codigo_normalizado": _normalizar(conta.get("codigo_contabil", "")),
                            "conta_matriz_id": conta["conta_destino_matriz_id"],
                            "conta_matriz_nome": conta.get("conta_destino_matriz_nome", conta["conta_destino_matriz_id"]),
                            "empresa_id": conta.get("empresa_id", "TODAS"),
                            "propagar_filiais": conta.get("propagar_filiais", True),
                            "observacao": f"Plano de Contas ({conta.get('escopo_label', 'Matriz + Filiais')})"
                        }
                        conglutinador_jev.regras_personalizadas.append(nova_regra)
                        alterou = True

            if alterou:
                conglutinador_jev._salvar_regras_personalizadas()

    # =========================================================================
    # 1. GESTÃO DE EMPRESAS (MATRIZ E FILIAIS)
    # =========================================================================
    def listar_empresas(self) -> List[Dict[str, Any]]:
        with self._lock:
            empresas = list(self.estado.get("empresas", []))
            if not empresas:
                self.estado = self._estrutura_inicial()
                self._salvar_banco()
                empresas = list(self.estado.get("empresas", []))
            for emp in empresas:
                emp["tipo"] = emp.get("tipo") or emp.get("tipo_unidade", "MATRIZ")
                emp["tipo_unidade"] = emp["tipo"]
                contas_aplicaveis = self.obter_plano_contas_efetivo_empresa(emp["id"])
                emp["total_contas_ativas"] = len(contas_aplicaveis)
            return empresas

    def cadastrar_empresa(
        self,
        razao_social: str,
        nome_fantasia: str = "",
        cnpj: str = "",
        tipo_unidade: str = "MATRIZ",
        matriz_id: Optional[str] = None,
        codigo_empresa: str = "",
        cidade_uf: str = "",
        regime_tributario: str = "Lucro Real",
        cidade: str = "",
        uf: str = "SP"
    ) -> Dict[str, Any]:
        with self._lock:
            tipo_norm = "FILIAL" if str(tipo_unidade).upper() == "FILIAL" else "MATRIZ"
            empresas = self.estado.setdefault("empresas", [])

            # Se for filial e não informou matriz_id, vincula automaticamente à primeira Matriz existente
            if tipo_norm == "FILIAL" and not matriz_id:
                matrizes = [e for e in empresas if (e.get("tipo") or e.get("tipo_unidade")) == "MATRIZ"]
                if matrizes:
                    matriz_id = matrizes[0]["id"]

            if not codigo_empresa:
                codigo_empresa = f"{len(empresas) + 1:03d}"

            cidade_limpa = cidade.strip() or (cidade_uf.split("/")[0].strip() if "/" in cidade_uf else cidade_uf.strip()) or "São Paulo"
            uf_limpa = uf.strip() or (cidade_uf.split("/")[1].strip() if "/" in cidade_uf else "SP")
            cidade_uf_final = cidade_uf.strip() or f"{cidade_limpa}/{uf_limpa}"

            nova_empresa = {
                "id": f"emp_{uuid.uuid4().hex[:8]}",
                "codigo_empresa": codigo_empresa.strip(),
                "razao_social": razao_social.strip(),
                "nome_fantasia": (nome_fantasia or razao_social).strip(),
                "cnpj": cnpj.strip(),
                "tipo": tipo_norm,
                "tipo_unidade": tipo_norm,
                "matriz_id": matriz_id if tipo_norm == "FILIAL" else None,
                "cidade": cidade_limpa,
                "uf": uf_limpa,
                "cidade_uf": cidade_uf_final,
                "regime_tributario": regime_tributario.strip(),
                "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            empresas.append(nova_empresa)
            self._salvar_banco()
            nova_empresa["total_contas_ativas"] = len(self.obter_plano_contas_efetivo_empresa(nova_empresa["id"]))
            return nova_empresa

    def remover_empresa(self, empresa_id: str) -> bool:
        with self._lock:
            empresas = self.estado.get("empresas", [])
            tam_antes = len(empresas)
            self.estado["empresas"] = [e for e in empresas if e.get("id") != empresa_id]
            if len(self.estado["empresas"]) < tam_antes:
                self._salvar_banco()
                return True
            return False

    # =========================================================================
    # 2. PLANO DE CONTAS MULTI-EMPRESAS (HERANÇA AUTOMÁTICA MATRIZ ➔ FILIAIS)
    # =========================================================================
    def obter_plano_contas_efetivo_empresa(self, empresa_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna o Plano de Contas ativo para uma empresa específica.
        Se a empresa for uma FILIAL, ela herda automaticamente todas as contas cadastradas
        na sua MATRIZ (onde propagar_filiais=True), além das contas específicas dela.
        """
        with self._lock:
            todas_contas = self.estado.get("plano_contas", [])
            for c in todas_contas:
                c["demonstracao"] = c.get("demonstracao") or c.get("tipo_demonstracao", "DRE")
                c["tipo_demonstracao"] = c["demonstracao"]
                c["escopo"] = c.get("escopo") or ("MATRIZ" if c.get("empresa_id") in (None, "TODAS", "MATRIZ", "MATRIZ_GLOBAL") else c.get("empresa_id"))

            if not empresa_id or empresa_id in ("todas", "CONSOLIDADO"):
                return list(todas_contas)

            empresas_map = {e["id"]: e for e in self.estado.get("empresas", [])}
            emp = empresas_map.get(empresa_id)
            if not emp:
                return list(todas_contas)

            eh_filial = (emp.get("tipo") or emp.get("tipo_unidade")) == "FILIAL"
            matriz_id_vinculada = emp.get("matriz_id") if eh_filial else emp["id"]

            contas_efetivas = []
            for c in todas_contas:
                c_emp_id = c.get("empresa_id")
                c_escopo = c.get("escopo")
                # 1. Conta global/Matriz ou da própria empresa
                if not c_emp_id or c_emp_id in ("TODAS", "MATRIZ", "MATRIZ_GLOBAL") or c_escopo == "MATRIZ" or c_emp_id == empresa_id or c_escopo == empresa_id:
                    c_copia = dict(c)
                    c_copia["origem_heranca"] = "Herdada da Matriz" if (eh_filial and (c_escopo == "MATRIZ" or c_emp_id in ("TODAS", "MATRIZ", "MATRIZ_GLOBAL"))) else "Própria / Global"
                    contas_efetivas.append(c_copia)
                # 2. Conta cadastrada especificamente no ID da Matriz com propagação automática para as Filiais
                elif eh_filial and (c_emp_id == matriz_id_vinculada or c_escopo == matriz_id_vinculada) and c.get("propagar_filiais", True):
                    c_copia = dict(c)
                    c_copia["origem_heranca"] = "Herdada da Matriz"
                    contas_efetivas.append(c_copia)

            return contas_efetivas

    def obter_mascara(self) -> str:
        with self._lock:
            return self.estado.get("mascara_plano", "#.#.#.##.###")

    def atualizar_mascara(self, nova_mascara: str) -> str:
        with self._lock:
            masc = (nova_mascara or "#.#.#.##.###").strip()
            self.estado["mascara_plano"] = masc
            self._salvar_banco()
            return masc

    def cadastrar_conta_plano(
        self,
        codigo_contabil: str,
        nome_conta: str,
        tipo_demonstracao: str = "DRE",
        grupo_contabil: str = "RECEITA",
        conta_destino_matriz_id: str = "vendas_mercadorias",
        conta_destino_matriz_nome: str = "",
        empresa_id: str = "MATRIZ_GLOBAL",
        propagar_filiais: bool = True,
        escopo: str = "MATRIZ",
        demonstracao: str = "",
        codigo_reduzido: str = "",
        ref: str = ""
    ) -> Dict[str, Any]:
        """
        Cadastra uma conta no Plano de Contas.
        Se cadastrada na Matriz (ou Global), propaga automaticamente o efeito para todas as Filiais
        e registra no motor de amarração JEV.
        """
        with self._lock:
            dem_final = (demonstracao or tipo_demonstracao or "DRE").upper().strip()
            escopo_final = (escopo or empresa_id or "MATRIZ").strip()
            emp_id_final = "MATRIZ_GLOBAL" if escopo_final in ("MATRIZ", "MATRIZ_GLOBAL", "TODAS") else escopo_final

            empresas = self.estado.get("empresas", [])
            emp_obj = next((e for e in empresas if e["id"] == emp_id_final), None)

            if emp_obj:
                if (emp_obj.get("tipo") or emp_obj.get("tipo_unidade")) == "MATRIZ":
                    filiais_vinc = [f for f in empresas if (f.get("tipo") or f.get("tipo_unidade")) == "FILIAL" and f.get("matriz_id") == emp_obj["id"]]
                    escopo_label = f"Matriz ({emp_obj['nome_fantasia']}) + {len(filiais_vinc)} Filiais" if propagar_filiais else f"Apenas Matriz ({emp_obj['nome_fantasia']})"
                else:
                    escopo_label = f"Filial ({emp_obj['nome_fantasia']})"
            else:
                escopo_label = "Corporativo Global (Matriz + Todas as Filiais)"

            # Determina o código reduzido sequencial automático caso não fornecido
            plano_atual = self.estado.get("plano_contas", [])
            cod_red = codigo_reduzido.strip() if codigo_reduzido else f"{len(plano_atual) + 1:06d}"

            # Determina Ref ('S' para analítica, vazio para grupo sintético)
            mascara = self.obter_mascara()
            partes_mascara = len(mascara.split("."))
            partes_conta = len(codigo_contabil.strip().split("."))
            ref_final = ref.strip().upper() if ref else ("S" if partes_conta >= partes_mascara else "")

            nova_conta = {
                "id": f"conta_{uuid.uuid4().hex[:8]}",
                "codigo_contabil": codigo_contabil.strip(),
                "codigo_reduzido": cod_red,
                "ref": ref_final,
                "nome_conta": nome_conta.strip(),
                "demonstracao": dem_final,
                "tipo_demonstracao": dem_final,
                "grupo_contabil": grupo_contabil.upper().strip(),
                "conta_destino_matriz_id": conta_destino_matriz_id.strip(),
                "conta_destino_matriz_nome": (conta_destino_matriz_nome or conta_destino_matriz_id).strip(),
                "escopo": "MATRIZ" if emp_id_final == "MATRIZ_GLOBAL" else emp_id_final,
                "empresa_id": emp_id_final,
                "escopo_label": escopo_label,
                "propagar_filiais": bool(propagar_filiais),
                "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M")
            }

            self.estado.setdefault("plano_contas", []).append(nova_conta)
            self._salvar_banco()
            self._sincronizar_plano_com_jev()
            return nova_conta

    def remover_conta_plano(self, conta_id: str) -> bool:
        with self._lock:
            plano = self.estado.get("plano_contas", [])
            tam_antes = len(plano)
            self.estado["plano_contas"] = [c for c in plano if c.get("id") != conta_id]
            if len(self.estado["plano_contas"]) < tam_antes:
                self._salvar_banco()
                # Remove também do JEV
                conglutinador_jev.remover_regra_depara(f"pc_{conta_id}")
                return True
            return False

    def limpar_plano_contas_completo(self) -> Dict[str, Any]:
        """
        Zera/limpa todas as contas cadastradas no Plano de Contas.
        Enquanto o Plano de Contas / DRE estiver vazio, a importação de saldos fica bloqueada.
        """
        with self._lock:
            self.estado["plano_contas"] = []
            self._salvar_banco()
            pront = self.verificar_prontidao_importacao()
            return {
                "status": "sucesso",
                "mensagem": "Todas as contas do Plano de Contas e DRE foram removidas com sucesso.",
                "plano_contas": [],
                "prontidao_importacao": pront,
                **pront
            }

    def verificar_prontidao_importacao(self) -> Dict[str, Any]:
        """
        Verifica se o Plano de Contas e a estrutura de DRE estão devidamente cadastrados.
        Restringe a importação de movimentação/saldos caso o cadastro esteja vazio.
        """
        with self._lock:
            plano = self.estado.get("plano_contas", [])
            contas_dre = [c for c in plano if (c.get("demonstracao") or c.get("tipo_demonstracao", "DRE")).upper() in ("DRE", "RESULTADO", "PLANO_DE_CONTAS")]
            contas_balanco = [c for c in plano if (c.get("demonstracao") or c.get("tipo_demonstracao", "")).upper() in ("BALANCO", "PATRIMONIAL", "PLANO_DE_CONTAS")]
            liberado = len(plano) > 0 and len(contas_dre) > 0
            if liberado:
                motivo = f"Cadastro validado: {len(plano)} conta(s) ativa(s) no Plano de Contas ({len(contas_dre)} DRE / {len(contas_balanco)} Balanço)."
            else:
                motivo = (
                    "🚫 Importação de Balanço e DRE Bloqueada: Não é permitido importar demonstrações com valores sem que o "
                    "Plano de Contas corporativo esteja previamente cadastrado! Acesse a aba '📑 Plano de Contas' para cadastrar primeiro a estrutura."
                )
            return {
                "liberado": liberado,
                "total_contas": len(plano),
                "total_contas_dre": len(contas_dre),
                "total_contas_balanco": len(contas_balanco),
                "tem_plano_contas": len(plano) > 0,
                "tem_dre_cadastrada": len(contas_dre) > 0,
                "motivo": motivo
            }

    # =========================================================================
    # 3. IMPORTADOR INTELIGENTE DE ESTRUTURA ENXUTA (PLANO DE CONTAS OU DRE)
    # =========================================================================
    def _limpar_nome_conta_enxuta(self, texto_bruto: str) -> Tuple[str, str]:
        """
        Higieniza profundamente uma linha de planilha/PDF para extrair SOMENTE:
        (codigo_contabil, nome_conta_limpo), removendo saldos numéricos, datas,
        percentuais, traços residuais, cabeçalhos e lixo visual.
        """
        if not texto_bruto:
            return "", ""
        s = str(texto_bruto).strip()
        if not s or s.lower() in ("nan", "none", "null", "-", ".", "--"):
            return "", ""

        # Remove datas (ex: "31/12/2026"), valores monetários (com ou sem parênteses/R$) e percentuais em qualquer posição
        s = re.sub(r'\b\d{2}/\d{2}/\d{2,4}\b', ' ', s)
        s = re.sub(r'[\(\[]?\s*R\$\s*[\d\.,\(\)-]+\s*[\)\]]?', ' ', s, flags=re.IGNORECASE)
        s = re.sub(r'[\(\-]?\b\d{1,3}(?:\.\d{3})*,\d{2}\b[\)\-]?', ' ', s)
        s = re.sub(r'\b\d+(?:[,\.]\d+)?\s*%', ' ', s)

        # Extrai código contábil no início caso esteja colado na descrição (ex: "3.1.01.001 - Vendas de Mercadorias")
        cod_extraido = ""
        m_cod = re.match(r'^(\d+(?:\.\d+)*)\s*[-–—:]?\s+(.*)$', s)
        if m_cod:
            cand_cod = m_cod.group(1).strip()
            resto = m_cod.group(2).strip()
            # Evita confundir "13º Salário" com código contábil "13"
            if not resto.lower().startswith(("º", "o salario", "º salario", "o. salario")):
                cod_extraido = cand_cod
                s = resto

        # Limpa múltiplos espaços e caracteres de controle
        s = re.sub(r'\s+', ' ', s).strip(" -–—:;|/\\")

        # Ignora linhas que são puramente números, datas ou cabeçalhos/rodapés de sistema
        if re.match(r'^[\d\.,\(\)\s%-]+$', s):
            return "", ""

        s_norm = _normalizar(s)
        palavras_lixo_cabecalho = {
            "conta", "codigo", "descricao", "descricao da conta", "nome da conta",
            "especificacao", "historico", "saldo anterior", "saldo atual", "debito",
            "credito", "movimento", "total", "totais", "subtotal", "pagina",
            "emitido em", "cnpj", "razao social", "periodo", "exercicio",
            "1o trimestre", "2o trimestre", "3o trimestre", "4o trimestre",
            "1t", "2t", "3t", "4t", "av", "ah", "analise vertical"
        }
        if s_norm in palavras_lixo_cabecalho or len(s) < 3:
            return "", ""
        if any(s_norm.startswith(p) for p in ("cnpj:", "empresa:", "periodo:", "emissao:", "data:", "hora:", "folha:", "pagina:")):
            return "", ""

        return cod_extraido, s

    def _identificar_peca_e_classificar_linhas(
        self,
        linhas_extraidas: List[Tuple[str, str]],
        nome_arquivo: str,
        tipo_forcar: str = "AUTO"
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Analisa o conjunto de contas extraídas e identifica automaticamente que tipo de peça contábil
        está sendo importada:
        - 'PLANO_DE_CONTAS' (Elenco/Plano de Contas Geral com Ativo, Passivo e Resultado)
        - 'DRE' (Estrutura de Demonstração do Resultado do Exercício)
        - 'BALANCO_PATRIMONIAL' (Estrutura de Balanço Patrimonial)
        """
        termos_dre = [
            "receita", "vendas", "faturamento", "deduc", "imposto incidente", "icms", "pis", "cofins",
            "iss", "custo", "cmv", "cpv", "csp", "despesa", "salario", "ordenado", "ferias", "13",
            "fgts", "inss", "vale transporte", "assistencia medica", "alimentacao", "energia",
            "agua", "telefone", "internet", "aluguel", "condominio", "depreciac", "honorario",
            "juros", "tarifa", "resultado", "lucro", "ebitda", "irpj", "csll", "pro-labore", "pro labore"
        ]
        termos_balanco = [
            "ativo", "circulante", "caixa", "banco", "aplicac", "clientes", "duplicatas a receber",
            "estoques", "adiantamento", "imobilizado", "intangivel", "investimento", "passivo",
            "fornecedor", "emprestimo", "financiamento", "obrigacoes", "contas a pagar",
            "patrimonio liquido", "capital social", "reservas", "lucros acumulados", "prejuizos acumulados"
        ]

        qtd_dre = 0
        qtd_bp = 0
        todos_codigos = [cod for cod, _ in linhas_extraidas if cod]

        contas_estruturadas = []
        for idx, (cod, nome) in enumerate(linhas_extraidas):
            nome_norm = _normalizar(nome)
            cod_limpo = cod.strip().rstrip(".")

            eh_dre = False
            eh_bp = False

            # Classificação por código contábil clássico ou semântica
            if any(w in nome_norm for w in termos_dre):
                eh_dre = True
            if any(w in nome_norm for w in termos_balanco) and not any(w in nome_norm for w in ["receita", "despesa", "custo", "resultado", "vendas"]):
                eh_bp = True

            if not eh_dre and not eh_bp:
                if cod_limpo.startswith(("1", "2")):
                    eh_bp = True
                elif cod_limpo.startswith(("3", "4", "5", "6", "7", "8", "9", "10")):
                    eh_dre = True
                else:
                    eh_dre = True

            if eh_dre and not eh_bp:
                qtd_dre += 1
                dem_item = "DRE"
            else:
                qtd_bp += 1
                dem_item = "BALANCO"

            # Detecta se é conta Sintética (Grupo Pai) ou Analítica (Filha)
            eh_sintetica = False
            if cod_limpo:
                for outro_c in todos_codigos:
                    outro_limpo = outro_c.strip().rstrip(".")
                    if outro_limpo != cod_limpo and outro_limpo.startswith(cod_limpo + "."):
                        eh_sintetica = True
                        break
            if any(g in nome_norm for g in [
                "receita operacional bruta", "deducoes da receita", "receita operacional liquida",
                "custo operacional", "resultado operacional", "despesas operacionais",
                "despesas com pessoal", "encargos sociais", "ativo circulante", "ativo nao circulante",
                "passivo circulante", "passivo nao circulante", "patrimonio liquido"
            ]):
                eh_sintetica = True

            # Amarração automática no destino da Matriz Oficial / Balanço
            if dem_item == "DRE":
                id_dest = ""
                for item_pai in conglutinador_jev.matriz_padrao:
                    for f in item_pai.get("filhos", []):
                        if _normalizar(f["conta"]) == nome_norm or any(_normalizar(s) in nome_norm for s in f.get("sinonimos", [])):
                            id_dest = f["id"]
                            break
                    if id_dest:
                        break
                    for sg in item_pai.get("subgrupos", []):
                        for f in sg.get("filhos", []):
                            if _normalizar(f["conta"]) == nome_norm or any(_normalizar(s) in nome_norm for s in f.get("sinonimos", [])):
                                id_dest = f["id"]
                                break
                        if id_dest:
                            break
                if not id_dest:
                    if any(w in nome_norm for w in ["custo", "cmv", "mercadoria vendida"]):
                        id_dest = "custo_mercadoria"
                    elif any(w in nome_norm for w in ["icms"]):
                        id_dest = "icms_vendas"
                    elif any(w in nome_norm for w in ["pis"]):
                        id_dest = "pis_vendas"
                    elif any(w in nome_norm for w in ["cofins"]):
                        id_dest = "cofins_vendas"
                    elif any(w in nome_norm for w in ["imposto", "deduc", "cancelad", "devoluc"]):
                        id_dest = "imposto_incidente"
                    elif any(w in nome_norm for w in ["salario", "ordenado", "pessoal", "folha"]):
                        id_dest = "salarios_ordenados"
                    elif any(w in nome_norm for w in ["despesa", "administrativ", "servico", "manutencao", "taxa"]):
                        id_dest = "serv_diversos_pj"
                    else:
                        id_dest = "vendas_mercadorias"
                natureza = "CREDORA" if id_dest in ("vendas_mercadorias", "rendimento_aplicacao", "juros_selic_impostos", "compensacoes_rf", "bonificacoes_fornec", "acordos_promocionais", "aluguel_loja") else "DEVEDORA"
                grupo_c = "RECEITA" if natureza == "CREDORA" else "DESPESA_CUSTO"
            else:
                if any(w in nome_norm for w in ["patrimonio liquido", "capital social", "reserva", "lucros acumulados"]) or cod_limpo.startswith(("2.3", "2.03")):
                    id_dest = "patrimonio_liquido"
                    natureza = "CREDORA"
                elif any(w in nome_norm for w in ["passivo", "fornecedor", "obrigac", "emprestimo", "pagar", "recolher"]) or cod_limpo.startswith("2"):
                    id_dest = "passivo_nao_circulante" if "nao circulante" in nome_norm or "longo prazo" in nome_norm or cod_limpo.startswith(("2.2", "2.02")) else "passivo_circulante"
                    natureza = "CREDORA"
                else:
                    id_dest = "ativo_nao_circulante" if any(w in nome_norm for w in ["imobilizado", "intangivel", "investimento", "nao circulante", "longo prazo"]) or cod_limpo.startswith(("1.2", "1.02")) else "ativo_circulante"
                    natureza = "DEVEDORA"
                grupo_c = id_dest.upper()

            codigo_final = cod_limpo if cod_limpo else f"{dem_item[:3]}.{idx + 1:03d}"

            contas_estruturadas.append({
                "codigo_contabil": codigo_final,
                "nome_conta": nome,
                "demonstracao": dem_item,
                "tipo_conta": "SINTETICA" if eh_sintetica else "ANALITICA",
                "natureza": natureza,
                "grupo_contabil": grupo_c,
                "conta_destino_matriz_id": id_dest
            })

        # Decisão sobre qual Peça Contábil foi importada
        nome_arq_norm = _normalizar(nome_arquivo)
        if tipo_forcar and tipo_forcar.upper() in ("PLANO_DE_CONTAS", "DRE", "BALANCO_PATRIMONIAL", "BALANCO"):
            peca_detectada = "BALANCO_PATRIMONIAL" if tipo_forcar.upper() == "BALANCO" else tipo_forcar.upper()
        elif "plano" in nome_arq_norm or "elenco" in nome_arq_norm or (qtd_dre >= 3 and qtd_bp >= 3):
            peca_detectada = "PLANO_DE_CONTAS"
        elif qtd_dre >= qtd_bp:
            peca_detectada = "DRE"
        else:
            peca_detectada = "BALANCO_PATRIMONIAL"

        # Se a peça inteira foi identificada como DRE, garante que todas as contas fiquem marcadas como DRE
        if peca_detectada == "DRE":
            for c in contas_estruturadas:
                c["demonstracao"] = "DRE"

        desc_peca_map = {
            "PLANO_DE_CONTAS": f"Plano de Contas Corporativo Completo ({qtd_dre} contas de Resultado/DRE e {qtd_bp} contas Patrimoniais/Balanço)",
            "DRE": f"Demonstração do Resultado do Exercício - Estrutura DRE ({len(contas_estruturadas)} rubricas enxutas)",
            "BALANCO_PATRIMONIAL": f"Balanço Patrimonial - Estrutura de Contas ({len(contas_estruturadas)} rubricas enxutas)"
        }
        return peca_detectada, desc_peca_map.get(peca_detectada, peca_detectada), contas_estruturadas

    def importar_estrutura_contas_enxuta(
        self,
        conteudo_arquivo: bytes,
        nome_arquivo: str,
        escopo: str = "MATRIZ",
        tipo_forcar: str = "AUTO",
        limpar_anterior: bool = False
    ) -> Dict[str, Any]:
        """
        Importa uma planilha (.xlsx, .xls, .csv) ou PDF contendo um Plano de Contas ou DRE,
        higieniza todos os dados (remove saldos, datas, cabeçalhos e ruídos para deixar a estrutura 100% enxuta),
        identifica automaticamente que tipo de peça contábil está sendo importada (Plano de Contas ou DRE),
        cadastra as contas na Matriz e propaga automaticamente para todas as Filiais!
        """
        nome_lower = (nome_arquivo or "").lower()
        linhas_brutas: List[Tuple[str, str]] = []

        # 1. Extração a partir de PDF, Excel ou CSV
        if nome_lower.endswith(".pdf"):
            import pdfplumber
            with pdfplumber.open(io.BytesIO(conteudo_arquivo)) as pdf:
                for page in pdf.pages:
                    texto = page.extract_text() or ""
                    for linha in texto.split("\n"):
                        cod, nome_limpo = self._limpar_nome_conta_enxuta(linha)
                        if nome_limpo:
                            linhas_brutas.append((cod, nome_limpo))
        else:
            dfs: List[pd.DataFrame] = []
            lido = False
            if nome_lower.endswith((".csv", ".txt")):
                for enc in ("utf-8", "latin-1", "cp1252"):
                    try:
                        dfs.append(pd.read_csv(io.BytesIO(conteudo_arquivo), sep=None, engine="python", encoding=enc))
                        lido = True
                        break
                    except Exception:
                        continue
            if not lido:
                for eng in ("openpyxl", "xlrd"):
                    try:
                        xl = pd.ExcelFile(io.BytesIO(conteudo_arquivo), engine=eng)
                        for sh in xl.sheet_names:
                            dfs.append(pd.read_excel(xl, sheet_name=sh))
                        lido = bool(dfs)
                        if lido:
                            break
                    except Exception:
                        continue
            if not lido:
                try:
                    dfs.extend(pd.read_html(io.BytesIO(conteudo_arquivo)))
                    lido = bool(dfs)
                except Exception:
                    pass
            if not lido:
                for enc in ("utf-8", "latin-1", "cp1252"):
                    try:
                        dfs.append(pd.read_csv(io.BytesIO(conteudo_arquivo), sep=None, engine="python", encoding=enc))
                        lido = True
                        break
                    except Exception:
                        continue

            for df in dfs:
                if df is None or df.empty:
                    continue
                # Examina também a linha de cabeçalho caso uma conta esteja na linha 0
                for _, row in df.iterrows():
                    textos_celulas = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip() not in ("", "nan", "None")]
                    if not textos_celulas:
                        continue
                    # Procura código e nome nas primeiras células não numéricas da linha
                    cod_linha = ""
                    nome_linha = ""
                    for cel in textos_celulas:
                        # Se for célula puramente de código contábil (ex: "1.01.01" ou "3.1.01")
                        if not cod_linha and re.match(r'^\d+(?:\.\d+)+$', cel):
                            cod_linha = cel
                            continue
                        c_ext, n_ext = self._limpar_nome_conta_enxuta(cel)
                        if n_ext and len(n_ext) >= 3:
                            if c_ext and not cod_linha:
                                cod_linha = c_ext
                            nome_linha = n_ext
                            break
                    if nome_linha:
                        linhas_brutas.append((cod_linha, nome_linha))

        # 2. Deduplicação enxuta preservando a ordem original
        linhas_unicas: List[Tuple[str, str]] = []
        chaves_vistas = set()
        for cod, nome in linhas_brutas:
            chave = f"{cod}_{_normalizar(nome)}"
            if chave not in chaves_vistas:
                chaves_vistas.add(chave)
                linhas_unicas.append((cod, nome))

        if not linhas_unicas:
            raise ValueError("Nenhuma conta contábil válida foi encontrada no arquivo enviado para estruturar o Plano de Contas / DRE.")

        # 3. Identificação inteligente da peça contábil (PLANO_DE_CONTAS vs DRE vs BALANCO) e classificação
        peca_detectada, descricao_peca, contas_classificadas = self._identificar_peca_e_classificar_linhas(
            linhas_unicas,
            nome_arquivo=nome_arquivo,
            tipo_forcar=tipo_forcar
        )

        # 4. Gravação no banco de dados com opção de substituir/limpar anteriores para manter enxuto
        with self._lock:
            if limpar_anterior:
                self.estado["plano_contas"] = []

            existentes_chaves = {
                f"{c.get('codigo_contabil', '')}_{_normalizar(c.get('nome_conta', ''))}"
                for c in self.estado.get("plano_contas", [])
            }

            novas_cadastradas = []
            for item in contas_classificadas:
                ch = f"{item['codigo_contabil']}_{_normalizar(item['nome_conta'])}"
                if ch in existentes_chaves:
                    continue
                existentes_chaves.add(ch)
                conta_salva = self.cadastrar_conta_plano(
                    codigo_contabil=item["codigo_contabil"],
                    nome_conta=item["nome_conta"],
                    tipo_demonstracao=item["demonstracao"],
                    grupo_contabil=item["grupo_contabil"],
                    conta_destino_matriz_id=item["conta_destino_matriz_id"],
                    conta_destino_matriz_nome=item["conta_destino_matriz_id"],
                    empresa_id="MATRIZ_GLOBAL" if escopo in ("MATRIZ", "MATRIZ_GLOBAL", "TODAS") else escopo,
                    propagar_filiais=True,
                    escopo=escopo,
                    demonstracao=item["demonstracao"]
                )
                conta_salva["tipo_conta"] = item["tipo_conta"]
                conta_salva["natureza"] = item["natureza"]
                conta_salva["peca_origem"] = peca_detectada
                novas_cadastradas.append(conta_salva)

            self._salvar_banco()
            self._sincronizar_plano_com_jev()

        qtd_dre_imp = sum(1 for c in novas_cadastradas if c.get("demonstracao") == "DRE")
        qtd_bp_imp = sum(1 for c in novas_cadastradas if c.get("demonstracao") == "BALANCO")
        plano_efetivo = self.obter_plano_contas_efetivo_empresa()

        return {
            "status": "sucesso",
            "arquivo": nome_arquivo,
            "peca_contabil_detectada": peca_detectada,
            "rotulo_peca": descricao_peca,
            "descricao_peca": descricao_peca,
            "total_linhas_higienizadas": len(linhas_unicas),
            "total_contas_importadas": len(novas_cadastradas),
            "total_novas_contas_cadastradas": len(novas_cadastradas),
            "contas_dre_importadas": qtd_dre_imp,
            "contas_balanco_importadas": qtd_bp_imp,
            "linhas_ruido_descartadas": max(0, len(linhas_brutas) - len(linhas_unicas)),
            "total_contas_ativas_no_plano": len(self.estado.get("plano_contas", [])),
            "contas_cadastradas": novas_cadastradas,
            "contas_importadas": novas_cadastradas,
            "plano_contas": plano_efetivo,
            "prontidao_importacao": self.verificar_prontidao_importacao(),
            "mensagem": (
                f"✅ Peça Contábil reconhecida como [{peca_detectada}] ({descricao_peca})! "
                f"Dados higienizados e enxutos: {len(novas_cadastradas)} conta(s) cadastrada(s) na Matriz e propagada(s) para todas as Filiais."
            )
        }


empresas_plano_service = EmpresasPlanoContasService()

