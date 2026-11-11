# Laboratório local de sincronização offline

Estado: Fase 1. Bootstrap, receptor, pareamento e experimento automatizado estão
implementados. Consultar o diário para saber quais execuções realmente ocorreram;
a existência do roteiro não significa reprodução ou validação concluída.

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

## Parear os dois números de teste

Após ativar a licença local pelo manager, criar as duas instâncias e abrir a página:

```sh
python3 scripts/offline-sync/lab.py pair
python3 scripts/offline-sync/lab.py qr-page
```

Abrir `http://127.0.0.1:18081` e parear `target` (receptor) e `sender` (remetente)
com dois números exclusivos de teste distintos. A página lê a imagem armazenada,
separa o PNG do código bruto e atualiza automaticamente. Não chama
`GET /instance/qr`, que pode iniciar outro cliente. Pareamento salvo e autenticação
ativa aparecem como estados distintos. O estado sanitizado também pode ser
consultado com `lab.py status`.

Se a API local tiver sido reiniciada deliberadamente, preservar o banco e retomar
as sessões já pareadas com `python3 scripts/offline-sync/lab.py connect`.
Esse comando não faz logout nem cria outro device e recusa iniciar outro cliente
quando já existe conexão não autenticada; investigar antes de contornar esse caso.

## Executar os ciclos e consultar os resultados

Com os dois números autenticados e o receptor de webhook ativo:

```sh
python3 scripts/offline-sync/experiment.py --label before --cycles 10 --recovery-seconds 180
```

O roteiro envia apenas marcadores artificiais entre os dois números de teste.
Cada ciclo confirma recebimento antes, chama `POST /instance/reconnect` no receptor,
confirma a janela offline, envia durante e depois da queda e verifica uma mensagem
de saída do receptor para o remetente. O endpoint chama o `ReconnectClient`
original; banco, webhook e remetente permanecem disponíveis. Nenhuma rede é alterada
por esse método. O atraso de restart é o da aplicação original (2 segundos).

O marcador durante a queda só é válido se a aceitação do envio terminar antes de
o receptor reconectar. Caso contrário, o roteiro para como inconclusivo. O tempo
para entrega inicial e marcador antes é 30 segundos. A recuperação e observação
após cada reconexão usam janela de 180 segundos, igual para referência e candidato.
O código não altera temporizadores nem comportamento da imagem testada.

Os resultados são gravados depois de cada etapa em
`build/offline-sync-lab/results/` (JSON sem credenciais) e em um Markdown por
execução em `docs/investigations/2026-11-11-offline-sync-<label>-<run>.md`.
O receptor correlaciona por hash da instância e por marcador e distingue mensagens
recebidas das próprias; ecos de envio do remetente não contam como recebimento.
Só contagens selecionadas são extraídas dos logs. Panics e erros de stream da
biblioteca sem ID são classificados como do processo, sem atribuição inventada.

Se houver `Connected`, prévia sem conclusão, perda de mensagens e envio do receptor
funcionando, a execução preserva a sessão com falha e para com `incident_reproduced`.
Falha inicial, autenticação perdida ou janela não confirmada encerram como
`stopped`, sem equivaler a reprodução válida. Dez ciclos sem o incidente encerram
como `not_reproduced`: parar e consultar o Tuan antes de atualizar a whatsmeow.
Não recuperar uma sessão com defeito automaticamente nem iniciar nova execução
concorrente sobre as mesmas instâncias.

## Método de queda real de socket somente no receptor

Esta extensão foi autorizada pelo Tuan após os dez ciclos da rota de API não
reproduzirem a perda de recebimento. Ela mantém a mesma imagem e biblioteca.

```sh
python3 scripts/offline-sync/lab.py socket-setup
python3 scripts/offline-sync/experiment.py --label before --method socket --cycles 10 --down-seconds 10 --recovery-seconds 180
```

`socket-setup` cria `evo-offline-sync-lab-proxy` sem porta publicada, valida-o com
tráfego TCP de eco em loopback (incluindo encerramento, CONNECT bloqueado e
restauração automática em vinte segundos) e configura apenas `target` pela API
local. A rota aplica a configuração com sua própria reconexão, fora da medição.
Não chamar outra reconexão em paralelo. O remetente deve continuar sem proxy.
As credenciais novas do túnel ficam em `build/offline-sync-lab/proxy.json` e
`proxy.env`, restritas e ignoradas; não copiar nem imprimir seus valores.
Como `Info` e `All` ocultam a configuração de proxy, o preflight verifica o
roteamento por consulta somente de leitura ao PostgreSQL local temporário,
retornando apenas host/protocolo/porta e presença de autenticação, sem credenciais.

O proxy encaminha bytes TLS opacos. Durante cada ciclo, fecha todos os túneis
ativos do receptor e segura novos CONNECT por dez segundos. Nenhum endpoint de
reconexão é chamado pelo roteiro nesse método: o evento `Disconnected` deve
disparar a recuperação da aplicação original. Validar sockets fechados, queda
observada, remetente autenticado, marco durante confirmado e restart automático.

A liberação é feita em `finally`. Um watchdog dentro do proxy abre a passagem
em vinte segundos mesmo se o processo do experimento morrer. A API/banco/receptor
de webhook e a saída direta do remetente não são interrompidos. A interface de
controle só escuta em loopback dentro do container e é usada por `docker exec`.

Resultados recebem prefixo `before-socket-<run>` e não sobrescrevem a referência
anterior. Se não reproduzir em dez ciclos ou aparecer outro bloqueio, parar e
consultar o Tuan novamente. `lab.py down` também remove o proxy quando a limpeza
do ambiente for apropriada; não executar isso durante testes ou ativação.

## Mídia e duração contínua

```sh
python3 scripts/offline-sync/media_traffic.py --label before
python3 scripts/offline-sync/media_traffic.py --label after --duration-seconds 7200 --interval-seconds 300
python3 -m unittest discover -s scripts/offline-sync -p 'test_*.py'
```

O roteiro envia PNG sintético, tom WAV de um segundo (convertido em Opus pela API)
e texto nas duas direções. Confirma recebimento pelo hash do ID, tipo e FromMe=false;
não salva payload, URL, chaves de mídia ou arquivo recebido. É verificação de entrega
à API/webhook, sem inspeção manual de reprodução da mídia no telefone.

A duração começa no início da execução e registra lotes periódicos e amostras de
autenticação a cada dois segundos. Não induz quedas; perda de autenticação, entrega,
panic ou erro de stream interrompe e preserva a sessão. Os experimentos de ciclos e
mídia usam o mesmo lock local para impedir execução simultânea. Não trocar imagem
nem iniciar novo pareamento durante a janela contínua.

O contador de conclusão usa o log real `Event: OfflineSyncCompleted,`, emitido pelo
handler explícito. Os dois primeiros relatórios históricos tinham contador incorreto
e receberam aviso; não usar seus zeros para comparar conclusão de sincronização.
A autorização do Tuan para prosseguir experimentalmente após não reproduzir está
registrada no plano. Passar os mesmos testes em ambas versões não prova a causa
nem a correção do congelamento de produção.
