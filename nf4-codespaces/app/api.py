import hmac
import json
import logging
import os
import re
import time
import uuid
from functools import wraps
import pymysql
from flask import Flask, g, request
from app.db import conexao
from app.regras import resumo, validar_itens

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16384
logging.basicConfig(level=logging.INFO, format="%(message)s")

def identidade(token):
    # Credenciais opacas de laboratório, armazenadas no servidor.
    # Não representam login, expiração, MFA ou gestão de sessões de produção.
    for variavel, ator in [("TOKEN_ANA", {"uid": "ana", "cid": 1, "papel": "cliente"}),
                          ("TOKEN_BRUNO", {"uid": "bruno", "cid": 2, "papel": "cliente"}),
                          ("TOKEN_GESTOR", {"uid": "gestor", "cid": None, "papel": "gestor"})]:
        segredo = os.getenv(variavel, "")
        if segredo and hmac.compare_digest(token, segredo):
            return ator
    return None

def permitir(*papeis):
    def decorar(funcao):
        @wraps(funcao)
        def executar(*args, **kwargs):
            cabecalho = request.headers.get("Authorization", "")
            g.ator = identidade(cabecalho[7:]) if cabecalho.startswith("Bearer ") else None
            if not g.ator:
                return {"erro": "Não autenticado"}, 401
            if g.ator["papel"] not in papeis:
                return {"erro": "Acesso negado"}, 403
            return funcao(*args, **kwargs)
        return executar
    return decorar

@app.before_request
def iniciar():
    g.inicio = time.perf_counter()
    g.request_id = str(uuid.uuid4())

@app.after_request
def registrar(resposta):
    logging.info(json.dumps({"request_id": g.request_id, "metodo": request.method,
        "rota": str(request.url_rule), "status": resposta.status_code,
        "ms": round(1000 * (time.perf_counter() - g.inicio), 3),
        "ator": getattr(g, "ator", {}).get("uid") if getattr(g, "ator", None) else None}))
    resposta.headers["X-Request-ID"] = g.request_id
    return resposta

@app.errorhandler(pymysql.MySQLError)
def erro_banco(_erro):
    return {"erro": "Banco indisponível ou conflito; tente novamente", "request_id": g.request_id}, 503

@app.get("/health")
def health():
    with conexao() as db, db.cursor() as cur:
        cur.execute("SELECT 1")
    return {"status": "ok"}

@app.get("/api/v1/produtos")
@permitir("cliente", "gestor")
def produtos():
    categoria = request.args.get("categoria")
    if categoria and len(categoria) > 100:
        return {"erro": "Categoria longa demais"}, 400
    with conexao() as db, db.cursor() as cur:
        sql = "SELECT rid,descricao,categoria FROM PRODUTO"
        parametros = ()
        if categoria is not None:
            sql += " WHERE categoria=%s"
            parametros = (categoria,)
        cur.execute(sql + " ORDER BY rid", parametros)
        return {"produtos": cur.fetchall()}

@app.get("/api/v1/pedidos/<int:pid>")
@permitir("cliente", "gestor")
def pedido(pid):
    with conexao() as db, db.cursor() as cur:
        cur.execute("SELECT pid,cid,status FROM PEDIDO WHERE pid=%s", (pid,))
        registro = cur.fetchone()
        if not registro:
            return {"erro": "Não encontrado"}, 404
        if g.ator["papel"] == "cliente" and registro["cid"] != g.ator["cid"]:
            return {"erro": "Acesso negado"}, 403
        cur.execute("SELECT rid,qtd,preco FROM ITEM WHERE pid=%s ORDER BY rid", (pid,))
        registro["itens"] = cur.fetchall()
        return registro

@app.get("/api/v1/indicadores")
@permitir("gestor")
def indicadores():
    with conexao() as db, db.cursor() as cur:
        cur.execute("""SELECT COUNT(DISTINCT p.pid) pedidos,
            COALESCE(SUM(i.qtd*i.preco),0) faturamento
            FROM PEDIDO p JOIN ITEM i ON i.pid=p.pid WHERE p.status='CONCLUIDO'""")
        return cur.fetchone()

def repeticao(cid, chave, assinatura):
    with conexao() as db, db.cursor() as cur:
        cur.execute("SELECT pid,resumo FROM REQUISICAO WHERE cid=%s AND chave=%s", (cid,chave))
        anterior = cur.fetchone()
    if anterior:
        if anterior["resumo"] != assinatura:
            return {"erro": "Chave já usada com outro conteúdo"}, 409
        return {"pid": anterior["pid"], "repetido": True}, 200
    return None

@app.post("/api/v1/pedidos")
@permitir("cliente")
def criar():
    chave = request.headers.get("Idempotency-Key", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", chave):
        return {"erro": "Idempotency-Key obrigatória: 1 a 64 caracteres alfanuméricos, _ ou -"}, 400
    try:
        itens = validar_itens(request.get_json(silent=True))
    except ValueError as erro:
        return {"erro": str(erro)}, 400
    assinatura, cid = resumo(itens), g.ator["cid"]
    anterior = repeticao(cid, chave, assinatura)
    if anterior:
        return anterior
    try:
        with conexao() as db, db.cursor() as cur:
            cur.execute("INSERT INTO PEDIDO(cid,status) VALUES (%s,'PENDENTE')", (cid,))
            pid = cur.lastrowid
            for item in itens:
                cur.execute("SELECT preco FROM PRECO_ATUAL WHERE rid=%s", (item["rid"],))
                produto = cur.fetchone()
                if not produto:
                    raise ValueError("Produto inexistente")
                cur.execute("INSERT INTO ITEM(pid,rid,qtd,preco) VALUES (%s,%s,%s,%s)",
                            (pid,item["rid"],item["qtd"],produto["preco"]))
            cur.execute("INSERT INTO REQUISICAO(cid,chave,resumo,pid) VALUES (%s,%s,%s,%s)",
                        (cid,chave,assinatura,pid))
            cur.execute("INSERT INTO OUTBOX(pid) VALUES (%s)", (pid,))
            cur.execute("INSERT INTO AUDITORIA(ator,acao,recurso) VALUES (%s,'pedido_criado',%s)",
                        (g.ator["uid"],pid))
        return {"pid": pid, "faturamento": "PENDENTE"}, 202
    except ValueError as erro:
        return {"erro": str(erro)}, 400
    except pymysql.IntegrityError:
        # O contexto já fez rollback, inclusive do pedido da requisição perdedora.
        anterior = repeticao(cid, chave, assinatura)
        if anterior:
            return anterior
        raise
