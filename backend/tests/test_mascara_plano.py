import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
