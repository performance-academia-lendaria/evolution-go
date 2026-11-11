# Laboratório local de sincronização offline

Estado: preparação da Fase 1. O bootstrap e o receptor estão implementados; o
pareamento, os ciclos e a medição ainda dependem dos pré-requisitos e não foram
executados. Este diretório não representa uma reprodução concluída.

O [plano](../../docs/plans/fix-whatsmeow-offline-sync.md) define todas as fases e
critérios; o [diário](../../docs/investigations/2026-11-11-whatsmeow-offline-sync.md)
registra resultados e o ponto de retomada.

## Preparar e consultar

Requer Docker local com endpoint Unix e as imagens locais
`tuanmedeiros/evolution-go:0.7.2-0.1.0`, `postgres:16-alpine` e
`python:3.12-slim`. O bootstrap usa os IDs locais e não faz pull.

```sh
python3 scripts/offline-sync/lab.py up
python3 scripts/offline-sync/lab.py status
```

A API fica em `http://127.0.0.1:18080` e o manager em
`http://127.0.0.1:18080/manager`. Banco e receptor não têm portas publicadas.
O futuro webhook da instância de teste deve apontar somente para
`http://evo-offline-sync-lab-receiver:8081/webhook` dentro da rede Docker.

O banco é temporário, em tmpfs, com os bancos `offline_sync_instances` e
`offline_sync_auth`. Sua remoção perde os dados e a ativação local. Não reiniciar
o PostgreSQL no meio do experimento. A API tem saída para a internet numa rede
separada; a outra rede é interna e conecta API, banco e receptor.

Credenciais novas são geradas automaticamente, sem ler `.env` nem dados de
produção. Os arquivos de estado ficam em `build/offline-sync-lab/`, ignorado pelo
Git e pelo contexto Docker. Não imprimir, versionar ou copiar os arquivos `.env`
desse diretório. O roteiro não ativa licença automaticamente; se o estado for
inativo, ele para e a execução deve aguardar orientação do Tuan.

O receptor grava somente horário, tipo do evento/mensagem, hash do ID, indicação
de mensagem própria e marcador artificial `EVOSYNC-<run>-C<cycle>-<phase>` quando
o texto inteiro corresponde ao formato. Ele descarta telefone, credenciais,
payloads completos, mídia e conteúdo livre. A API pode produzir logs sensíveis:
não usar `docker logs` com saída direta; a futura coleta deve retornar apenas
contagens/eventos selecionados, sem exibir nem salvar linhas brutas.

## Remover o laboratório

```sh
python3 scripts/offline-sync/lab.py down
```

Este comando remove apenas containers e redes locais identificados com a label
do laboratório, inclusive o banco temporário e eventuais volumes anônimos desses
containers. Os arquivos em `build/offline-sync-lab/` são preservados para limpeza
local explícita após conferir quais evidências devem permanecer. Não executar
limpeza durante o experimento ou enquanto a ativação local estiver em uso.

## Próxima etapa do roteiro

Depois de confirmar licença e disponibilidade do número exclusivo, implementar
pareamento sem exposição de token e ciclos com restauração garantida da rede de
saída, correlação dos eventos e confirmação dos marcadores pelo remetente. Fixar
janelas antes da primeira medição, executar ao menos dez ciclos e registrar o
resultado de referência antes de qualquer atualização da whatsmeow.
