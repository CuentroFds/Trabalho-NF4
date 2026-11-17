import pytest
from app.api import app
from app.regras import analisar_notas, resumo, validar_itens
from app.pagamento import PagamentoFalso, executar_pagamento

def test_notas():
    notas=[7,8,6,9]
    assert analisar_notas(notas)=={'media':7.5,'acima_de_7':2}
    assert notas==[7,8,6,9]
    with pytest.raises(ValueError):
        analisar_notas([])

@pytest.mark.parametrize('dados', [None,{}, {'itens':[]}, {'itens':[{'rid':10,'qtd':True}]},
    {'itens':[{'rid':10,'qtd':0}]}, {'itens':[{'rid':10,'qtd':1,'preco':0}]},
    {'itens':[{'rid':10,'qtd':1},{'rid':10,'qtd':2}]}])
def test_validacao(dados):
    with pytest.raises(ValueError):
        validar_itens(dados)

def test_resumo_normalizado():
    a={'itens':[{'rid':20,'qtd':1},{'rid':10,'qtd':2}]}
    b={'itens':list(reversed(a['itens']))}
    assert resumo(validar_itens(a))==resumo(validar_itens(b))

def test_cabecalho_forjado_nao_autentica():
    r=app.test_client().get('/api/v1/indicadores',headers={'X-Perfil':'gestor','X-Usuario-ID':'1'})
    assert r.status_code==401

def test_papel_conferido_no_servidor(monkeypatch):
    monkeypatch.setenv('TOKEN_ANA','token_teste')
    r=app.test_client().get('/api/v1/indicadores',headers={'Authorization':'Bearer token_teste','X-Perfil':'gestor'})
    assert r.status_code==403

def test_interface_substituivel():
    assert executar_pagamento(PagamentoFalso(),{'evento_id':7})['estado']=='APROVADO'
