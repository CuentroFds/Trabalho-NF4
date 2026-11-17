# NF4 — Loja Cerrado: laboratório de sistemas, segurança e integração

**Atualizações em Sistemas de Informação III — Sistemas de Informação — UniAtenas — 2026/2**

Realize os experimentos e registre os resultados por **linha de comando**, no GitHub Codespaces: `bash`, `curl`, Python, cliente MySQL e Docker Compose. Não é necessário criar interface gráfica, instalar MySQL no computador pessoal ou contratar serviços externos.

## 1. Desafio e escopo

A Loja Cerrado quer receber pedidos por uma API. Requisições repetidas não podem gerar pedidos ou cobranças duplicadas; um cliente não pode consultar o pedido de outro; a indisponibilidade do faturamento não deve bloquear a criação de pedidos. A equipe deverá executar os exemplos, provocar falhas, interpretar os resultados e completar as tarefas indicadas.

O projeto contém API, MySQL, outbox, worker e faturamento simulado. Execute os fluxos disponíveis, implemente as melhorias indicadas e observe como o sistema se comporta diante de erros e requisições concorrentes.

## 2. Passo a passo inicial

### 2.1 Acessar o ambiente

Abra um Codespace deste repositório e utilize o terminal integrado. Se já estiver no ambiente, continue em “Conferir diretório e ferramentas”. Mantenha `.env`, backups e tokens fora do Git.

### 2.2 Entrar no Codespaces pela linha de comando

No terminal do computador pessoal, com GitHub CLI instalado e conta autenticada:

```bash
gh auth login
# Substitua ORGANIZACAO/REPOSITORIO pelo nome deste repositório no GitHub.
gh codespace create -r ORGANIZACAO/REPOSITORIO -b main
gh codespace list
gh codespace ssh
```

O último comando permite selecionar o ambiente criado. Se o Codespace já estiver aberto, use seu terminal e continue. A criação está sujeita às permissões e à disponibilidade da conta GitHub. Ao terminar a aula, pare o ambiente: em seu terminal pessoal, `gh codespace stop`.

### 2.3 Conferir diretório e ferramentas

**Dentro do Codespace**, na raiz do repositório:

```bash
pwd
ls
python3 --version
docker version
docker compose version
bash scripts/preparar.sh
```

`preparar.sh` cria quatro tokens aleatórios em `.env` apenas se esse arquivo ainda não existir. Se o arquivo tiver sido criado copiando `.env.example`, substitua os valores `gerar` por tokens aleatórios distintos antes de prosseguir. Preferencialmente deixe o script criá-lo.

Se `docker version` não conseguir conectar ao daemon, confira a conclusão da criação do dev container; resolva a conexão com o daemon antes de iniciar os serviços. O projeto inclui a configuração Docker-in-Docker. Depois de alterar essa configuração em um Codespace já criado, reconstrua o dev container.

### 2.4 Subir os serviços

```bash
docker compose up -d --build --wait
docker compose ps
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

Resultado esperado do último comando: `{"status":"ok"}`. O primeiro build precisa baixar imagens e dependências. Se houver falha:

```bash
docker compose logs --tail=80 db api worker faturamento
```

As credenciais do MySQL são **fictícias e exclusivas do laboratório**, declaradas em `dados/02_extensoes.sql`. O banco e o faturamento não publicam portas no Codespace; a API publica somente em `127.0.0.1:8000`. Não habilite encaminhamento público. Esses cuidados não transformam o protótipo em ambiente de produção.

### 2.5 Carregar tokens no terminal e instalar ferramentas de teste

```bash
set -a
source .env
set +a
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mkdir -p evidencias
python -m pip freeze > evidencias/versoes-python.txt
docker compose images > evidencias/imagens.txt
```

Repita `source .venv/bin/activate` e o carregamento de `.env` quando abrir outro terminal. Não use `set -x`, não grave `env` e não salve os tokens no relatório.

### 2.6 Conferir o banco fornecido

```bash
bash scripts/mysql.sh loja_cerrado <<'SQL'
SELECT 'CLIENTE' tabela,COUNT(*) n FROM CLIENTE
UNION ALL SELECT 'PEDIDO',COUNT(*) FROM PEDIDO
UNION ALL SELECT 'PRODUTO',COUNT(*) FROM PRODUTO
UNION ALL SELECT 'ITEM',COUNT(*) FROM ITEM
UNION ALL SELECT 'CLIENTE_PF',COUNT(*) FROM CLIENTE_PF
UNION ALL SELECT 'CLIENTE_PJ',COUNT(*) FROM CLIENTE_PJ
UNION ALL SELECT 'ENDERECO_ENTREGA',COUNT(*) FROM ENDERECO_ENTREGA;
SQL
```

Antes dos experimentos, espere **5, 5, 5, 9, 4, 1 e 3** registros, respectivamente. A carga original foi preservada. Novos pedidos passam a usar `AUTO_INCREMENT` a partir de 1000; não use `MAX(pid)+1`.

Os arquivos em `dados/` são executados automaticamente **somente na inicialização de um volume vazio**. Alterar um SQL e reiniciar o serviço não reaplica a alteração. Para alterações posteriores, escreva uma migração e execute-a com `scripts/mysql.sh`.

## 3. Entender o que já existe

| Arquivo ou serviço | Responsabilidade |
|---|---|
| `app/api.py` | Autenticação por token de laboratório, RBAC, propriedade do pedido, contrato v1 |
| `app/regras.py` | Validação de itens, resumo do conteúdo e algoritmo de notas |
| `app/db.py` | Conexão, commit, rollback e fechamento |
| `app/worker.py` | Consumo da outbox com lease, retries limitados e estado MORTO |
| `app/pagamento.py` | Interface `Processavel`, implementação HTTP e implementação falsa |
| `app/faturamento.py` | Serviço HTTP interno de cobrança fictícia e deduplicação persistente |
| `dados/01_loja_cerrado.sql` | Esquema e registros originais |
| `dados/02_extensoes.sql` | Tabelas adicionais e contas de banco separadas |
| `scripts/` | Preparação, SQL, backup, restauração, integração e medição |
| `labs/ia_iot.py` | Dados sintéticos de IA e eventos de sensor |
| `tests/` | Testes iniciais para ampliar |
| `docs/relatorio.md` | Registro dos experimentos |

Extensões: `PRECO_ATUAL`, `REQUISICAO`, `OUTBOX`, `COBRANCA_SIMULADA` e `AUDITORIA`. A base original não tem estoque, data de venda nem preço corrente no produto. O preço histórico continua em `ITEM.preco`; a API busca o preço atual no servidor. Não aceite preço ou identidade de cliente no corpo da compra.

**Fronteira do protótipo:** não implementa reserva de estoque nem muda automaticamente o status do pedido após a cobrança. Um pedido novo continua `PENDENTE`; cobrança e entrega do evento têm estados próprios. `ENVIADO` significa que o faturamento respondeu, inclusive quando recusou. Atualização do pedido e compensação de estoque são tarefas opcionais, com migração explícita.

Três camadas no laboratório: apresentação = cliente `curl`; aplicação = API, worker e faturamento; dados = MySQL. Serviços distintos compartilham a mesma instância MySQL por simplicidade didática, com permissões diferentes. Isso cria um ponto único de falha.

## 4. Identidade, RBAC, autorização e dados pessoais

Execute e anote status e justificativa:

```bash
# Sem identidade: 401.
curl -s -i http://127.0.0.1:8000/api/v1/pedidos/101
# Um perfil enviado pelo cliente não autentica: 401.
curl -s -i -H 'X-Usuario-ID: 1' -H 'X-Perfil: gestor' \
  http://127.0.0.1:8000/api/v1/indicadores
# Ana pode consultar o seu pedido 101: 200.
curl -s -i -H "Authorization: Bearer $TOKEN_ANA" \
  http://127.0.0.1:8000/api/v1/pedidos/101
# Ana não pode consultar o pedido 103 de Bruno: 403.
curl -s -i -H "Authorization: Bearer $TOKEN_ANA" \
  http://127.0.0.1:8000/api/v1/pedidos/103
# Declarar outro perfil não eleva o privilégio do token de Ana: 403.
curl -s -i -H "Authorization: Bearer $TOKEN_ANA" -H 'X-Perfil: gestor' \
  http://127.0.0.1:8000/api/v1/indicadores
# Gestor consulta indicadores: 200.
curl -s -i -H "Authorization: Bearer $TOKEN_GESTOR" \
  http://127.0.0.1:8000/api/v1/indicadores
```

Resultado inicial dos indicadores: **3 pedidos concluídos e R$ 2.420,00**. O `COUNT(DISTINCT p.pid)` evita contar linhas de itens como pedidos. Novos pedidos pendentes não alteram esse indicador.

### Experimentos e implementações

1. Monte uma matriz de permissões: cliente consulta apenas seus pedidos e cria pedidos; gestor consulta pedidos e indicadores; worker envia eventos; faturamento registra cobranças.
2. Inspecione o privilégio da conta da API e prove que ela não lê CPF:

```bash
bash scripts/mysql.sh -e "SHOW GRANTS FOR 'api_lab'@'%';"
docker compose exec -T db sh -c \
  'MYSQL_PWD=api_local mysql -uapi_lab loja_cerrado -e "SELECT cpf FROM CLIENTE_PF"'
```

O segundo comando deve falhar por falta de permissão. Explique por que RBAC na aplicação e `GRANT` no banco são controles diferentes. O script administrativo usa root apenas para preparar e investigar o laboratório; a API não usa root.

3. Faça um inventário de `nome`, `cidade`, `cpf`, `cnpj`, `contato`, `logradouro`, pedidos e logs: finalidade, classificação, necessidade, acesso e retenção proposta. Os identificadores da carga são fictícios. CNPJ de uma organização não equivale automaticamente a dado pessoal, mas contato e outros campos podem identificar pessoas naturais.
4. **Implemente** `PATCH /api/v1/clientes/me` para corrigir `cidade`. Identidade vem do token, nunca de um `cid` arbitrário. Valide string não vazia de até 100 caracteres; use SQL parametrizado; grave correção e auditoria na mesma transação. Não grave valor antigo/novo no log. Crie uma migração com privilégio `UPDATE(cidade)` para a conta da API. Teste Ana corrigindo a própria cidade e tentativa de alterar a de Bruno. Documente quem validaria a solicitação em um processo real.
5. Leia os logs e verifique que não há Authorization, corpo completo, CPF ou endereço:

```bash
docker compose logs --no-color api > evidencias/api.log
bash scripts/mysql.sh loja_cerrado -e 'SELECT ator,acao,recurso,instante FROM AUDITORIA ORDER BY id;'
```

Logs técnicos e trilha de auditoria têm finalidades distintas. Proponha revisão de acessos, retenção, destino centralizado e restrições de escrita; a tabela local não é uma trilha imutável.

## 5. Diagnóstico por camada: DNS, TCP, TLS e HTTP

Instale ferramentas de terminal no Codespace, caso ausentes:

```bash
sudo apt-get update
sudo apt-get install -y dnsutils netcat-openbsd openssl
```

### Experimento local

```bash
nc -vz 127.0.0.1 8000
curl -s -i http://127.0.0.1:8000/rota-inexistente
curl -s -i http://127.0.0.1:8000/health
```

Porta aberta demonstra conectividade TCP, não autenticação nem saúde funcional completa. `404` significa que houve resposta HTTP para um caminho não encontrado; não é erro de DNS. No acesso por IP local não há resolução DNS pública, e o endpoint local usa HTTP sem TLS.

### Experimento HTTPS externo, sem tokens da atividade

```bash
nslookup docs.github.com
nc -vz docs.github.com 443
openssl s_client -connect docs.github.com:443 -servername docs.github.com \
  -verify_return_error -verify_hostname docs.github.com </dev/null
curl --http1.1 -I --max-time 15 https://docs.github.com
```

Registre DNS, conexão TCP, validação do certificado e status HTTP separadamente. `--http1.1` permite observar o modelo HTTP/TLS/TCP utilizado neste experimento; outras versões podem usar outro transporte. Se a rede bloquear saída, registre a limitação; não invente resultados e não desative a validação de certificado com `-k`.

**Tarefa:** escreva um diagnóstico para cada caso: nome inexistente; conexão recusada; certificado inválido; HTTP 401; HTTP 403; HTTP 404; HTTP 503. Explique por que `ping` não resolve todos esses diagnósticos.

## 6. Contrato HTTP, SQL parametrizado e evolução

| Operação | Permissão | Contrato inicial |
|---|---|---|
| `GET /health` | Sem token | 200 se consulta simples ao banco funcionar; 503 em falha de banco |
| `GET /api/v1/produtos?categoria=...` | Cliente/gestor | 200; coleção `produtos`; ordem por `rid` |
| `GET /api/v1/pedidos/{pid}` | Dono/gestor | 200, 403 ou 404; preço decimal serializado como string |
| `GET /api/v1/indicadores` | Gestor | 200; pedidos concluídos e faturamento |
| `POST /api/v1/pedidos` | Cliente | `itens` com `rid` e `qtd`; header `Idempotency-Key` obrigatório |
| Mesmo POST novo | Cliente | 202: pedido persistido, faturamento pendente |
| Mesmo POST e mesma chave | Mesmo cliente | 200: mesmo pid, `repetido=true` |
| Mesma chave e outro conteúdo | Mesmo cliente | 409 |
| Corpo inválido/produto inexistente | Cliente | 400 e nenhuma transação parcial |

A chave é sensível a maiúsculas/minúsculas, limitada a 64 caracteres e associada ao cliente. O exemplo não implementa expiração dessas chaves.

```bash
curl -s --get -H "Authorization: Bearer $TOKEN_ANA" \
  --data-urlencode 'categoria=Informatica' \
  http://127.0.0.1:8000/api/v1/produtos
curl -s --get -H "Authorization: Bearer $TOKEN_ANA" \
  --data-urlencode "categoria=' OR 1=1 -- " \
  http://127.0.0.1:8000/api/v1/produtos
```

O primeiro comando retorna três produtos. O segundo deve retornar coleção vazia: a entrada é um **valor**, não parte da sintaxe SQL. Faça também um teste com apóstrofo isolado. Não é preciso criar uma aplicação pública vulnerável.

**Tarefa de evolução:** acrescente paginação opcional sem renomear `produtos`, preservando o comportamento quando os parâmetros não forem enviados; limite o tamanho de página. Acrescente teste para o consumidor antigo. Proponha v2 para uma mudança incompatível e registre política de migração. Parâmetros SQL protegem valores; nomes de colunas dinâmicos precisam de lista permitida.

## 7. Repetições, fila durável e falhas parciais

### 7.1 Criar e repetir

```bash
curl -s -i -X POST http://127.0.0.1:8000/api/v1/pedidos \
  -H "Authorization: Bearer $TOKEN_ANA" \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: aula-001' \
  -d '{"itens":[{"rid":10,"qtd":1},{"rid":20,"qtd":2}]}'
```

Repita o comando: mesmo `pid`, uma linha em `REQUISICAO`, um evento em `OUTBOX`. Use a mesma chave e mude a quantidade: espere 409. Para um pedido realmente novo, use outra chave.

```bash
bash scripts/mysql.sh loja_cerrado -e \
  'SELECT * FROM REQUISICAO; SELECT * FROM OUTBOX; SELECT * FROM COBRANCA_SIMULADA;'
python scripts/integracao.py
```

O teste de integração envia duas requisições concorrentes com a mesma chave. As respostas devem conter o mesmo pid, com status 200 e 202. A unicidade está no banco, portanto também vale entre processos da API; uma variável Python em memória não garantiria isso.

### 7.2 Parar consumidor e continuar produzindo

```bash
docker compose stop worker
curl -s -i -X POST http://127.0.0.1:8000/api/v1/pedidos \
  -H "Authorization: Bearer $TOKEN_ANA" -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: fila-001' -d '{"itens":[{"rid":20,"qtd":1}]}'
bash scripts/mysql.sh loja_cerrado -e 'SELECT id,pid,estado,tentativas FROM OUTBOX;'
docker compose start worker
docker compose logs --tail=30 worker
```

O pedido foi aceito enquanto o consumidor estava parado. Observe novamente a tabela depois de o worker processar. **Nesta implementação a própria OUTBOX é a fila durável**, consultada por polling. Não existe RabbitMQ/Redis nem relay separado já implementado.

Pedido, itens, chave e evento são confirmados **na mesma transação**. Se o processo cair após o commit, o evento continua no banco. Se cair antes do commit, tudo sofre rollback. O worker usa transação curta para reservar o evento, confirma a reserva e só então faz HTTP.

### 7.3 Cobrança criada, resposta perdida

```bash
MODO_FATURAMENTO=lento docker compose up -d --force-recreate faturamento
curl -s -i -X POST http://127.0.0.1:8000/api/v1/pedidos \
  -H "Authorization: Bearer $TOKEN_ANA" -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: timeout-001' -d '{"itens":[{"rid":10,"qtd":1}]}'
docker compose logs -f worker
```

Saia dos logs com Ctrl+C; isso não para os serviços. O faturamento grava a cobrança e demora quatro segundos para responder. O worker desiste da leitura após dois segundos e tenta de novo com o **mesmo evento**. A chave primária `evento_id` impede uma segunda cobrança. O efeito já ocorreu mesmo que o cliente HTTP tenha visto timeout.

Restabeleça o modo normal e confira as tabelas:

```bash
MODO_FATURAMENTO=normal docker compose up -d --force-recreate faturamento
bash scripts/mysql.sh loja_cerrado -e \
  'SELECT id,pid,estado,tentativas,erro FROM OUTBOX; SELECT * FROM COBRANCA_SIMULADA;'
```

Se o evento já esgotou cinco tentativas, ficará `MORTO`. Após investigar e corrigir a causa, anote o ID e reprocesse **o mesmo evento**:

```bash
# Substitua 123 pelo ID observado; não crie uma segunda cobrança manualmente.
bash scripts/mysql.sh loja_cerrado -e \
  "UPDATE OUTBOX SET estado='PENDENTE',tentativas=0,proxima=NOW(6),dono=NULL,lease_ate=NULL WHERE id=123 AND estado='MORTO';"
```

### 7.4 Outros cenários obrigatórios

Repita com `MODO_FATURAMENTO=indisponivel` e depois `MODO_FATURAMENTO=recusado`, sempre com uma chave de pedido nova. Restaure `normal` ao final.

| Cenário | Observação esperada |
|---|---|
| Indisponível | HTTP 503 interno, backoff, no máximo cinco tentativas e possível estado MORTO |
| Recusado | Cobrança simulada RECUSADO, evento ENVIADO; não retentar recusa comercial |
| Lento | Timeout pode ocorrer depois do efeito; uma cobrança por evento |
| Worker encerrado após reserva | Lease expira em 30 s; outro consumidor pode retomar |

Execute `docker compose kill -s SIGKILL worker`, seguido de `docker compose up -d worker`, durante um processamento lento e observe a recuperação. O momento do kill afeta o resultado; documente o estado efetivamente observado.

**Atividades:**

1. Explique o papel do lease, do `dono`, de `SKIP LOCKED` e da unicidade no faturamento. Não prometa entrega “exatamente uma vez”: há repetição de entrega e deduplicação do efeito persistente.
2. Acrescente teste automatizado para falha no meio da criação: produto inexistente deve deixar o total de pedidos e eventos inalterado.
3. Diferencie falhas retentáveis (rede/503) e definitivas (payload inválido/409). O worker inicial retenta qualquer erro HTTP; melhore a classificação e registre o motivo sem dados pessoais.
4. Proponha como manter o resultado de pagamento no pedido, sem chamar serviço externo dentro da transação e sem violar os estados permitidos.
5. Desenhe a extensão com **relay → broker → worker**: o relay lê eventos persistidos, publica e aguarda confirmação durável antes de marcar a publicação; pode republicar após crash. O consumidor confirma a mensagem depois de registrar o efeito; também pode recebê-la novamente. A chave deve atravessar todos os componentes. Registre como a publicação, a confirmação e a deduplicação se comportam quando um componente falha. A implementação de um broker é uma extensão opcional.

## 8. Backup, restauração, RTO e RPO

Considere as seguintes metas para a Loja Cerrado: **RTO de 2 horas e RPO de 15 minutos**. Compare os resultados dos experimentos e o procedimento proposto com essas metas.

```bash
bash scripts/backup.sh
ARQUIVO=$(cat backups/ultimo.txt)
bash scripts/restaurar.sh "$ARQUIVO" | tee evidencias/restauracao.txt
```

O dump não inclui `CREATE DATABASE`/`USE`; a restauração importa em **uma base nova**. O script verifica checksum e mede o tempo de restauração SQL. Confira também contagens, somas e chaves específicas na base nova, usando o nome exibido. Valide especialmente `REQUISICAO`, `OUTBOX` e cobranças, pois afetam a recuperação da idempotência.

**Experimento de perda:** faça backup, crie um novo pedido, restaure aquele backup e prove que o novo pid não existe na cópia. Registre horários UTC do início do backup, da criação e do incidente simulado. A diferença entre o instante do incidente e o último ponto recuperável é a janela de perda, não o tempo gasto restaurando.

**Análise dos resultados:**

- Separe tempo de restore SQL, validação, reconfiguração e retorno dos consumidores. A soma, desde o incidente, é que deve ser comparada ao RTO.
- Proponha política para RPO de 15 min: backups/PITR, frequência e atraso máximo de transporte, monitoramento e teste. Um cron a cada 15 min sozinho não garante a meta se houver falhas ou atraso.
- Explique por que `backups/` no mesmo Codespace não é cópia isolada ou imutável e pode desaparecer junto com o ambiente. Proponha destino independente, acesso restrito, credenciais separadas, retenção, criptografia em repouso e exercício de restauração.
- Não confunda checksum com criptografia, réplica com backup ou restore rápido de uma base pequena com comprovação de atendimento à meta em produção.
- Depois de restaurar uma base para um instante anterior, reconcilie efeitos externos já realizados. A cobrança pode existir no provedor mesmo que o registro local tenha sido perdido.

## 9. Requisitos não funcionais e latência

Com o ambiente normal e os tokens exportados:

```bash
python scripts/latencia.py | tee evidencias/latencia.txt
docker compose logs --no-color api > evidencias/api.log
```

São 100 **novos pedidos**, cinco clientes concorrentes, cada POST com chave única. O p95 usa o método de posto mais próximo. O script informa erros e a porcentagem de chamadas bem-sucedidas em até 300 ms. Erros também ficam na distribuição total; rapidez de falhas não conta como sucesso.

**Tarefa:** registre recursos do Codespace, carga, aquecimento, tamanho da amostra e resultados. Compare worker ativo/parado e faturamento normal/lento. A criação assíncrona retorna 202 antes do faturamento; a latência de aceitação não é o tempo até cobrança concluída. Acrescente uma métrica de idade do evento pendente e uma de erros de integração.

Não declare a meta cumprida apenas porque uma chamada levou 20 ms. A amostra pequena descreve as condições deste experimento; amplie a carga antes de concluir sobre a capacidade do serviço.

## 10. Arquitetura, escala e limites de confiança

Inspecione e aumente apenas os consumidores:

```bash
docker compose ps
docker compose top
docker compose up -d --scale worker=2
```

Compare drenagem da fila com um e dois workers e verifique ausência de duplicações. Retorne com `docker compose up -d --scale worker=1`.

**Registre em `docs/relatorio.md` uma descrição ou diagrama** com:

1. Cliente `curl` (representando o navegador), gateway/balanceador, API, banco, outbox/relay, broker, worker e faturamento.
2. Três camadas e limites de confiança. O cliente nunca escolhe seu papel de acesso nem acessa o banco diretamente.
3. TLS no acesso público e nos enlaces internos necessários; validação de certificados; autenticação entre serviços; criptografia em repouso. O HTTP interno deste laboratório não demonstra esses controles.
4. Validação de identidade e autorização na API, mesmo depois do gateway. Tokens estáticos de laboratório devem ser substituídos por gestão de identidade com expiração/revogação.
5. API replicada atrás do balanceador e workers replicados; estado compartilhado e deduplicação persistente. O Compose atual fixa a porta 8000: **não basta executar `--scale api=2`**; seria necessário retirar a porta fixa das réplicas e acrescentar balanceador.
6. Pontos únicos de falha e limites do banco. Dois processos gunicorn não são dois servidores independentes.

Explique VM × contêiner e Compose local × orquestração de cluster. Este laboratório não executa cluster, escalonamento multinó nem alta disponibilidade. Descreva como um orquestrador trataria falha de instância, probes e réplicas.

## 11. Algoritmos e orientação a interfaces

```bash
python -c 'from app.regras import analisar_notas; print(analisar_notas([7,8,6,9]))'
python -m pytest -q
```

Resultado das notas: média 7,5; duas notas estritamente maiores que 7. Explique **O(n)** de tempo e **O(1)** de espaço auxiliar, sem contar a lista de entrada. Um laço não significa tempo constante. Valide fronteiras: 7 não conta; lista de um elemento; lista vazia.

Leia `Processavel`, `PagamentoHTTP`, `PagamentoFalso` e `executar_pagamento`. O serviço depende do contrato `processar`, permitindo trocar a implementação. **Implemente** `PagamentoRecusadoFalso` e escreva teste sem rede nem MySQL. Explique por que uma interface facilita testes, mas não elimina a necessidade deles.

## 12. CI, artefato e entrega controlada

```bash
ruff check app labs scripts tests --select E9,F63,F7,F82
python -m pytest -q
python scripts/integracao.py
git status --short
```

O workflow `.github/workflows/ci.yml` faz análise estática básica, testes unitários, inicialização dos serviços, teste de integração e exportação da imagem Docker em artefato identificado pelo commit. Não publica nem implanta em serviço externo.

Depois de revisar os arquivos:

```bash
git add app dados scripts labs tests docs README.md requirements.txt Dockerfile compose.yaml .github .devcontainer .gitignore .dockerignore .env.example
git commit -m "Implementa atividades e evidencias NF4"
git push
# Se gh estiver disponível/autenticado no ambiente:
gh run list
gh run view --log-failed
```

Não adicione `.env` nem dumps. O `.gitignore` exclui `evidencias/` por padrão. Revise os registros e remova segredos antes de compartilhá-los.

**Tarefa de projeto:** escreva um procedimento de deploy gradual: mesma imagem identificada pelo commit, pequeno percentual de tráfego para a nova versão, verificação de saúde, comparação de erros e p95, expansão ou rollback para a imagem anterior. Defina limiares e janela de observação. Explique por que recriar a imagem a cada estágio prejudica a rastreabilidade e por que voltar o código não desfaz automaticamente uma migração incompatível.

O workflow fornece CI e artefato; implantação gradual e rollback são **procedimentos a projetar**, não funcionalidades já executadas neste Codespace.

## 13. IA, IoT e dados em escala

```bash
python labs/ia_iot.py | tee evidencias/ia-iot.txt
```

O script usa saídas sintéticas de um classificador: grupo A com erro de 25%, grupo B com erro de 75%, quatro casos por grupo. Não há modelo treinado nem evidência estatística suficiente para concluir discriminação real.

**IA:** explique limitações da amostra, representatividade, qualidade de rótulos, falsos positivos/negativos e impacto humano. Acrescente contagens por grupo e discuta revisão humana e monitoramento após implantação. Um resultado agregado pode esconder diferenças entre grupos; também não basta olhar uma única métrica.

**IoT:** espere evento normal, alerta de temperatura, duplicado e rejeitado por valor inválido. Cada evento tem ID, sensor, instante com fuso, valor e unidade.

**Implemente:** persistência de eventos e dos IDs de deduplicação; teste que reiniciar o programa não aceita novamente o mesmo evento; acrescente detecção de sensor sem comunicação e registro de eventos rejeitados. O conjunto `vistos` inicial só funciona durante uma execução.

**Desenhe para escala:** sensores → ingestão autenticada → fila/stream → armazenamento particionado → processamento/indicadores, com validação de esquema, origem e timestamp. Explique lote × fluxo, atraso, ordem e deduplicação. Um script com quatro registros não é uma plataforma Big Data.

## 14. Registro dos experimentos

Atualize `docs/relatorio.md` ao longo do laboratório com:

- Comandos, versões, resultados observados e alterações realizadas.
- Matriz de acesso, inventário de dados e fluxo de correção cadastral.
- Testes de contrato, propriedade de recurso, SQL parametrizado e idempotência concorrente.
- Comportamento da fila, timeouts após cobrança, recusas e recuperação de eventos.
- Procedimento de backup/restauração e comparação com RTO/RPO.
- p95, taxa de erros e limitações da medição.
- Complexidade do algoritmo e substituição da implementação de pagamento.
- Arquitetura proposta, TLS, limites de confiança e escalabilidade.
- Pipeline, artefato e procedimento de implantação gradual e rollback.
- Métricas por grupo e persistência/deduplicação de eventos IoT.

Para interpretar os resultados, responda: o que fazer quando a cobrança é criada, mas a resposta HTTP expira? Como recuperar um evento após uma falha logo depois do commit? Por que um cabeçalho de perfil não pode elevar privilégios? Quais etapas, além da restauração SQL, compõem o tempo de recuperação do serviço?

## 15. Encerramento e problemas frequentes

```bash
# Para serviços preservando o volume de dados:
docker compose down
# Para voltar:
docker compose up -d --wait
```

**Reset destrutivo, apenas quando decidir apagar o laboratório:** `docker compose down -v` remove o volume MySQL deste projeto. Na próxima subida os scripts SQL recriam os dados. Faça backup antes se precisar conservar experimentos. O SQL original também contém `DROP DATABASE`; não o execute em base de trabalho com dados importantes.

| Sintoma | Verificação |
|---|---|
| 401 inesperado | Carregou `.env` neste terminal? Token corresponde ao servidor? |
| 403 | Papel ou proprietário do pedido não permite a ação |
| 409 | Chave já usada com outro corpo; nova intenção exige nova chave |
| 503 da API | `docker compose ps` e logs do banco; não é “erro de DNS” automaticamente |
| Evento MORTO | Corrigir causa e reprocesar o mesmo ID de maneira controlada |
| Editou Python, mas comportamento não mudou | `docker compose up -d --build`; código está dentro da imagem |
| Editou SQL, mas tabela não mudou | Volume existente não reexecuta init; aplicar migração |
| API não sobe por porta ocupada | Identificar processo em 8000; encerrar serviço antigo ou alterar mapeamento e comandos |
| Dependências/imagens não baixam | Verificar conectividade e permissões do Codespace |

## 16. Referências oficiais

A instalação depende de conectividade aos registros de imagens e pacotes. Utilize a documentação correspondente às versões executadas no ambiente.

- GitHub Codespaces pelo CLI: https://docs.github.com/pt/codespaces/developing-in-a-codespace/using-github-codespaces-with-github-cli
- Configuração Python e dev containers: https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/setting-up-your-python-project-for-codespaces
- Docker Compose e healthchecks: https://docs.docker.com/compose/how-tos/startup-order/
- MySQL, locks e SKIP LOCKED: https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html
- Testes Flask: https://flask.palletsprojects.com/en/stable/testing/
- LGPD, texto atualizado, especialmente arts. 6º, 18 e 46: https://www2.camara.leg.br/legin/fed/lei/2018/lei-13709-14-agosto-2018-787077-normaatualizada-pl.html
