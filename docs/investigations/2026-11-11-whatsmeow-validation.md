# Validação da candidata whatsmeow offline sync

**Estado: pools validados; preparar nova duração autorizada com recuperação até60s. A causa de produção permanece aberta.**
Tuan autorizou a atualização como candidata experimental depois que os dois métodos
locais não reproduziram o incidente. A conclusão deste relatório aguarda a nova execução de duas horas autorizada pelo Tuan.

## Identidade e ambiente

- Referência: imagem `0.7.2-0.1.0`, SDK `b572e5bcb92b`; base do fork `main@8d77799`.
- Candidata: código `f072697`, SDK `c88388f983b4`, Go 1.26.5, Linux/amd64, CGO habilitado.
- Tag apenas local: `tuanmedeiros/evolution-go:0.7.2-0.1.0-whatsmeow-c88388f-candidate`.
- Image ID: `sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd`.
- SHA-256 do binário: `985871d19c22059c733eaad0de962c6d35e5151044ca2934ffcd43a9636ee9dc`.
- VERSION interno preservado: `0.7.2-0.1.0`. Nenhuma imagem publicada.
- Docker e PostgreSQL temporário locais, dois números exclusivos e webhook local.
  Nenhuma mensagem ou chamada de teste usou instância de produção ou SuperAgentes.
- `alwaysOnline=false` nos dois clientes. `SynchronousAck=false` e
  `UnifiedSessionInterval=0` mantidos nos defaults. Justificativa e commits primários:
  [análise da atualização](2026-11-11-whatsmeow-upgrade-analysis.md).

## Comparação válida

| Medida | Referência | Candidata final |
|---|---|---|
| Rota ReconnectClient | 10/10 ciclos; Completed 10/10 | 10/10 ciclos; Completed 10/10 |
| Queda TCP de 10 s, somente receptor | 10/10 ciclos; Completed 10/10 | 10/10 ciclos; Completed 10/10 |
| Entrada antes/durante/depois | 60/60 nos dois métodos | 60/60 nos dois métodos |
| Saída recebida no outro número | 20/20 | 20/20 |
| Reinícios induzidos | 0 por API; 10 por socket | 0 por API; 10 por socket |
| Panics / erros de stream nos ciclos | 0 / 0 | 0 / 0 |
| Texto, imagem e áudio nas duas vias | 6/6 na prova curta | 6/6 na prova curta |
| Pareamento por QR | Dois números pareados por Tuan | QR adicional na SDK nova autenticou e recebeu prova |
| Conexões authDB após20reconexões+30s | 4→44 (+40) | 3→2, faixa2..3, sem acúmulo |
| Tráfego periódico por pelo menos 2 h | Não executado na referência | Interrompido: 41min08,5s, 54/54 entregas; 1 queda/erro503, recuperação automática |
| Build / vet / suíte completa | Testes existentes preservados | Passaram em `f072697` |
| Race dos três serviços alterados | Regressões sintéticas | Passou em `f072697` |

Resultados válidos da referência:
[API `7188d36c`](2026-11-11-offline-sync-before-7188d36c.md), 80,643 segundos;
[socket `a70c1164`](2026-11-11-offline-sync-before-socket-a70c1164.md), 162,916 segundos.

Resultados finais da candidata:
[API `07bec535`](2026-11-11-offline-sync-after-07bec535.md),
[socket `b8739baa`](2026-11-11-offline-sync-after-socket-b8739baa.md) e
[mídia `7c526e36`](2026-11-11-offline-sync-media-after-7c526e36.md).
[Duração `e282b2eb`](2026-11-11-offline-sync-media-after-e282b2eb.md) encerrou como `stopped`, não como aprovação de duas horas.

Foram entregues os 54 envios aceitos antes da queda. Houve um `stream:error`503,
sem o ack de status/media do relato, e o receptor voltou com OfflineSyncCompleted.
Não houve novo envio após a recuperação. O roteiro parou na perda momentânea de
autenticação/conexão. Tuan autorizou repetir2h aceitando recuperação+sync+entrega até60s e contando quedas; preparação em andamento. Nenhuma recuperação manual foi feita.

As primeiras execuções `588b5cb3` e `1d697be3` tinham contador de Completed incorreto.
Seus zeros foram invalidados, os relatórios receberam aviso e ambos os métodos foram
repetidos. As entregas históricas continuam válidas. As imagens intermediárias também
foram identificadas nos relatórios; seus resultados não substituem os da imagem final.

A comparação usa os mesmos números, dez ciclos por método, queda TCP de dez segundos
e janela de recuperação de 180 segundos. Envios durante a queda exigem confirmação
do remetente antes da reconexão. Quedas induzidas ficam separadas das espontâneas.
O incidente completo não apareceu na referência nem nos ciclos da candidata.

## Pools PostgreSQL: defeito confirmado localmente

Vinte reconexões reais do receptor na imagem original elevaram as conexões de4
a44, todas ociosas nas amostras; persistiram após30s. Na candidata,3→2, faixa2..3,
sem crescimento proporcional. Completed20/20 e provas20/20 em ambas. O observador
consultou pg_stat_activity pelo banco postgres, excluído da contagem de auth.

A main cria sqlstore/container/pool por StartClient e não fecha o pool aposentado.
A branch já compartilha um container por processo via deviceStoreInitializer; não
foi necessária outra mudança no aplicativo. Esse achado é da integração EvolutionGo
e não comprova a causa do congelamento de produção. Detalhes, comandos, identidades
e regressões RED/GREEN: [comparação dos pools](2026-11-11-whatsmeow-auth-pools.md).

## Evidência das correções

- O handler real de Archive falhava com a SDK antiga e com a nova. Três casos
  passaram após preservar o evento tipado na serialização do webhook.
- Os testes de reconexão verificam desconexão mesmo com socket fechado, retirada de
  handlers, espera do worker, concorrência, callbacks atrasados, QR/LoggedOut
  cancelados, exclusão sem fechar canal retido, ForceReconnect, Disconnect,
  configurações pendentes e limpeza completa antes de outro início.
- O primeiro bootstrap com a SDK nova apresentou migração concorrente. A
  inicialização SQL compartilhada tem testes de abertura única e retry após erro.
- Adaptadores mantêm `DHash/JIDs` dos bloqueios e PN/LID de `/user/check`. A regressão
  PN/LID também foi observada pela API local; a candidata passou pela mesma consulta
  e recebeu texto enviado com a formatação padrão.
- Regressões do roteiro cobrem o log real de Completed e rejeitam janela offline
  inconclusiva antes de classificar reprodução.
- Controles de versão/handshake do fork foram preservados, com seus testes existentes.
  Comandos e resultados vermelho/verde estão no [diário](2026-11-11-whatsmeow-offline-sync.md).

## Revisão do Codex

Codex CLI, modelo `gpt-6.1-sol`, esforço `high`, comando `codex review --base main`.
Cada rodada usou snapshot limpo separado do estado privado do laboratório. Nenhuma
branch foi trocada enquanto a revisão correspondente estava em execução.

| Rodada | Achados | Resultado |
|---|---|---|
| 1 | 2 P1 + 2 P2 | Corrigidos com regressões vermelho/verde |
| 2 | 1 P1 + 2 P2 | Corrigidos com regressões vermelho/verde |
| 3 | 2 P2 | Corrigidos com regressões vermelho/verde |
| 4 | 2 P2 | Corrigidos com regressões vermelho/verde |
| 5 | 1 P2 | Corrigido com regressão vermelho/verde |
| 6 | 1 P2 | Corrigido com regressão vermelho/verde |
| 7 | Limpa | Código `f072697`, sem novos achados |
| 8 | Limpa | Snapshot `86eb808`, incluindo medição de pools e regressão sequencial |
| 9 | 1 P2 | Corrigido: webhook atrasado poderia duplicar contagem de queda |
| 10 | 1 P2 | Corrigido: alinhar observação e contadores no mesmo corte final |
| 11 | Limpa | Snapshot `46fa181`, roteiro de recuperação e corte final |

Foram corrigidos 15 achados: 3 P1 e 12 P2 (o último no novo roteiro de duração). O sandbox do revisor restringiu listeners
locais na execução completa do pacote. No Mac, `go test ./pkg/whatsmeow/service -count=1`
passou após a revisão, além da suíte completa, build, vet e race já verdes no mesmo
código. O registro exigido permanece em `.code-review-log/fix-whatsmeow-offline-sync.md`,
local e ignorado pelo Git conforme a skill.

A oitava rodada revisou a extensão solicitada de pools sem novos achados. A
11ª encerrou limpa o novo modo de duração após corrigir os achadosR9/R10 com
regressões;14testes Python e a prova real do finalizador5b135557 passaram. O teste
sequencial de store foi verificado vermelho/verde e o pacote completo passou no Mac.
O aplicativo da imagem candidata continua sendo `f072697`; a extensão adiciona
testes e medição, sem nova mudança de runtime.

### Comportamentos alterados e suas consequências

| Decisão | Consequência sem a correção |
|---|---|
| Archive mantém evento tipado no JSON | Panic antes do webhook de arquivamento |
| Cancelar e aguardar a geração anterior, fechar socket e retirar handlers | Workers e callbacks antigos poderiam disputar a reconexão |
| Trava por instância cobre início e limpeza completos | Limpeza antiga poderia remover a referência do cliente novo |
| Sinais retidos por callbacks respeitam cancelamento e seus canais permanecem abertos | Panic em canal fechado ou bloqueio ao remover handler |
| Callback cancelado é ignorado e job compartilhado identifica o cliente aposentado | Estado do substituto poderia ser sobrescrito ou sua recuperação perdida |
| Pedido mais recente é aplicado durante a publicação do cliente | Atualização aceita de webhook/subscriptions poderia ser perdida |
| ForceReconnect e Disconnect aguardam a operação compartilhada, com fallback global de proxy | Substituição descartada, confirmação prematura ou rota ignorada |
| Inicialização SQL compartilhada, com retry após erro | Migrações concorrentes e pools acumulados por reconexão (4→44 no ensaio original) |
| Adaptadores preservam contratos HTTP de bloqueios e PN/LID | Mudança silenciosa de esquema ou identidade na SDK nova |
| Roteiro usa log real e exige queda comprovada | Medição incorreta de sincronização ou reprodução falsa |
| Observador usa horários originais de lifecycle e prova pós-recuperação até60s | Webhook atrasado poderia contar duas quedas; autenticação sozinha poderia ocultar falta de sync/recepção |

A trava abrange a operação inteira porque reservar somente o worker não protegia a
limpeza restante do chamador. Configurações pendentes usam uma trava curta separada;
SQL e conexão permanecem fora dela para permitir cancelamento durante a inicialização.
Vários achados de lifecycle foram introduzidos durante a implementação desta candidata;
não são apresentados como causas observadas em produção.

### Achados rejeitados

Nenhum. Todos os 15 procediam e foram corrigidos. Nenhum achado de revisão foi adiado.

### O que ficou fora

A causa de produção continua aberta e sua observação em canário depende de autorização
futura. Não foram reproduzidos o ack específico de status/media, a carga de 104
instâncias ou o playback manual da mídia. Também não há cobertura ao vivo de todos
os endpoints. Não foram criadas issues separadas para esses limites. A duração de duas horas permanece pendente após a interrupção. O próximo teste foi autorizado com recuperação+sync+entrega até60s e contagem de quedas; sua execução permanece pendente.

## Riscos, rollback e proposta de implantação

Testes verdes nas duas versões demonstram compatibilidade local e não isolam a causa
do congelamento. Não há controle de duas horas na referência. Mídia foi confirmada
por ID, tipo e entrega ao webhook, sem inspeção manual de reprodução no telefone.

A SDK exige Go 1.26 e migrações SQL 15/16, declaradas compatíveis com v8+. A imagem
antiga conectou e passou ambos os métodos no banco temporário já migrado. Essa é
evidência local de rollback, sem garantir todos os estados possíveis da produção.
Recuar dados antigos de sessão pode retroceder ratchets; o rollback proposto preserva
os dados atuais e troca a imagem para o digest anterior.

Digest atual confirmado dos dois serviços:
`tuanmedeiros/evolution-go:0.7.2-0.1.0@sha256:5c41352292072d0f533596389cc9445fc6d3ce1ce551aeb29dfe8b8e923a3c68`.

Após pedidos explícitos separados para publicar a imagem e fazer deploy: começar por
evoapi3, observar 24 horas e depois combinar janela para evoapi1. Fixar o digest
publicado, manter o digest anterior pronto e serializar migração/rollout. Observar
conclusões de sincronização por reconexão, recebimento, panics e quedas espontâneas.
Nenhum merge, publicação de imagem ou deploy foi feito neste trabalho.
