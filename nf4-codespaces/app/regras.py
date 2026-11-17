import hashlib
import json

def validar_itens(dados):
    if not isinstance(dados, dict) or set(dados) != {"itens"}:
        raise ValueError("Informe somente itens; identidade e preço vêm do servidor")
    itens = dados["itens"]
    if not isinstance(itens, list) or not 1 <= len(itens) <= 20:
        raise ValueError("Informe entre 1 e 20 itens")
    vistos = set()
    for item in itens:
        if not isinstance(item, dict) or set(item) != {"rid", "qtd"}:
            raise ValueError("Cada item exige apenas rid e qtd")
        if type(item["rid"]) is not int or type(item["qtd"]) is not int:
            raise ValueError("rid e qtd devem ser inteiros")
        if item["rid"] <= 0 or not 1 <= item["qtd"] <= 100:
            raise ValueError("rid positivo e qtd entre 1 e 100")
        if item["rid"] in vistos:
            raise ValueError("Produto repetido")
        vistos.add(item["rid"])
    return sorted(itens, key=lambda item: item["rid"])

def resumo(itens):
    return hashlib.sha256(json.dumps(itens, sort_keys=True).encode()).hexdigest()

def analisar_notas(notas):
    # Exercício da Q18: sem ordenar e sem alterar a lista.
    if not notas:
        raise ValueError("Lista vazia")
    soma = 0
    acima = 0
    for nota in notas:
        soma += nota
        if nota > 7:
            acima += 1
    return {"media": soma / len(notas), "acima_de_7": acima}
