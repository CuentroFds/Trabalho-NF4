# Validação do material

Preparação: 17/11/2026.

- 12 testes unitários aprovados com Python 3.12.14.
- Ruff, seleção E9,F63,F7,F82: aprovado.
- Compilação sintática dos módulos Python: aprovada.
- Sintaxe dos quatro scripts Bash: aprovada.
- Leitura estrutural do Compose e do devcontainer: aprovada.
- Exemplo IA/IoT executado: erros 25%/75%, normal, alerta, duplicado e rejeitado.

O ambiente de elaboração não dispõe de Docker. Não foram executados aqui o build das imagens, a inicialização do MySQL, os testes de integração HTTP/MySQL, a concorrência com banco real nem backup/restore. Esses testes estão incluídos para execução no Codespaces e no workflow. Não interpretar resultados esperados do README como medições já realizadas.
