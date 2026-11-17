import concurrent.futures
import math
import os
import statistics
import time
import uuid
import requests

# Mede POSTs novos: chaves únicas. Não confundir repetição idempotente com criação.
def medir(_):
    inicio = time.perf_counter()
    try:
        r = requests.post('http://127.0.0.1:8000/api/v1/pedidos',
            headers={'Authorization': 'Bearer '+os.environ['TOKEN_ANA'],
                     'Idempotency-Key': 'carga-'+str(uuid.uuid4())},
            json={'itens':[{'rid':20,'qtd':1}]}, timeout=10)
        return (time.perf_counter()-inicio)*1000, r.status_code
    except requests.RequestException:
        return (time.perf_counter()-inicio)*1000, 0

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        resultados = list(pool.map(medir, range(100)))
    tempos = sorted(t for t,_ in resultados)
    corretas = sum(s==202 for _,s in resultados)
    rapidas = sum(s==202 and t<=300 for t,s in resultados)
    print({'amostras':len(tempos), 'concorrencia':5,
        'media_ms':round(statistics.mean(tempos),2),
        'p95_ms':round(tempos[math.ceil(.95*len(tempos))-1],2),
        'erros':len(tempos)-corretas, 'sucessos_ate_300ms_percentual':rapidas})
