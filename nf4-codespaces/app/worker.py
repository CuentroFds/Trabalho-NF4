import time
import uuid
import pymysql
import requests
from app.db import conexao
from app.pagamento import PagamentoHTTP, executar_pagamento

# Outbox funciona como fila durável neste protótipo, sem broker separado.
# Lease + comparação de dono evita confirmação por worker que perdeu a posse.
def uma_vez():
    dono = str(uuid.uuid4())
    with conexao() as db, db.cursor() as cur:
        cur.execute("""SELECT id,pid,tentativas FROM OUTBOX
          WHERE (estado='PENDENTE' AND proxima<=NOW(6))
             OR (estado='PROCESSANDO' AND lease_ate<NOW(6))
          ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED""")
        evento = cur.fetchone()
        if not evento:
            return False
        if evento["tentativas"] >= 5:
            cur.execute("UPDATE OUTBOX SET estado='MORTO' WHERE id=%s", (evento["id"],))
            return True
        cur.execute("""UPDATE OUTBOX SET estado='PROCESSANDO',dono=%s,
          lease_ate=DATE_ADD(NOW(6),INTERVAL 30 SECOND),tentativas=tentativas+1 WHERE id=%s""",
          (dono,evento["id"]))
        cur.execute("SELECT SUM(qtd*preco) valor FROM ITEM WHERE pid=%s", (evento["pid"],))
        valor = str(cur.fetchone()["valor"])
    # COMMIT acontece antes da chamada externa, sem reter locks de banco.
    erro = None
    try:
        executar_pagamento(PagamentoHTTP(), {"evento_id": evento["id"], "pid": evento["pid"], "valor": valor})
    except (requests.RequestException, ValueError):
        erro = "falha_integracao"
    with conexao() as db, db.cursor() as cur:
        if erro:
            estado = "MORTO" if evento["tentativas"] + 1 >= 5 else "PENDENTE"
            atraso = 2 ** (evento["tentativas"] + 1)
            cur.execute("""UPDATE OUTBOX SET estado=%s,erro=%s,
              proxima=DATE_ADD(NOW(6),INTERVAL %s SECOND),lease_ate=NULL
              WHERE id=%s AND dono=%s AND estado='PROCESSANDO'""",
              (estado,erro,atraso,evento["id"],dono))
        else:
            cur.execute("""UPDATE OUTBOX SET estado='ENVIADO',erro=NULL,lease_ate=NULL
              WHERE id=%s AND dono=%s AND estado='PROCESSANDO'""", (evento["id"],dono))
    print({"evento": evento["id"], "resultado": erro or "enviado"}, flush=True)
    return True

if __name__ == "__main__":
    while True:
        try:
            if not uma_vez():
                time.sleep(1)
        except pymysql.MySQLError:
            print({"erro": "banco_indisponivel"}, flush=True)
            time.sleep(3)
