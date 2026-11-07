import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_configuracao_mascara_plano():
    # 1. Obter empresas e plano inicial
    res = client.get("/api/empresas-plano")
    assert res.status_code == 200
    dados = res.json()
    assert "mascara_plano" in dados
    assert "plano_contas" in dados

    # 2. Atualizar a mascara para o modelo Fortes/Dominio 5 niveis
    nova_mascara = "#.#.#.##.###"
    res_post = client.post("/api/plano-contas/mascara", json={"mascara": nova_mascara})
    assert res_post.status_code == 200
    assert res_post.json()["mascara_ativa"] == nova_mascara

    # 3. Cadastrar conta com codigo reduzido e ref analitica
    nova_conta = {
        "codigo_contabil": "1.1.1.01.001",
        "codigo_reduzido": "000005",
        "ref": "S",
        "nome_conta": "Banco Caixa Econômica Federal",
        "demonstracao": "BALANCO",
        "tipo_demonstracao": "BALANCO",
        "conta_destino_matriz_id": "ativo_circulante",
        "escopo": "MATRIZ",
        "empresa_id": "MATRIZ_GLOBAL",
        "propagar_filiais": True
    }
    res_conta = client.post("/api/plano-contas", json=nova_conta)
    assert res_conta.status_code == 200
    contas = res_conta.json()["plano_contas"]
    conta_salva = next((c for c in contas if c["codigo_contabil"] == "1.1.1.01.001"), None)
    assert conta_salva is not None
    assert conta_salva["codigo_reduzido"] == "000005"
    assert conta_salva["ref"] == "S"

def test_bloqueio_importacao_sem_plano_de_contas():
    """
    REGRA CONTÁBIL DE GOVERNANÇA ZERO TRUST:
    NÃO É PERMITIDO IMPORTAR BALANÇO OU DRE SE NÃO EXISTIR UM PLANO DE CONTAS CADASTRADO!
    """
    # 1. Zera o plano de contas para simular ambiente sem plano cadastrado
    client.post("/api/plano-contas/limpar-tudo")

    # 2. Tenta enviar uma planilha de balanço/DRE para /api/upload-demonstracao
    arquivo_falso = io.BytesIO(b"conteudo_simulado_planilha")
    res_upload = client.post(
        "/api/upload-demonstracao",
        files={"file": ("balanco_teste.xlsx", arquivo_falso, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"ano_destino": "2026", "trimestres_autorizados": '["1T"]'}
    )

    # 3. Deve ser TERMINANTEMENTE BLOQUEADO com status 400
    assert res_upload.status_code == 400
    dados = res_upload.json()
    assert dados.get("bloqueado") is True
    assert "Bloqueada" in dados.get("mensagem", "")
    assert "Plano de Contas" in dados.get("mensagem", "")

    # 4. Restaura cadastrando uma conta para restabelecer a integridade do sistema
    conta_restauracao = {
        "codigo_contabil": "3.1.01.001",
        "codigo_reduzido": "000001",
        "ref": "S",
        "nome_conta": "Vendas de Mercadorias",
        "demonstracao": "DRE",
        "tipo_demonstracao": "DRE",
        "conta_destino_matriz_id": "vendas_mercadorias",
        "escopo": "MATRIZ",
        "empresa_id": "MATRIZ_GLOBAL",
        "propagar_filiais": True
    }
    res_cad = client.post("/api/plano-contas", json=conta_restauracao)
    assert res_cad.status_code == 200
    assert len(res_cad.json()["plano_contas"]) > 0
