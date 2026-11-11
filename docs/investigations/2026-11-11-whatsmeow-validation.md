# Validação da candidata whatsmeow offline sync

**Estado: em andamento. Nenhuma correção do congelamento de produção foi provada.**
A atualização experimental foi autorizada por Tuan após dois métodos locais não
reproduzirem a falha. Este documento deve ser finalizado antes do PR.

## Escopo e identidade

- Referência: main8d77799, imagem0.7.2-0.1.0, SDKb572.
- Candidata atual: sourcef072697, SDKc88388f, Go1.26.5/linux-amd64/CGO1.
- Tag somente local: tuanmedeiros/evolution-go:0.7.2-0.1.0-whatsmeow-c88388f-candidate.
- Produção intacta; somente digest e contagens sanitizadas foram consultados.
- Banco local temporário, dois números exclusivos e webhook local. Nenhuma mensagem
  de teste enviada a instâncias de produção ou SuperAgentes.
- Novas opções mantidas nos defaults: SynchronousAck=false, UnifiedSessionInterval=0.
  Ver análise de commits e justificativa em 2026-11-11-whatsmeow-upgrade-analysis.md.

## Comparação com a referência válida

| Medida | Referência corrigida | Candidata final |
|---|---|---|
| Rota de reconexão | 10/10 ciclos, Completed10/10 | 10/10 ciclos, Completed10/10 |
| Queda real TCP,10s receptor | 10/10 ciclos, Completed10/10 | 10/10 ciclos, Completed10/10 |
| Entrada antes/durante/depois | 60/60 nos dois métodos | 60/60 nos dois métodos |
| Saída recebida no outro número | 20/20 | 20/20 |
| Reinícios induzidos | 0 API;10 socket | 0 API;10 socket |
| Panics/erros de stream locais | 0/0 nos ciclos | 0/0 nos ciclos; duração em andamento |
| Texto/imagem/áudio duas vias | 6/6 prova curta | 6/6 prova curta; duração em andamento |
| QR novo na SDK | Referência pareada por Tuan | Passou na SDKc883, imagem1df14a7; prova recebida |
| Duração contínua com tráfego | Não executada na referência | Em andamento: e282b2eb, início22:15:21UTC,7200s solicitados |
| Build/vet/suíte | Testes preservados | Passaram emf072697 |
| Race dos serviços alterados | Regressões sintéticas | Passou emf072697 |

Candidata final: after-07bec535/API e after-socket-b8739baa/TCP, imagem4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd.
Prova curta de mídia:7c526e36.

Referência válida: before-7188d36c (80,643s) e before-socket-a70c1164 (162,916s).
As primeiras execuções588b5cb3/1d697be3 tinham contador Completed incorreto; seus
zeros foram invalidados e os relatórios receberam aviso. Entregas históricas seguem
válidas. Candidatas intermediárias foram identificadas como tais e não devem ser
usadas como comprovação da imagem final.

## Evidência de defeitos e regressões

- Archive: handler real falhava na SDKantiga e nova com conversão de tipo inválida;
  três casos passaram após preservar evento tipado no JSON. Atualizar SDK sozinha
  não corrige esse panic da aplicação.
- Reconexão: tests verificam desconexão mesmo com socket já fechado, remoção de
  handler, espera do worker, concorrência, callback atrasado, QRtimeout/LoggedOut
  cancelados, exclusão sem canal fechado, força de reconexão, configurações pendentes
  e serialização até terminar limpeza. Resultados vermelho/verde estão no diário e
  review log. Achados introduzidos pela candidata foram corrigidos, não atribuídos
  retroativamente à produção.
- NovoSDK: migração concorrente observada no primeiro bootstrap local; inicializador
  compartilhado/serializado foi coberto com testes de única abertura e retry após erro.
- Blocklist: adapter mantém DHash/JIDs do HTTP apesar de mudança upstream para Items.
- Harness: regressões cobrem log real Completed e impedem reprodução sem queda válida.
- Versão/handshake: nenhum arquivo de controle de versão foi alterado; testes existentes
  de seleção, inicialização, proxy e payload/nomes concorrentes passaram.

## Revisão obrigatória

CodexCLI, gpt-6.1-sol/high, codex review --base main. Snapshot limpo separado do estado
sensível do laboratório, sem troca de branch durante execução.

| Rodada | Achados | Estado |
|---|---|---|
| 1 | 2P1+2P2 | Aceitos, regressões RED/GREEN, corrigidos |
| 2 | 1P1+2P2 | Aceitos, regressões RED/GREEN, corrigidos |
| 3 | 2P2 | Aceitos, regressões RED/GREEN, corrigidos |
| 4 | 2P2 | Aceitos, regressões RED/GREEN, corrigidos |
| 5 | 1P2 | Aceito, regressão RED/GREEN, corrigido |
| 6 | 1P2 | Aceito, regressão RED/GREEN, corrigido |
| 7 | Limpa | Snapshotf072697, sem novos achados |

13achados aceitos/corrigidos (3P1/10P2). Nenhum rejeitado ou adiado.
Reviewer não pôde abrir listeners no sandbox para suíte completa; no ambiente
principal go test ./pkg/whatsmeow/service -count=1 passou0 após a revisão, além da
suíte completa/build/vet/race já verdes no mesmo código.

### Decisões que mudam comportamento e sua consequência

| Decisão | Consequência sem a correção |
|---|---|
| Archive preserva evento tipado no JSON | Panic antes do webhook de arquivamento |
| Geração anterior cancelada/aguardada, handlers removidos e socket fechado | Worker antigo e callbacks poderiam disputar a reconexão |
| Trava porID cobre operação inteira, inclusive início e limpeza | Limpeza antiga poderia remover referência do cliente novo |
| Canal retido por callback não é fechado e envio respeita cancelamento | Panic send-on-closed-channel ou bloqueio ao retirar handler |
| Callback atrasado ignora geração cancelada, job compartilhado identifica cliente recuperado | Estado do substituto poderia ser sobrescrito ou sua recuperação perdida |
| Configuração mais recente é aplicada antes/depois da publicação | Pedido de trocar webhook/subscriptions poderia ser reconhecido e perdido |
| ForceReconnect e Disconnect aguardam lifecycle compartilhado, com fallback de proxy global | Substituição descartada, confirmação prematura ou rota global ignorada |
| Inicializador SQL compartilhado com retry após falha | Migrações concorrentes tentavam adicionar a mesma coluna |
| Adaptadores preservam bloqueios e identidade PN/LID no HTTP | Contratos públicos mudavam com a SDK nova |
| Harness conta log real e valida janela offline antes de classificar | Medição de sync incorreta ou reprodução falsa |

A trava cobre operação completa porque reservar somente o worker não protegia a
limpeza posterior do chamador. Atualizações pendentes têm mutex próprio: SQL e
Connect não ficam sob ele, preservando cancelamento durante inicialização.

### Achados rejeitados

Nenhum. Todos os13achados procediam e tiveram testes de regressão antes/depois.

### O que ficou fora da validação

A causa do congelamento de produção permanece aberta; canário/observação dependem
de aprovação futura. Não foi reproduzido o ack de status/media específico, nem
feito teste de carga com104instâncias ou playback manual da mídia; não há issues
separadas criadas para esses limites. Duração≥2h ainda pendente neste rascunho.
 Log exigido:
.code-review-log/fix-whatsmeow-offline-sync.md (local, ignorado por orientação da skill).

## Limites e proposta de implantação (sem execução)

O incidente de produção ainda não foi reproduzido localmente. Testes verdes em
ambas versões demonstram compatibilidade local; não isolam causalidade da biblioteca.
O ack de status/media do relato não foi reproduzido pelo proxy de queda TCP. Não há
medida comparável de duas horas na referência nem teste de carga com104instâncias.
Mídia é confirmada por entrega ao webhook/tipo/ID, sem playback manual no telefone.

Imagem local final (código f072697):
sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd.
Binário inspecionado: Go1.26.5, linux/amd64, CGO1, SDKc883; SHA256server
985871d19c22059c733eaad0de962c6d35e5151044ca2934ffcd43a9636ee9dc.
VERSION interno preservado0.7.2-0.1.0. Nenhuma imagem publicada.

SDK exige Go1.26 e migrações15/16. SQLdeclara compatibilidade comv8+; imagem antiga
conectou e passou ambos métodos no banco temporário já migrado, evidência local de
rollback sem garantir todos os cenários da produção. Não restaurar snapshot antigo
sobre chaves de sessão atuais como rotina de rollback: pode retroceder ratchets.

Digest atual confirmado dos dois serviços:
tuanmedeiros/evolution-go:0.7.2-0.1.0@sha256:5c41352292072d0f533596389cc9445fc6d3ce1ce551aeb29dfe8b8e923a3c68.

Após pedidos explícitos separados para publicação e deploy: candidata primeiro em
evoapi3, observar24h, depois evoapi1 com janela combinada. Fixar digest publicado e
ter rollback para o digest acima pronto. Serializar migração/rollout e monitorar
conclusões de sync por reconexão, mensagens recebidas, panics e quedas espontâneas.
Nenhuma publicação, merge ou alteração de serviço está autorizada neste trabalho.
