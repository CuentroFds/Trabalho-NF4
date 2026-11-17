import os
import concurrent.futures
import uuid
import requests
base='http://127.0.0.1:8000'
h={'Authorization':'Bearer '+os.environ['TOKEN_ANA']}
assert requests.get(base+'/api/v1/pedidos/101',headers=h,timeout=5).status_code==200
assert requests.get(base+'/api/v1/pedidos/103',headers=h,timeout=5).status_code==403
chave='teste-'+str(uuid.uuid4())
h['Idempotency-Key']=chave
corpo={'itens':[{'rid':20,'qtd':1}]}
def enviar(_):
    return requests.post(base+'/api/v1/pedidos',headers=h,json=corpo,timeout=10)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    respostas=list(pool.map(enviar,range(2)))
assert sorted(r.status_code for r in respostas)==[200,202], [(r.status_code,r.text) for r in respostas]
assert respostas[0].json()['pid']==respostas[1].json()['pid']
corpo['itens'][0]['qtd']=2
assert requests.post(base+'/api/v1/pedidos',headers=h,json=corpo,timeout=5).status_code==409
print('Integração OK: propriedade do pedido, concorrência e conflito de chave')
