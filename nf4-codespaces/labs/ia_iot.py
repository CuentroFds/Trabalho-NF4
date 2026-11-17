import json
from datetime import datetime, timezone

def avaliar_grupos(registros):
    grupos = {}
    for r in registros:
        n, erros = grupos.get(r['grupo'], (0,0))
        grupos[r['grupo']] = n+1, erros+int(r['real'] != r['previsto'])
    return {g:{'n':n,'taxa_erro':erros/n} for g,(n,erros) in grupos.items()}

def validar_evento(e):
    try:
        instante = datetime.fromisoformat(e['instante'].replace('Z','+00:00'))
        return (isinstance(e['evento_id'],str) and bool(e['evento_id'])
            and isinstance(e['sensor_id'],str) and bool(e['sensor_id'])
            and instante.tzinfo is not None and e['unidade']=='C'
            and type(e['valor']) in (int,float) and -50<=e['valor']<=100)
    except (KeyError,TypeError,ValueError,AttributeError):
        return False

if __name__=='__main__':
    dados = [{'grupo':g,'real':1,'previsto':p} for g,previsoes in
        [('A',[1,1,1,0]),('B',[1,0,0,0])] for p in previsoes]
    print('IA: saídas sintéticas de classificador, sem treino:', avaliar_grupos(dados))
    instante = datetime.now(timezone.utc).isoformat()
    eventos = [dict(evento_id='e1',sensor_id='s1',instante=instante,valor=5,unidade='C'),
               dict(evento_id='e2',sensor_id='s1',instante=instante,valor=18,unidade='C'),
               dict(evento_id='e1',sensor_id='s1',instante=instante,valor=5,unidade='C'),
               dict(evento_id='e3',sensor_id='s1',instante=instante,valor=999,unidade='C')]
    vistos=set()
    for e in eventos:
        if not validar_evento(e):
            print('REJEITADO', e['evento_id'])
        elif e['evento_id'] in vistos:
            print('DUPLICADO',e['evento_id'])
        else:
            vistos.add(e['evento_id'])
            print(json.dumps(e), 'ALERTA' if e['valor']>8 else 'OK')
    # TODO aluno: persistir IDs; medir atraso; detectar sensor sem comunicação.
