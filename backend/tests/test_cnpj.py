"""
Testes automatizados da consulta de dados na Receita Federal via CNPJ.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.cnpj_service import formatar_cnpj, consultar_dados_cnpj

client = TestClient(app)

def test_formatar_cnpj():
    assert formatar_cnpj("00000000000191") == "00.000.000/0001-91"
    assert formatar_cnpj("123") == "123"

def test_cnpj_invalido():
    res = consultar_dados_cnpj("12345")
    assert res["sucesso"] is False
    assert "14 números" in res["erro"]

    response = client.get("/api/consultar-cnpj/12345")
    assert response.status_code == 400
    assert response.json()["sucesso"] is False

def test_consulta_cnpj_banco_do_brasil():
    # CNPJ do Banco do Brasil (estável e público na base da Receita)
    response = client.get("/api/consultar-cnpj/00.000.000/0001-91")
    # Caso a máquina tenha acesso externo aos endpoints da Receita
    if response.status_code == 200:
        dados = response.json()
        assert dados["sucesso"] is True
        assert "BANCO DO BRASIL" in dados["razao_social"]
        assert dados["uf"] == "DF"
        assert dados["tipo_unidade"] == "MATRIZ"
