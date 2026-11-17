from typing import Protocol
import os
import requests

class Processavel(Protocol):
    def processar(self, evento: dict) -> dict: ...

class PagamentoHTTP:
    def processar(self, evento: dict) -> dict:
        resposta = requests.post("http://faturamento:8001/cobrancas", json=evento,
            headers={"Authorization": "Bearer " + os.environ["TOKEN_SERVICO"]}, timeout=(1,2))
        resposta.raise_for_status()
        return resposta.json()

class PagamentoFalso:
    def processar(self, evento: dict) -> dict:
        return {"evento_id": evento["evento_id"], "estado": "APROVADO"}

def executar_pagamento(porta: Processavel, evento: dict) -> dict:
    return porta.processar(evento)
