import hmac
import os
import time
import pymysql
from flask import Flask, request
from app.db import conexao

app = Flask(__name__)

@app.post("/cobrancas")
def cobrar():
    segredo = os.getenv("TOKEN_SERVICO", "")
    if not segredo or not hmac.compare_digest(request.headers.get("Authorization", ""), "Bearer " + segredo):
        return {"erro": "Não autenticado"}, 401
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or type(dados.get("evento_id")) is not int or type(dados.get("pid")) is not int:
        return {"erro": "Evento inválido"}, 400
    # Mock interno: valor é calculado pelo worker. Falta validação monetária robusta (extensão).
    from decimal import Decimal, InvalidOperation
    try:
        valor = Decimal(str(dados.get("valor")))
        if not valor.is_finite() or valor < 0 or valor > Decimal("9999999999.99"):
            raise ValueError()
    except (InvalidOperation, ValueError):
        return {"erro": "Valor inválido"}, 400
    modo = os.getenv("MODO_FATURAMENTO", "normal")
    if modo == "indisponivel":
        return {"erro": "Falha simulada"}, 503
    estado = "RECUSADO" if modo == "recusado" else "APROVADO"
    try:
        with conexao() as db, db.cursor() as cur:
            cur.execute("INSERT INTO COBRANCA_SIMULADA(evento_id,pid,valor,estado) VALUES (%s,%s,%s,%s)",
                        (dados["evento_id"],dados["pid"],valor,estado))
    except pymysql.IntegrityError:
        pass  # Conferir conteúdo é obrigatório antes de responder à repetição.
    with conexao() as db, db.cursor() as cur:
        cur.execute("SELECT evento_id,pid,valor,estado FROM COBRANCA_SIMULADA WHERE evento_id=%s", (dados["evento_id"],))
        registro = cur.fetchone()
    if not registro or registro["pid"] != dados["pid"] or registro["valor"] != valor:
        return {"erro": "Identificador reutilizado com outro conteúdo"}, 409
    # Simula efeito confirmado e resposta perdida por timeout: o retry não recobra.
    if modo == "lento":
        time.sleep(4)
    return registro, 200
