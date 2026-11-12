# Conexões PostgreSQL por reconexão: antes e depois

Resultado: **acúmulo confirmado na imagem original; candidata sem acúmulo neste ensaio.**

## Medição real

| Medida | Imagem original / referência da main | Candidata f072697 |
|---|---:|---:|
| Reconexões sequenciais do receptor | 20 | 20 |
| Conexões iniciais | 4 | 3 |
| Conexões após20ciclos+30s | 44 | 2 |
| Diferença final−inicial | 40 | -1 |
| OfflineSyncCompleted | 20/20 | 20/20 |
| Mensagens de prova entregues | 20/20 | 20/20 |
| Remetente autenticado nas amostras | 20/20 | 20/20 |
| Panics / stream errors | 0 / 0 | 0 / 0 |

A referência cresceu4→6→8→...→44 (duas conexões por reconexão), mantendo44
após30s. A candidata iniciou com3, ficou entre2e3 nas vinte amostras e terminou2.
As conexões estavam ociosas nas amostras. São sessões SQL totais nesse banco,
não quantidade de pools; um pool compartilhado pode manter várias conexões.

## Método e limites

- Somente daemon Unix local e containers com label do laboratório. Nenhuma consulta
  a banco de produção. Banco de autenticação local: `offline_sync_auth`.
- Observador conectado a `postgres`, excluído da contagem pelo filtro de banco.
  O roteiro calcula `count(*)` de `pg_stat_activity WHERE datname = 'offline_sync_auth'`
  e contagens por estado, sem coletar SQL das sessões, endereços ou credenciais.
- Mesmos dois dispositivos, banco e configurações. Schema16 previamente migrado
  nas duas execuções. A API foi reiniciada somente para trocar a imagem; PostgreSQL,
  licença e pareamentos preservados. O companion QR adicional permaneceu inativo.
- Aquecimento com mensagens nos dois sentidos,10s antes da amostra inicial,
  `/instance/reconnect` somente no receptor,3s após cada ciclo e30s ao final.
- Depois de cada reconexão: nova conexão, Completed, entrega no webhook local
  e remetente autenticado. Nenhum restart espontâneo ou stream:error nos ciclos.
- Ao parar o processo original depois do teste, as44sessões caíram a0 sem reiniciar
  o Postgres. A candidata foi restaurada e ficou autenticada no laboratório.

## Causa encontrada e correção existente

Na main, `StartClient` chama `sqlstore.New` por início/reconexão. O SDK usa
`sql.Open`, criando um pool, e oferece `Container.Close`; a integração não fecha
esse container quando aposenta o cliente. O encerramento do websocket não fecha
o pool SQL. O crescimento medido confirma o defeito de gerenciamento de recursos.

Na branch, `deviceStoreInitializer` é campo do único `whatsmeowService` criado
pelo processo. Ele serializa a primeira inicialização bem-sucedida e compartilha
o mesmo container/pool entre todos os dispositivos e reconexões desse serviço.
Aposentar um cliente não fecha esse pool compartilhado, necessário aos demais.
Essa correção já estava em f072697, inicialmente motivada pela migração concorrente;
nenhuma nova alteração no runtime foi necessária para resolver o acúmulo medido.

Isso confirma um defeito independente na integração EvolutionGo. **Não prova que
ele causa o congelamento de recebimento em produção**, que não foi reproduzido.
Também não isola o efeito da atualização da SDK das demais correções da candidata.

## Regressões e reprodução

```bash
python3 scripts/offline-sync/pool_connections.py --label before --cycles 20 --expect-stable
# RED: exit2, conexões4→44
python3 scripts/offline-sync/pool_connections.py --label after --cycles 20 --expect-stable
# GREEN: exit0, conexões3→2
```

Trocar apenas a API local entre os comandos e conectar os pareamentos salvos,
conforme o plano e README do laboratório. O roteiro registra a imagem real.

- `TestDeviceStoreIsReusedAcrossSequentialReconnects`: início+20reconexões.
  RED com fábrica sem cache: falhou em reconnect1 por criar outro store; GREEN
  com inicializador compartilhado. Outros TestDeviceStore também passaram.
- Regressão de contrato dos marcadores: RED detectou o erro do roteiro inicial;
  GREEN após adequação à allowlist do receptor. Primeira tentativa e01acf67,
  interrompida antes de medir, ficou preservada como inválida.
- Python:3testes passaram. `go test ./...`:exit0 após a extensão.
- CodexCLI gpt-6.1-sol high, oitava rodada limpa em86eb808. Restrição de listeners
  do sandbox coberta pela execução completa do pacote no Mac, exit0.

## Identidade e registros

- [before b014b243](2026-11-11-auth-pools-before-b014b243.md): 2026-11-12T01:33:15.846067Z → 2026-11-12T01:36:47.573211Z; image ID `sha256:30cfa84be63f28f17a9e7e78e49a323fc59d33a68a029cab5dea4c1577321c0e`; harness `86eb808cc5cf75bc855ac97f28e950215467b716`.
- [after ca27b001](2026-11-11-auth-pools-after-ca27b001.md): 2026-11-12T01:37:58.824576Z → 2026-11-12T01:41:29.583986Z; image ID `sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd`; harness `86eb808cc5cf75bc855ac97f28e950215467b716`.

Plano: [fix-whatsmeow-offline-sync](../plans/fix-whatsmeow-offline-sync.md).
A nova duração d147ec0f passou7206,791s:150/150mensagens periódicas e uma prova,
1queda natural recuperada em5,181s,0panics/stream errors. Após duração, authDBlocal2idle.
Nenhum push, PR, merge, publicação de imagem ou deploy foi realizado.
