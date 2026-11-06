import os
import json
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.services.matriz_empresa_service import conglutinador_jev, _normalizar


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
        demonstracao: str = ""
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

            nova_conta = {
                "id": f"conta_{uuid.uuid4().hex[:8]}",
                "codigo_contabil": codigo_contabil.strip(),
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


empresas_plano_service = EmpresasPlanoContasService()

