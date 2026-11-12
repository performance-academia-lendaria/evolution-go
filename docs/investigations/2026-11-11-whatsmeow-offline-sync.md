# Diário da investigação da sincronização offline do WhatsApp

## Ponto de retomada

Atualizado em 2026-11-12, 01:31 BRT / 04:31 UTC.
**Nova autorização: seguir até versão/release, imagem publicada, digest e rollback prontos. Sem deploy.**

Plano ativo: `docs/plans/release-0.7.2-0.1.1.md`. A parada anterior permanece no histórico; foi substituída pelo pedido explícito do Tuan para os passos1–4.

PR: https://github.com/performance-academia-lendaria/evolution-go/pull/2

- **Branch/base:** `fix/whatsmeow-offline-sync`, `main@8d77799`. Não ler, modificar
  ou adicionar os arquivos pessoais não rastreados `AGENTS.md` e `untitled.md`.
  Push realizado somente para academia; PR #2 aberto no fork.
- **Aplicativo:** `f072697`, SDK `c88388f`, Go 1.26.5. Imagem local Linux/amd64:
  `sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd`.
  Tag: `tuanmedeiros/evolution-go:0.7.2-0.1.0-whatsmeow-c88388f-candidate`.
  Imagem não publicada. Versão/handshake preservados; ack=false/sessionInterval=0.
- **Pools:** a main abre SQLStore/pool por StartClient sem fechar o anterior.
  A branch compartilha um container por processo. Após 20 reconexões: original
  4→44 (+40), candidata 3→2 (faixa 2–3); 20 syncs/provas em cada versão.
  RED exit2/GREEN exit0; regressão unitária vermelho/verde. Após duas horas,
  authDB local com 2 conexões ociosas. Nenhuma consulta a banco de produção.
- **Ciclos:** API10+TCP10 por versão, Completed20/20, entrada60/60, saída20/20.
  Congelamento de produção não reproduzido. Tuan autorizou candidata experimental.
  Contadores antigos incorretos invalidados e testes repetidos.
- **Duração d147ec0f PASS:** 7206,791s, 02:23:38.873122Z→04:23:45.641773Z;
  25 lotes, 150/150 periódicas (50 de cada tipo) + 1 prova; 3660 amostras.
  Uma queda natural do receptor, nenhuma do remetente; 5,181s até conexão,
  Completed e prova. Panics0/stream errors0; nenhuma tentativa interrompida.
  Sem falha forçada ou recuperação manual. Sessão49229 exit0 e watcher427
  encerrados; caffeinate terminou. Não aguardar esses processos novamente.
- **Queda:** 04:14:33.568193Z→04:14:38.749033Z. Causa não isolada. A primeira
  duração e282b2eb parou aos 41min pelo critério estrito, sem aprovação de duas
  horas. Preflights induzidos de 3,943s/4,573s são separados da taxa natural.
- **Revisão:** R11 limpa em `46fa181`. R1:2P1+2P2; R2:1P1+2P2; R3/R4:2P2;
  R5/R6:1P2; R7/R8:limpas; R9/R10:1P2 no roteiro; R11:limpa.
  Quinze corrigidos (3P1/12P2), nenhum rejeitado/adiado. 14 testes Python passaram.
  Build/vet/test Go completos e race dos três serviços passaram. Listeners
  restritos no sandbox do revisor foram cobertos pela suíte completa no Mac.
- **Identidade:** runtime não mudou após f072697; só teste sequencial de store,
  roteiro e docs. Código do roteiro revisto em46fa181; duração usou harness3abf955
  (mesmo código, documentação posterior). Nenhum ajuste de código depois da R11.
- **Lab preservado:** API/PG/receptor/proxy, ambos os números autenticados, proxy
  aberto e autherrors0. Não reiniciar/remover o PG tmpfs: licença/ratchets vivos.
  Estado privado ignorado em `build/offline-sync-lab`. Companion QR salvo/inativo;
  não pedir novo QR. Bancos locais offline_sync_auth/offline_sync_instances,
  schema16; a imagem original já passou nesse schema. Não restaurar sessões antigas.
- **Produção:** somente leitura. Campo Image dos dois serviços reconfirmado após
  a duração: `tuanmedeiros/evolution-go:0.7.2-0.1.0@sha256:5c41352292072d0f533596389cc9445fc6d3ce1ce551aeb29dfe8b8e923a3c68`.
  Sem consulta a DB/segredos, temporários ou mutações remotas. Contagens sanitizadas
  anteriores estão no histórico. Não é necessário novo acesso remoto.
- **GitHub:** academia conferido; main remoto8d77799; branch enviada e PR #2 aberto.
  Gofmt dos 11 arquivos Go alterados limpo. Corpo do PR inglês completo, sem
  placeholders, em `.code-review-log/pr-body-draft.md`.
- **Parada:** PR #2 aberto após testes/revisão. Nenhum trabalho restante desta
  autorização. Não executar merge, publicação de imagem ou deploy sem pedidos
  explícitos separados. Proposta registrada: evoapi3/24h, depois evoapi1 em
  janela combinada, rollback pela imagem registrada. Tráfego de teste encerrado;
  laboratório e pareamentos preservados para inspeção.
- **Relatórios:** `2026-11-11-whatsmeow-validation.md` e
  `2026-11-11-whatsmeow-auth-pools.md`. Review log privado:
  `.code-review-log/fix-whatsmeow-offline-sync.md`.

## Critério de registro

Evidência histórica, leitura de código, preparação e execução são categorias
distintas. Um resultado ausente fica como **não executado**. Cada experimento
deve identificar versão exata, configuração não sensível, comando, intervalo,
observação e interpretação. Não salvar tokens, licença, connection strings,
telefones, payloads completos ou conteúdo de mensagem.

## Progresso registrado

### 2026-11-11 — Conferência inicial, antes dos testes

- Lidas as instruções de `AGENTS.md` e a seção de 2026-11-11 da investigação em
  `~/Documents/GitHub-Projects/legendsagents/.local/investigations/2026-11-10-agente-nao-responde-whatsapp.md`.
  Seus achados são antecedentes; não foram refeitos em produção nesta sessão.
- `git status --short`: apenas `?? AGENTS.md` antes da criação dos documentos.
  Esse arquivo é preexistente, não será incluído nos commits da correção.
- Remotos conferidos: `academia` é o fork autorizado; `origin` é o upstream.
  Nenhum fetch/push executado até este checkpoint.
- Branch criada com `git switch -c fix/whatsmeow-offline-sync main`.
  `HEAD` continua no mesmo commit da base.
- Go local: `go1.26.5 darwin/arm64`; `go.mod` exige `go 1.25.0`.
- Docker cliente/servidor: `29.8.2`; Compose: `v5.5.0`.
  Contexto `orbstack`, servidor `OrbStack`, arquitetura `aarch64`, endpoint Unix
  local. Não há uso de daemon Docker da EC2.
- Imagem de referência já presente no Docker local:
  `tuanmedeiros/evolution-go:0.7.2-0.1.0`, `linux/amd64`.
  ID local: `sha256:30cfa84be63f28f17a9e7e78e49a323fc59d33a68a029cab5dea4c1577321c0e`.
  RepoDigest local:
  `sha256:5c41352292072d0f533596389cc9445fc6d3ce1ce551aeb29dfe8b8e923a3c68`.
  Este digest **não foi conferido na EC2** e não é ainda a evidência de rollback.
- Imagens locais disponíveis para preparação: `postgres:16-alpine` e
  `python:3.12-slim`, entre outras. Nenhum container foi iniciado.
- Código lido: configuração de banco/API, inicialização, rotas de licença e
  instância, envio de webhook e caminhos de conexão/reconexão.
- O código prevê `GET /license/status`; licença inativa bloqueia as rotas da API
  com HTTP 503. O estado do futuro laboratório ainda não foi consultado.
- Confirmado em código que `EnableAutoReconnect=false` e que `Disconnected`
  agenda `ReconnectClient` em goroutine. Isso não demonstra a causa do incidente.
- A imagem executa o servidor diretamente e não requer leitura do `.env` local;
  o roteiro deve fornecer apenas configuração nova e descartável.
- A `.dockerignore` atual não exclui `.env`. Se for necessário construir imagem,
  preparar contexto apenas com arquivos rastreados para não enviar dados locais
  ao builder. Nenhum build foi iniciado.
- Skill `tm-codex-review-loop` lida. Modelo `gpt-6.1-sol` e esforço `high` já
  definidos pelo Tuan. `.code-review-log/` já consta no `.gitignore` e na
  `.dockerignore`; nenhuma rodada executada.

### 2026-11-11, 14:22 BRT — Documentação solicitada antes de prosseguir

- Tuan determinou que planejamento e progresso devem ficar documentados para
  permitir retomada após interrupções.
- Execução interrompida na preparação; nenhum teste iniciado antes de registrar
  o plano das cinco fases, critérios de bloqueio, evidências e ponto de retomada.
- Criados `docs/plans/fix-whatsmeow-offline-sync.md` e este diário no repositório.
- Decisão: continuar somente a preparação local autorizada; dependência e código
  de produção permanecem sem mudanças até a reprodução.

### 2026-11-11 — Plano salvo e bootstrap preparado

- Plano e diário salvos no commit local
  `1ef5673 docs(whatsapp): record offline sync investigation plan`.
  Apenas esses dois arquivos foram incluídos; nenhum push executado.
- Criados `scripts/offline-sync/lab.py`, `receiver.py` e `README.md`.
  O roteiro inicial oferece `up`, `status` e `down`; pareamento/ciclos/medição
  permanecem pendentes, sem alegação de reprodução.
- Preparação prevista: daemon exclusivamente local por socket Unix, imagens
  fixadas por ID, banco em tmpfs sem porta publicada, receptor na rede interna,
  API com porta em loopback e rede separada de saída, estado em diretório ignorado.
- Receptor usa lista permitida de metadados. Não salva payload nem imprime logs
  de requisição. O bootstrap não lê `.env` e não fornece licença real.
- Próximo experimento: conferir sintaxe e recursos locais; iniciar a referência
  apenas para verificar prontidão e estado da licença. Se inativa, registrar o
  bloqueio, manter o ambiente para decisão do Tuan e parar.

### 2026-11-11, 14:26 BRT — Bootstrap executado; parada por licença

- `ast.parse` de `lab.py` e `receiver.py`: ambos com sintaxe válida.
- `python3 scripts/offline-sync/lab.py status` antes do bootstrap: três containers
  ausentes, licença indisponível; nenhum recurso preexistente foi reutilizado.
- `python3 scripts/offline-sync/lab.py up`: criou as duas redes e os três
  containers, usando IDs das imagens locais. Configuração de banco e chave local
  foram geradas automaticamente; nenhum segredo existente foi lido.
- O estado sanitizado retornou `running` para os três containers e
  `license: inactive`. O roteiro terminou intencionalmente com código 1:
  `STOP: local license is not active. Ask Tuan before any activation or workaround.`
- Conferidas somente portas, destinos/tipos de montagens e configuração das redes,
  sem inspeção de variáveis de ambiente. Apenas `127.0.0.1:18080` publicado.
- Conferidas permissões dos arquivos por `stat`, sem abrir conteúdo sensível.
- **Decisão:** cumprir a parada solicitada. Não ativar automaticamente, não copiar
  licença de produção, não alterar código de licença e não tentar parear.
- Nenhum ciclo, mensagem real, unidade Go, atualização de dependência, build,
  acesso à EC2, push ou PR foi executado. O receptor ainda não foi validado com
  tráfego WhatsApp; sua preparação não constitui validação funcional.
- Pendência para o Tuan: orientar ativação de licença própria de teste pelo manager
  local e confirmar número exclusivo e outro remetente, sem enviar chaves no chat.

### 2026-11-11, 14:41 BRT — Acesso local para ativação pelo Tuan

- Tuan informou que vai ativar e solicitou a `GLOBAL_API_KEY` do laboratório.
- A chave administrativa gerada foi copiada diretamente de
  `build/offline-sync-lab/api.env` para a área de transferência do macOS via
  `pbcopy`. A leitura parou na linha da chave, sem abrir os valores das connection
  strings subsequentes. Nenhum valor de chave foi exibido ao agente ou registrado.
- Ação restrita ao laboratório, sem leitura de credenciais de produção, alteração
  de configuração ou tentativa de ativação pelo agente.
- Próximo passo: Tuan usa Cmd+V no manager local e conclui a ativação com licença
  própria de teste. A chave administrativa aleatória não constitui uma licença
  válida por si. Depois da confirmação, consultar apenas o estado sanitizado.
- Sem novo pareamento, ciclos, atualização de dependência, push ou acesso à EC2.

### 2026-11-11, 14:42 BRT — Autorização explícita para exibir a chave de teste

- Tuan autorizou expressamente expor a API key de teste no chat.
- Lida e exibida somente a linha `GLOBAL_API_KEY` do arquivo gerado do laboratório,
  sem ler as connection strings subsequentes nem acessar credenciais de produção.
- Não registrar o valor em arquivos versionados. Nenhuma alteração na configuração
  ou no bloqueio de licença; ativação local pelo Tuan continua pendente.
- Observado `untitled.md` não rastreado; arquivo não aberto, alterado ou incluído
  em commits, assim como o `AGENTS.md` preexistente.

### 2026-11-11, 14:43 BRT — Licença ativada pelo Tuan e conferida

- Tuan informou que ativou a licença local. `python3 scripts/offline-sync/lab.py status`
  retornou os três containers `running` e `license: active`.
- Nenhuma chave de licença foi lida ou exibida nessa conferência; apenas o campo
  de estado foi retornado. Nenhum restart ou alteração de configuração executado.
- Bloqueio de licença resolvido. Retomada da preparação do roteiro da Fase 1;
  nenhum pareamento/ciclo ainda iniciado.
- Pergunta pendente ao Tuan: envio manual pelo segundo celular, dois números de
  teste pareáveis para automatização, ou indisponibilidade dos números agora.
  A escolha não altera a exigência de teste exclusivamente local e descartável.

### 2026-11-11 — Dois números confirmados e preparação dos QRs

- Tuan confirmou dois números exclusivos de teste e se disponibilizou a parear
  ambos para automatizar o tráfego. Pré-requisito de números disponível.
- Decisão: criar `offline-sync-target` (receptor) e `offline-sync-sender` (remetente)
  no laboratório existente, com webhook exclusivamente local. Não usar produção.
- O roteiro `pair` cria IDs/tokens antes da escrita na API, verifica duplicatas e
  recupera QRs em arquivos locais restritos. Não imprime tokens nem telefones.
- Para as quedas de rede com remetente disponível, preparar conexão intermediária
  exclusiva do receptor; não derrubar toda a rede da API compartilhada pelos dois.
  Essa preparação ainda não foi executada e não altera código da aplicação.
- Fonte primária local da biblioteca: `OfflineSyncPreview` anuncia eventos
  perdidos; `OfflineSyncCompleted` indica término do envio pelo servidor. O
  experimento deverá criar mensagens durante a queda, sem presumir backlog.
- Nenhuma medição de reconexão começou. Primeiro apresentar os QRs ao Tuan.

### 2026-11-11, 14:47 a 14:55 BRT — Pareamentos e correções do roteiro

- QRs PNG gerados pelo roteiro às 14:47 e apresentados ao Tuan. Página auxiliar
  local em `http://127.0.0.1:18081`, sem tokens no navegador e com atualização
  automática dos QRs. Processo antigo da página substituído após corrigir a exibição.
- Erro introduzido pelo agente na página: `Instance.Qrcode` armazena
  `PNG data URI|código bruto`, e a página tentou usar a composição toda como imagem.
  Corrigido para usar apenas a primeira parte. PNG obtido de `/state` decodificado
  com `base64.b64decode(validate=True)` e assinatura PNG conferida; exibição anterior
  falhou no navegador, conforme screenshot enviado pelo Tuan.
- Remetente pareado às 14:48:43 BRT; receptor às 14:54:01 BRT. Eventos `PairSuccess`
  vistos em contagem/cronologia sanitizadas. PostgreSQL local contém dois devices
  (`SELECT count(*) FROM whatsmeow_device`), sem leitura de chaves ou telefones.
- Às 14:54:45 BRT o receptor está `Connected=true, LoggedIn=true`; remetente tem
  JID salvo mas `LoggedIn=false`. A página distingue pareamento salvo de autenticação
  ativa e não oferece novamente o QR de uma sessão já registrada.
- Encontrado segundo erro do roteiro inicial: `POST /instance/connect` seguido
  imediatamente por `GET /instance/qr` pode criar dois clientes, pois o GET inicia
  uma instância se o cliente assíncrono ainda não foi registrado. Logs mostram duas
  inicializações de cada papel às 14:47 e dois devices novos para o remetente.
- Um cliente não pareado continuou rotacionando QR e reiniciando com dados antigos,
  enquanto o outro já havia pareado. Essa preparação é **inconclusiva como referência**
  para o incidente e não conta entre os dez ciclos.
- O remetente também teve uma queda espontânea, novo Connected e OfflineSyncPreview
  sem OfflineSyncCompleted observado. Há interferência de clientes duplicados;
  esse achado não prova o incidente nem a hipótese de biblioteca defasada.
- Corrigido o roteiro para ler o QR via `GET /instance/info/:id`, sem chamar o GET
  mutante. Adicionado comando `connect` para reutilizar somente sessões salvas.
- Decisão: reiniciar somente `evo-offline-sync-lab-api` para eliminar as goroutines
  antigas e reconectar ambos com os dois devices persistidos. Sem logout, exclusão,
  limpeza de banco, ativação nova, alteração de imagem ou acesso à produção.
- Método escolhido para os ciclos: `POST /instance/reconnect` exclusivamente no
  receptor, que chama `ReconnectClient` e mantém o remetente disponível na mesma
  API. É uma das alternativas autorizadas no plano original. A conexão intermediária
  cogitada antes não foi implementada nem usada.

### 2026-11-11, 14:57 a 15:00 BRT — Sessões retomadas e roteiro de referência pronto

- Executado restart somente da API local, na mesma imagem por ID; PostgreSQL,
  licença, ambos os devices e receptor de webhook preservados.
- `lab.py connect` iniciou uma conexão por papel, usando os devices salvos e sem
  solicitar QR. Conferência posterior: `Connected=true, LoggedIn=true` para ambos,
  licença `active`. Nenhum telefone ou token exibido.
- Criado `scripts/offline-sync/experiment.py` para envio automatizado, reconexão
  dirigida ao receptor e relatório incremental por execução. Mesma imagem e mesma
  biblioteca da referência, sem alteração em código Go, dependências ou timers.
- Configuração de medição fixada antes da execução: dez ciclos; 30 segundos para
  entrega inicial/antes; 180 segundos para recuperação e observação após reconexão.
  A janela de queda vem do `ReconnectClient` original (sleep de 2 segundos).
  Envio durante só conta se a aceitação acabar com o receptor ainda offline.
- Recebimento é correlacionado por hash da instância, mensagem não própria e marcador
  artificial. Remetente e receptor usam os mesmos webhook/banco descartáveis.
- Atualizado e reiniciado somente o receptor local para acrescentar hash da
  instância e direção desconhecida explícita; isso ocorreu antes de medir tráfego.
- Smoke de HTTP/privacidade: payload sintético retornou 204; registro contém hashes,
  mas não o token, ID bruto, identificador da instância, chat nem conteúdo livre
  usados na prova. Marcador não correspondente não foi salvo como texto.
- `ast.parse` dos três scripts: sintaxe válida. A leitura dos logs é programática,
  com saída somente de contagens, sem salvar/imprimir linhas ou payloads brutos.
- Relatórios Markdown e JSON serão atualizados após cada etapa/ciclo. Sem novo QR,
  logout, exclusão, mudança de versão, push ou acesso à produção.

### 2026-11-11, 15:01 BRT — Referência iniciada; primeiro ciclo em observação

- Preparação salva no commit local
  `90a273f test(whatsapp): automate local pairing and reconnect measurements`.
- Confirmado diff vazio de `main` em `go.mod`, `go.sum`, `pkg/` e `cmd/`.
  Somente documentação e roteiro local alterados nesta branch.
- Execução `before-588b5cb3`, sessão `58062`, usando imagem local atual por ID.
  Relatório incremental específico referenciado no ponto de retomada.
- Prova inicial de envio do remetente até o webhook do receptor passou, antes de
  iniciar os ciclos. No primeiro ciclo a queda foi observada; envio aceito em
  0,673 s com receptor ainda offline; receptor reconectou e todos os marcadores
  antes/durante/depois chegaram. Mensagem de saída do receptor chegou ao remetente.
- No checkpoint, um `Connected`, um `OfflineSyncPreview`, zero `OfflineSyncCompleted`,
  zero panics/erros de stream no período do ciclo; janela de 180 s ainda em curso.
- Interpretação provisória: falta de `OfflineSyncCompleted` isolada não demonstra
  interrupção de mensagens. O incidente completo ainda não foi reproduzido.

### 2026-11-11, 15:04 BRT — Primeiro ciclo concluído; identidade do binário conferida

- Ciclo 1 encerrou a janela de 180 s com entrega dos três marcadores e da mensagem
  de saída, um Preview e zero Completed. Resultado `delivery_pass_sync_unobserved`;
  nenhuma perda de mensagem demonstrada. Ciclo 2 começou automaticamente com os
  mesmos parâmetros; acompanhar seu estado no relatório incremental.
- Auditados metadados de build do executável `/app/server` copiado somente do
  container **local**. Saída selecionada: Go `go1.25.0`, versão de fork
  `0.7.2-0.1.0`, whatsmeow `v0.0.0-20260630180629-b572e5bcb92b`.
- SHA-256 do executável:
  `0c8c285749ed9f19a90b02ff1008b49585b8ebe842ca7011085e20e532e965bf`.
  O build não embute revisão VCS; não há prova criptográfica de commit de fonte
  por esse metadado. A referência é a imagem atual indicada pelo Tuan, fixada por ID.
- Metadados selecionados em `build/offline-sync-lab/reference-binary-metadata.json`;
  cópia temporária do binário removida ao final da auditoria. Nenhum arquivo na EC2.
- Como Completed não apareceu, manter a janela completa de três minutos por ciclo
  (aproximadamente meia hora para dez), sem encurtar o critério durante a medição.

### 2026-11-11, 15:10 BRT — Três ciclos fechados; referência continua

- Três quedas/reconexões dirigidas e três envios durante queda confirmados.
- Recebimento no receptor: 9/9 marcadores de ciclo, além da prova inicial.
  Recebimento no remetente: 3/3 provas de saída do receptor.
- Nos três ciclos fechados: três Preview, zero Completed, zero panics e zero erros
  de stream observados nas janelas. O quarto ciclo começou com os mesmos parâmetros.
- Não há reprodução do congelamento do recebimento até este checkpoint. Continuar
  até dez ciclos ou uma falha que exija a parada prevista no roteiro.

### 2026-11-11, 15:32 BRT — Dez ciclos concluídos; parada por não reprodução

- Execução `before-588b5cb3`: 15:01:00 a 15:32:12 BRT (18:01:00 a 18:32:12 UTC),
  duração de 1.872,042 segundos, aproximadamente 31min12s. Código de saída 0;
  estado de experimento **`not_reproduced`**.
- Dez quedas observadas, dez reconexões autenticadas e dez envios aceitos durante
  a queda, com receptor ainda offline. Todas as janelas de 180 s concluídas.
- No receptor: 10/10 marcadores antes, 10/10 durante, 10/10 depois; prova inicial
  adicional também entregue. No remetente: 10/10 mensagens de saída do receptor.
- Eventos do receptor nas janelas: dez `Connected`, dez `OfflineSyncPreview`, zero
  `OfflineSyncCompleted`, zero reinícios automáticos por `Disconnected`.
  Eventos do processo: zero panics de handler e zero erros contendo `stream:error`.
- Latência máxima observada, do início do pedido local até o webhook: antes 1,452 s,
  durante 3,904 s, depois 0,814 s; saída para o remetente 1,307 s. São relógios do
  host/receptor Docker local e tráfego sintético, não benchmark de produção.
- **Conclusão:** a ausência de `OfflineSyncCompleted` coexistiu com recebimento
  funcionando. Ela não é, sozinha, prova de fila de mensagens congelada. Não foi
  demonstrada causa do incidente nem confirmada/descartada a hipótese de dependência.
- **Limites:** chamadas à rota de `ReconnectClient`, sem queda real de socket/rede,
  sem erro de ack de status/media do servidor, somente mensagens sintéticas de texto
  pontuais por fase; duração inferior a duas horas. Não valida mídia, áudio, carga
  contínua ou estabilidade de 1–2 h. Não equivale a produção com 18 quedas/h agregadas.
- **Decisão obrigatória:** cumprir a regra de não reprodução e parar antes da
  atualização. Nenhuma edição em `pkg/`, `cmd/`, `go.mod` ou `go.sum`; sem build
  candidato, revisão Codex, push, PR, publicação ou deploy. Produção não acessada.
- Ambiente local preservado para uma possível continuação: dois pareamentos e
  licença ativos, três containers e página de QR; nenhum experimento em execução.
- Pergunta enviada ao Tuan: ampliar para quedas reais do socket exclusivamente
  no receptor (remetente online), testar pelo menos duas horas na referência com
  tráfego periódico, ou manter parado. Nenhuma alternativa executada ainda.

### 2026-11-11 — Extensão para quedas reais autorizada pelo Tuan

- Tuan escolheu: “Provocar quedas reais do socket só no receptor, mantendo o
  remetente online”. A parada da primeira execução foi cumprida antes da resposta.
- Resultados iniciais e documentação salvos no commit local
  `6c1ada5 test(whatsapp): record ten reconnects without receive failure`.
- Plano de extensão registrado antes de implementar: proxy CONNECT local só no
  receptor, queda de túneis por dez segundos, liberação em finally e watchdog de
  vinte segundos, sem descriptografar TLS ou alterar a aplicação.
- Validar primeiro com tráfego de eco sintético, depois aplicar à sessão já salva
  do receptor. Nenhum novo pareamento necessário. Preservar remetente direto.
- Medir os mesmos dez ciclos/30s/180s numa execução separada, agora observando
  `Disconnected` e restart automático. Não chamar a rota de reconexão nos ciclos.
- Não executado ainda: proxy, configuração ou ciclos do novo método. Sem escrita
  em produção, mudança Go/dependência, build candidato, push ou PR.

### 2026-11-11, 15:42 BRT — Proxy validado e aplicado ao receptor

- Criados `fault_proxy.py` e `proxy_smoke.py`; estendidos `lab.py` e `experiment.py`
  para o método `socket`. Nenhuma edição no código Go ou nas dependências.
- `lab.py socket-setup` criou o quarto container de teste na rede interna/saída,
  com imagem Python já fixada por ID, sem porta publicada, disco somente leitura
  e credenciais novas restritas. Teste de eco exclusivamente em loopback, sem WhatsApp.
- Smoke passou: encaminhamento TCP, EOF real no socket fechado, novo CONNECT
  bloqueado durante queda, restauração explícita e watchdog independente que
  restaurou a passagem após vinte segundos.
- Configurado somente `target` pela rota local de proxy. Essa rota reconecta
  automaticamente para aplicar; essa preparação não conta como ciclo experimental.
  Nenhuma nova leitura de QR, logout, exclusão, restart da API ou alteração no banco
  fora da configuração descartável da instância de teste.
- Estado após preparação: ambos `Connected=true, LoggedIn=true`; licença ativa.
  Proxy com um túnel ativo, três aceitos (dois do smoke), zero autenticações rejeitadas;
  controle aberto. Remetente confirmado sem proxy.
- Parâmetros do próximo experimento: dez ciclos, dez segundos de queda real,
  restauração máxima de vinte segundos, limites de 30/180 s preservados.
  Registrar EOF/Disconnected/restart automático e entrega, sem reconexão manual
  durante os ciclos. Nova execução separada da primeira.

### 2026-11-11, 15:46 BRT — Roteamento conferido por metadados locais

- Preparação do proxy salva em
  `82b46d5 test(whatsapp): add target-only TCP fault injection`.
- Primeira tentativa do método socket encerrou antes de qualquer marcador/ciclo:
  o preflight tentou conferir proxy via `Info`, mas `Info` e `All` deliberadamente
  zeram esse campo na resposta (`instance_service.go`). Não houve queda real nessa
  tentativa nem criação de relatório experimental; não conta como ciclo.
- Corrigida verificação do roteiro com `proxy_routes`: consulta somente local ao
  PostgreSQL temporário, IDs validados como UUID, banco fixo `offline_sync_instances`,
  selecionando host/protocolo/porta e booleano de presença de autenticação. Não
  retorna senha, username, token, licença ou connection string.
- Corrigida uma aspa SQL na nova consulta; habilitado `ON_ERROR_STOP=1` para uma
  falha SQL não ser tratada como lista vazia válida. Verificação repetida passou.
- Resultado sanitizado: `target_route_matches=true`, `sender_direct=true`;
  `gate_open=true`, um túnel ativo, três aceitos, zero rejeições de autenticação.
- Sem alteração no Go, biblioteca, pareamentos ou imagem. Pronto para nova
  execução; aplicar esta correção não iniciou outra reconexão.

### 2026-11-11, 15:48 BRT — Queda real iniciada; primeiro ciclo em observação

- Roteiro corrigido salvo em
  `7460f77 test(whatsapp): verify fault routing with local metadata`.
- Nova execução `before-socket-1d697be3`, sessão `46833`, relatório incremental
  separado. A prova inicial de recebimento pelo túnel passou antes da primeira queda.
- Primeiro ciclo: um túnel TCP fechado, queda observada, remetente continuou
  autenticado, envio durante aceito com passagem fechada, gate restaurado e receptor
  reconectado automaticamente pelo código original.
- Log selecionado confirma um restart por `Disconnected`, um Connected, um Preview,
  zero Completed, zero panics e zero erros de stream até o checkpoint. Nenhuma
  chamada manual à rota de reconexão durante o ciclo.
- Marcadores antes/durante/depois e prova de saída entregues. Janela de 180 s
  ainda em curso. Não há conclusão sobre o incidente completo neste checkpoint.

### 2026-11-11, 16:05 BRT — Metade das quedas reais concluída

- Cinco ciclos socket concluíram todas as janelas; sexto em observação.
- Nos cinco concluídos: cinco sockets encerrados, cinco quedas observadas, cinco
  reinícios disparados por `Disconnected`, remetente autenticado durante todas
  as quedas e gate restaurado em todas. Não confundir esses reinícios induzidos
  com quedas espontâneas.
- Entrega nos cinco ciclos: 15/15 marcadores no receptor e 5/5 provas de saída no
  remetente. Dez segundos nominais de queda por ciclo; mesmos limites de 30/180 s.
- Cinco Preview, zero Completed, zero panics e zero erros de stream nas janelas.
  O sexto já entregou seus marcadores e prova de saída, ainda sem janela concluída.
- Hipótese da dependência permanece aberta; nenhum congelamento reproduzido até
  este checkpoint. Relatório incremental segue salvando cada etapa automaticamente.

### 2026-11-11, 16:20 BRT — Dez quedas reais concluídas; não reprodução confirmada

- Execução `before-socket-1d697be3`: 15:47:42 a 16:20:11 BRT
  (18:47:42 a 19:20:11 UTC), duração 1.949,486 s, aproximadamente 32min29s;
  código 0 e estado de experimento **`not_reproduced`**.
- Dez túneis TCP ativos efetivamente encerrados, dez quedas observadas, dez envios
  durante a queda confirmados, dez recuperações autenticadas e dez liberações do
  gate. Remetente permaneceu autenticado durante todas as interrupções.
- Dez reinícios por `Disconnected`, todos provocados pelo teste. Dez Connected,
  dez Preview, zero Completed. Sem chamada manual de reconexão durante os ciclos.
- Entrega: 10/10 antes, 10/10 durante, 10/10 depois; prova inicial adicional
  entregue. No outro sentido: 10/10 provas de saída do receptor.
- Zero panics e zero erros `stream:error` do processo nas janelas. O fechamento
  TCP gerou EOF/Disconnected e não reproduziu a rejeição de ack de status/media
  vista no servidor. Não misturar os reinícios induzidos com taxa espontânea.
- Máximo do pedido local até webhook: antes 0,714 s, durante 12,250 s, depois
  1,173 s, saída 1,236 s. A mensagem de durante ficou pendente enquanto o túnel
  esteve fechado e chegou após a recuperação. Valores de host/Docker local.
- **Conclusão:** mesmo com o handler real Disconnected/Restart exercitado, não
  houve congelamento. As duas execuções demonstram que falta de Completed isolada
  pode coexistir com entrega funcionando. A causa do incidente e a hipótese de
  biblioteca defasada continuam sem confirmação ou descarte causal.
- **Limites:** cada execução durou cerca de meia hora, com textos sintéticos
  pontuais. Não foi feito teste contínuo de duas horas, tráfego de áudio/imagem,
  status/mídia, carga de produção nem reconexões concorrentes para o mesmo device.
  Não houve panic Archive durante esses cenários; seu fix/teste continuam pendentes.
- **Parada:** nenhuma alteração em Go/dependências, build candidato, revisão Codex,
  push, PR, merge, publicação ou deploy. Produção nunca foi acessada nesta sessão.
- Ambiente preservado com quatro containers, gate aberto e dois números autenticados.
  Não há ciclo em execução. Nova pergunta enviada ao Tuan antes de prosseguir:
  duração de pelo menos duas horas com texto/áudio/imagem (sugerido), reconexões
  concorrentes só no receptor, ou manter parado.

### 2026-11-11, 16:33–16:40 BRT — Nova orientação e análise da biblioteca

- Após a parada por não reprodução, Tuan sugeriu prosseguir com correção na
  biblioteca e perguntou sobre a viabilidade. Retomada da Fase 2 como candidata
  experimental, mantendo a causa não comprovada e os demais limites originais.
- `go list -m -json go.mau.fi/whatsmeow@latest`, sem editar go.mod, resolveu
  `v0.0.0-20261110152934-c88388f983b4`, de 2026-11-10 15:29:34 UTC, Go mínimo 1.26.0.
- Clonado upstream público, apenas para leitura, em
  `build/offline-sync-lab/whatsmeow-upstream`. HEAD
  `c88388f983b4bc43dfd0bcc2b46969fcde82d61f`; `git rev-list --count`
  confirmou exatamente 117 commits desde `b572e5bcb92b`.
- Lidos diffs primários de filas/conexão, stream errors, keepalive, handshake,
  status, acks, sessão unificada e app state; análise dedicada linkada abaixo.
- Opções e causa permanecem decisões técnicas a validar. O suporte a stanza
  `status` não prova correção da rejeição `ack class=status type=media` observada.
- Próximas ações: teste de regressão de Archive antes de mexer nele; atualização
  oficial e adaptação do build para Go 1.26; testes locais e de duração. Não criar
  fork/patch especulativo da biblioteca sem defeito concreto na versão atual.

### 2026-11-11, 16:53 BRT — Panic Archive reproduzido antes da correção

- Criado `pkg/whatsmeow/service/archive_event_test.go`: chama o handler real com
  evento tipado e captura seu despacho de webhook em memória, sem rede ou segredos.
  Casos previstos: arquivar, desarquivar em full sync e Action nula; verifica o
  contrato JSON e a fila, em vez de testar somente uma função auxiliar.
- Comando: `go test ./pkg/whatsmeow/service -run '^TestArchiveEventDispatchesTypedPayload$' -count=1`.
- **VERMELHO**, exit 1, na versão antiga: primeiro caso reproduziu
  `interface conversion: interface {} is *events.Archive, not map[string]interface {}`
  em `whatsmeow.go:1787`. Não é resultado de WhatsApp/produção; é regressão unitária
  do panic já relatado e independente da hipótese de congelamento.
- Upstream também confirmou migrações 15 e 16 de sqlstore (companion meta nonce e
  segredo WASA). Revisar compatibilidade e preservar rollback local antes de trocar
  a imagem do laboratório; nenhum schema local ou de produção alterado ainda.
- Atualização selecionada: oficial `c88388f983b4`, com Go mínimo 1.26.0. O arquivo
  da dependência sugere toolchain 1.27.2; verificar o resultado efetivo de go get/build
  com o Go 1.26.5 instalado. Não inferir necessidade de atualizar produção.

### 2026-11-11, 16:54–17:17 BRT — Dependência atualizada e regressões corrigidas

- Executados `go get go.mau.fi/whatsmeow@latest` e `go mod tidy` usando proxy público
  e Go 1.26.5 local. Resolvido `c88388f983b4`, go.mod passou para `go 1.26.0`;
  dependências transitivas acompanhadas pelo resolvedor. Não foi necessário baixar
  Go 1.27.2 nem editar os mecanismos de versão/payload do fork para compilar o pacote.
- Dockerfile atualizado de Go 1.25.0 para 1.26.5, alinhado ao novo mínimo e ao host.
- Archive continuou **vermelho** com o SDK novo, mesmo panic/linha. Removida somente
  a conversão indevida: o evento tipado já contém os campos JSON necessários.
  Casos arquivar/desarquivar full-sync/Action nula ficaram **verdes**, preservando
  fila, envelope, JID, timestamp e ação no teste do handler real.
- Testes de reconexão no código anterior ficaram **vermelhos** por motivos
  funcionais: socket já fechado não recebia Disconnect explícito; duas chamadas
  concorrentes executavam duas limpezas (4 consultas em vez de 2); preparação da
  substituição ocorria com worker anterior ainda ativo e contexto não cancelado.
- Reconexão agora combina chamadas simultâneas por instância, cancela a geração
  anterior, chama Disconnect mesmo com socket fechado, remove handlers e aguarda
  término do worker antes de limpar registros e iniciar substituto. Removido o
  sinal não bloqueante de kill usado na reconexão e a recursão de restart do worker.
- Workers capturam o canal da própria geração. Presença e rotação QR encerram com
  o contexto; o worker de presença não consome o sinal destinado ao worker principal.
- Novo teste provou **vermelho**: timeout QR bloqueado numa operação antiga podia,
  após substituição, enviar kill ao canal novo. Corrigido com contexto e canal da
  geração capturados; teste **verde**.
- Callback Disconnected passa identidade do cliente ao fluxo interno. Guarda de
  propriedade impede callback antigo de aposentar substituto. Prova **vermelha**
  removendo temporariamente apenas a guarda: matou o substituto e removeu seu
  handler. Guarda restaurada; mesmo teste **verde**. Código temporário não mantido.
- Grupo de regressões passou após correções:
  `go test ./pkg/whatsmeow/service -run '^(TestArchiveEventDispatchesTypedPayload|TestReconnect.*|TestStaleDisconnected.*|TestCanceledQRTimeout.*)$' -count=1`.
- Receivers do serviço passaram a ponteiro para não copiar o grupo sincronizado.
  Interface pública mantida. Nenhum estado online/payload de handshake alterado.
- As migrações oficiais 15/16 declaram compatibilidade com v8+ e acrescentam colunas;
  nenhum schema foi migrado ainda no laboratório. Confirmar antes de trocar imagem.
- SDK novo e patches de app ainda não rodaram com os números reais. Biblioteca
  continua sem confirmação causal em produção; candidato precisa de validação local
  completa e teste de duração antes de PR. Opções de ack/sessão continuam sob análise.

## Comparação dos dois métodos na referência (contador corrigido)

As execuções históricas 588b5cb3 e 1d697be3 tinham contador de Completed inválido.
As duas repetições abaixo são a referência válida para sincronização. Os scripts
executados correspondiam ao conteúdo depois commitado em 1df14a7; o campo
harness_commit das execuções iniciais registra somente HEAD no início, e não
certifica árvore limpa. Todos os ciclos válidos tiveram janela offline confirmada.

| Indicador | Rota ReconnectClient | Queda TCP real só no receptor |
|---|---|---|
| Execução válida | before-7188d36c | before-socket-a70c1164 |
| Ciclos com queda e reconexão confirmadas | 10/10 | 10/10 |
| Sockets encerrados pelo controle | Não se aplica | 10 |
| Reinícios automáticos por Disconnected | 0 | 10 induzidos |
| Envio aceito durante queda confirmada | 10/10 | 10/10 |
| Entrada antes/durante/depois no webhook | 30/30 | 30/30 |
| Saída do receptor recebida no remetente | 10/10 | 10/10 |
| Preview / Completed | 10 / 10 | 10 / 10 |
| Panics / erros de stream nas janelas | 0 / 0 | 0 / 0 |
| Incidente de recebimento congelado | Não reproduzido | Não reproduzido |

Ambas usam a imagem original e biblioteca b572. As provas iniciais adicionais
chegaram; não estão somadas aos 30 marcadores de cada execução. Testaram a imagem
antiga contra schema temporário já atualizado pela primeira candidata, sem rewinding
chaves/sessões. Isso demonstra compatibilidade local de leitura/conexão do rollback.

## Comparação antes e depois — estado atual

| Medida | Referência válida | Candidata final f072697 |
|---|---|---|
| Biblioteca | b572e5bcb92b | c88388f983b4 |
| Ciclos por API / por socket | 10/10 + 10/10 | 10/10 + 10/10 |
| OfflineSyncCompleted | 20/20 | 20/20 |
| Entrada antes/durante/depois | 60/60 | 60/60 |
| Saída recebida no outro número | 20/20 | 20/20 |
| Reinícios induzidos | 0 API; 10 socket | 0 API; 10 socket |
| Panics / erros de stream nos ciclos | 0 / 0 | 0 / 0 |
| Texto/imagem/áudio nas duas vias | 6/6 prova curta | 6/6 prova curta |
| QR da SDK nova | Não se aplica | Novo companion autenticou e recebeu prova na SDK c883 |
| Duração de pelo menos duas horas | Não executada na referência | Em andamento, e282b2eb |
| Build / vet / suíte / race | Testes existentes preservados | Passaram; pacote completo repetido fora do sandbox do revisor |
| Revisão Codex | Não se aplica | Limpa na 7ª rodada; 13 achados corrigidos |

Referência: 7188d36c/API e a70c1164/socket. Candidata final: 07bec535/API,
b8739baa/socket, 7c526e36/mídia. Imagem local de código f072697:
sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd.
O [relatório consolidado](2026-11-11-whatsmeow-validation.md) reúne os detalhes.

## Conclusão causal atual

O congelamento relatado na produção não foi reproduzido em nenhum dos dois métodos.
Na referência medida corretamente, a sincronização terminou e mensagens chegaram.
A hipótese da biblioteca defasada não está confirmada nem descartada. Atualização
oficial e correções demonstradas nos testes são uma candidata experimental autorizada
pelo Tuan; compatibilidade local não provará que o incidente de produção foi resolvido.

## Fase 2 — checks e adaptação de API (17:26 BRT)

- Primeiro build/vet/suíte completos falharam em quatro chamadas de pkg/user/service:
  UpdateBlocklist agora recebe dhash, GetBlocklist idem; SetStatusMessage recebe
  types.SetStatusInput. Ajustado dhash vazio para manter resposta completa, conforme
  documentação/código upstream; status usa Text apontando para o texto já recebido.
  Nenhuma alteração no contrato HTTP. Não é prova comportamental de correção.
- Race em pkg/whatsmeow/service passou. Saídas resumidas em
  build/offline-sync-lab/checks/. Novos checks serão registrados após adaptação.
- make fmt foi executado; formatação incidental do arquivo obfuscado pkg/core/c0.go
  foi restaurada após comparação byte a byte com gofmt(HEAD), preservando escopo.
- Produção permanece intocada; lab ainda usa imagem antiga. Nenhuma publicação.

## Fase 2 — compilação concluída (17:30 BRT)

- Após adaptar as quatro chamadas, go build ./..., go vet ./... e go test ./...
  encerraram com código 0. go test -race ./pkg/whatsmeow/service também código 0.
  Logs locais em build/offline-sync-lab/checks/; suíte preexistente preservada.
- Primeira candidata usa defaults upstream: SynchronousAck=false e
  UnifiedSessionInterval=0. Alterar opções juntamente com SDK impediria distinguir
  efeitos; sem defeito demonstrado, manter comportamento de ack/presença atual.
- Próximo: imagem linux/amd64 de contexto Git sem arquivos locais; cópias internas
  dos bancos temporários antes da migração; executar no mesmo lab e comparar.
- A revisão obrigatória usará a skill tm-codex-review-loop já lida, com modelo
  gpt-6.1-sol e esforço high explicitamente escolhidos pelo Tuan. Nenhuma nova
  escolha/autoridade de deploy é inferida.

## Fase 3 — prova curta de mídia da referência (17:32 BRT)

- Roteiro complementar criado: scripts/offline-sync/media_traffic.py.
- Comando: python3 scripts/offline-sync/media_traffic.py --label before.
- Execução media-before-19d178f4, 8,359 segundos, código 0: texto 2/2, imagem 2/2,
  áudio 2/2 entregues nas duas direções; confirma hash do ID, FromMe=false e tipo.
  Sem mídia real, download remoto de fixture ou conteúdo pessoal.
- Relatório: [mídia antes](2026-11-11-offline-sync-media-before-19d178f4.md).
  Isto é prova curta de envio/recebimento, não teste de duração.
- Build da candidata está em execução (sessão 17955), log restrito local
  build/offline-sync-lab/candidate-build.log; fonte Git cbe91dc, linux/amd64,
  tag local 0.7.2-0.1.0-whatsmeow-c88388f-candidate. Não houve push.
- Revisão Codex rodada 1 executa em snapshot limpo cbe91dc, sessão 35472,
  relatório .code-review-log/round-1.txt, decisões em fix-whatsmeow-offline-sync.md.
  Mudanças posteriores no roteiro deverão entrar na próxima rodada. Não trocar
  branch do snapshot enquanto o processo executar.

## Revisão rodada 1 e primeira conexão da candidata (17:36 BRT)

- Codex encerrou com 2 P1 e 2 P2, todos aceitos; decisões no log obrigatório.
  Dois hangs de lifecycle foram introduzidos pelo patch atual (LoggedOut bloqueante
  após cancelamento; StartInstance substitui canal mesmo com socket ativo).
  Adaptar também JSON de blocklist, que mudou na biblioteca.
- **Correção de evidência:** contador Completed do roteiro busca log Unhandled,
  mas o handler trata esse evento e emite Event: OfflineSyncCompleted. O 0/20
  anterior é inválido como medição de sincronização. Entregas/quedas continuam
  válidas. Logs do antigo container já não existem após troca local; não reconstruir
  resultado por inferência. Corrigir contador com regressão e repetir referência.
- Candidata linux/amd64 construída, ID
  sha256:669d2c58683bccf477228491b1d5ce5b0a0f27ceb1bd91c5b446cc12b9580cc8.
  Apenas API local trocada; bancos temporários copiados internamente para
  offline_sync_auth_before_c88388f e offline_sync_instances_before_c88388f.
- Licença ativa; remetente autenticou. Receptor não iniciou: duas chamadas
  sqlstore.New concorrentes tentaram migrar v14->v15; uma falhou por coluna
  companion_meta_nonce já existente. Sem logout, sem QR novo e sem bypass.
  Fluxo de migração precisa ser serializado antes de repetir conexão.
- Não iniciar ciclos nesta candidata até corrigir achados/migração. Próximo passo:
  testes de regressão vermelhos/verdes, build revisado, referência recontada e
  comparação seguida do teste contínuo. SynchronousAck/UnifiedSessionInterval ainda
  nos defaults; nenhum motivo observado para alterá-los.
- Produção consultada apenas via docker service inspect --format da imagem dos
  dois serviços. Usuário SSH não tem docker.sock; leitura formatada por sudo -n
  funcionou. Ambos usam tag 0.7.2-0.1.0 com digest
  sha256:5c41352292072d0f533596389cc9445fc6d3ce1ce551aeb29dfe8b8e923a3c68.
  Nenhum log/ambiente/segredo remoto lido, nenhum temporário remoto criado.

## Correções da rodada 1 — regressões verificadas (17:42 BRT)

- LoggedOut: teste com evento real despachado pela SDK, DB pausado e contexto
  cancelado falhou antes (remoção de handlers bloqueada); passou após sinal de
  parada específico da geração e sensível a cancelamento.
- StartInstance: teste falhou antes porque chamada redundante substituía canal do
  worker; passou com guarda do worker ativo. Criação do canal movida para início
  efetivo de StartClient; removida dos chamadores. starts.LoadOrStore impede dois
  workers simultâneos do mesmo ID. Exige revisão da publicação e do encerramento.
- Blocklist: teste JSON falhou com Items/AddressingMode sem JIDs; passou com adapter
  do contrato HTTP DHash/JIDs, preferindo PN conhecido e usando LID como fallback.
- Contador: fixture do log real falhou com 0 em vez de 1; passou após buscar
  Event: OfflineSyncCompleted. Receptor também reconhece o tipo explicitamente.
- Migração concorrente: refatoração de inicialização sem cache reproduziu 20
  inicializações em 20 chamadas; teste passou com inicialização compartilhada e
  serializada. Falha transitória não fica memorizada; novo teste valida retry.
- Referência foi retomada na imagem original contra DB temporário migrado, sem
  restaurar schema: licença e ambos devices autenticaram. É evidência de rollback
  de leitura/conexão local; não é restauração completa de produção.
- Repetição da referência API em andamento: before-7188d36c, sessão 64874,
  relatório em docs. Primeiro ciclo agora contou Completed=1, mostrando por que os
  antigos zeros não podiam ser usados para concluir falta de sincronização.

## Referência com contador corrigido — API (17:43 BRT)

- before-7188d36c encerrou código 0: dez ciclos, 10/10 Completed e Preview,
  entrada 30/30, saída 10/10; zero panics/stream errors. Incidente não reproduzido.
- Mesmo roteiro/janelas de 180s, imagem original, dois devices preservados. Não
  houve espera artificial pelo timeout porque a conclusão agora é detectada.
- Próxima execução de referência: socket, 10 quedas de 10s no receptor apenas,
  log build/offline-sync-lab/reference-socket-corrected.log. Não mudar imagem até
  encerramento. Continuação de candidata já autorizada pelo pedido do Tuan.
- Após correções da rodada 1: build/vet/suíte completos e race dos pacotes alterados
  passaram. Novas regressões vermelhas/verdes registradas acima e no review log.

## Referência com contador corrigido — socket (17:46 BRT)

- before-socket-a70c1164 código0, dez quedas TCP de 10s: Preview10, Completed10,
  entrada30/30, saída10/10, remetente autenticado10/10, reinícios automáticos10
  induzidos, nenhum panic/stream error. Gate restaurado. Incidente não reproduzido.
- Execuções substituem a contagem de sincronização inválida dos primeiros relatos;
  nenhuma conclusão causal da biblioteca é permitida por esse resultado.
- Candidata corrigida construída de 1df14a7, apenas API local em troca; mesmos
  bancos e devices preservados, sem outra migração no schema já atualizado.

## QR adicional autorizado (17:47 BRT)

- Tuan confirmou que pode escanear novamente com um dos dois números. Orientado a
  usar o receptor (target, primeiro telefone), preservando companions atuais.
- Antecipar validação de QR antes dos próximos ciclos para aproveitar disponibilidade
  do Tuan. Helper pairing_check.py inicia instância separada; não altera instances.json.
  Página loopback18082, log local pairing-check-page.log. Não iniciar quedas enquanto
  o novo pareamento estiver em andamento. Depois confirmar autenticação e uma
  mensagem de teste antes de seguir. Nenhum dispositivo de produção envolvido.

## QR confirmado e correções rodada 2 (17:54 BRT)

- Tuan escaneou QR adicional. Companion novo da candidata autenticou e recebeu
  prova sintética no webhook (sem número/token/payload no registro). Página18082
  continua somente leitura; estado privado separado de instances.json.
- Todos os 3 achados da rodada2 aceitos e corrigidos, testes falharam antes e
  passaram após (detalhes no review log). Delete/ClearInstanceCache agora aposentam
  geração por cancelamento/espera; canais de parada nunca são fechados com callbacks
  retidos. ForceReconnect usa ReconnectClient serializado. Roteiro rejeita janela
  offline inválida antes de avaliar assinatura do incidente.
- Verificação adicional encontrou início ainda sem MyClient publicado: teste
  falhou porque o restart não cancelava a inicialização do banco. Run com contexto
  agora é reservado sincronamente em StartClient antes do go; aposentadoria aguarda
  stopped mesmo nessa fase; conexões/SQL usam contexto da geração. Worker fecha
  socket/remove handlers ao terminar, antes de liberar reserva/notificar stopped.
- Execução de ciclos da candidata aguarda rebuild destas correções. QR testou a SDK
  nova, mas a imagem anterior ainda tem os defeitos de lifecycle demonstrados em
  testes; não conta como candidata final nem validação de estabilidade completa.
- Build/vet/suíte/race em execução para rodada2. Nenhum deploy/push/publicação.

## Reserva de substituição e checks finais da rodada 2 (17:56 BRT)

- TestStartClientWaitsForRetiringReservation falhou antes: substituição era
  descartada se encontrasse reserva cancelada mas ainda não encerrada. Passou após
  aguardar stopped e tentar reservar novamente; worker ativo continua compartilhado,
  sem criação de socket duplicado. Cobre também entrada direta de Connect após stop.
- Build/vet/suíte passaram com mudanças da rodada2; detector de race passou nos
  três pacotes de serviço alterados, incluindo regressão adicional acima.
- Nenhuma opção nova da SDK foi ligada: pareamento novo e reconexões da referência
  completam sem isso. Candidata final ainda precisa dos seus ciclos e duração.
- Preparar commit/rodada3 e rebuild. API local ainda roda imagem 635d..., com QR
  validado; não iniciar duração enquanto houver alteração de código da candidata.

## Terceira revisão e primeiros ciclos da candidata (18:06 BRT)

- Imagem local 4a137f1 construída em linux/amd64,
  sha256:db384371e4b0186174798c5442dcc76665c1c3b4aacc7fcdfc6a4f6ad06d41c7.
  Ambos devices retomaram autenticados; companion do QR adicional ficou salvo,
  sem retomar durante comparação, preservando dois clientes ativos como referência.
- API after-72be3eb9: 10/10 ciclos/Completed, entrada30/30, saída10/10, zero
  panics/stream errors. Não é imagem final: novo patch abaixo exige nova execução.
- Observação: cancelamento deliberado emite callback Disconnected antigo; log de
  automatic_restart nessa imagem contou tentativas antes de verificar geração, não
  novos sockets. Teste reproduziu escrita de status false por geração cancelada;
  fix ignora Disconnected dessa geração antes de alterar DB/cache ou emitir evento.
- Rodada3 Codex: 2P2, sem P1, ambos aceitos. Callback de uma geração nova podia
  compartilhar job anterior sem ter sido recuperado; resultado agora identifica
  cliente aposentado e reavalia quando job compartilhado pertencia a outro.
  Teste RED perdeu recovery da geração nova, GREEN aposentou-a corretamente.
- UpdateInstanceSettings agora rejeita contexto já cancelado; Connect segue então
  caminho de iniciar/aguardar substituto, em vez de reconhecer worker morrendo como
  conexão pronta. Teste RED retornou sucesso em worker cancelado; GREEN erro de
  indisponibilidade esperado. Primeiros fixtures tinham cache ausente e foram
  completados antes de medir o vermelho comportamental; panic de fixture não é prova.
- Checks completos em execução após esses fixes; preparar rodada4 e rebuild.
  Nenhum teste de duração iniciado, nenhum deploy/publicação/push.

## Checks após rodada3 (18:08 BRT)

- go build ./..., go vet ./..., go test ./...: código0 após todos os fixes.
- go test -race nos três pacotes alterados: código0. Duas regressões Python: verdes.
- Candidata intermediária after-72be3eb9 anotada como intermediária e com limitação
  do contador de tentativas de callback. Não usar essa linha como taxa de quedas.
- Preparar rodada4 no novo commit e rebuild, preservando somente dois clientes
  usados pela comparação. QR adicional já foi confirmado sem novo pedido ao Tuan.

## Candidata5b0e96e — identidade e dez ciclos API (18:12 BRT)

- Imagem local linux/amd64 construída sem publicar:
  sha256:8d7165a354a9e03bb48b61d1d2db1a0af120fdf8463a080f19ab91f71901096f.
- Inspeção do binário real em execução confirmou Go1.26.5, whatsmeow
  v0.0.0-20261110152934-c88388f983b4, CGO=1, GOOS=linux, GOARCH=amd64,
  VERSION0.7.2-0.1.0. SHA256server:
  30057abe29eb6c6bcaa7bd23552381da47f11355d5fdba6050c4fe72c5753202.
  Cópia temporária local do binário apagada em finally; metadados sem segredos em
  build/offline-sync-lab/candidate-binary-metadata.json. Não houve arquivo remoto.
- after-92222051: dez ciclos API, Completed10/10 e Preview10/10, entrada30/30,
  saída10/10, zero callbacks de restart de gerações canceladas, panics0/stream0.
  Mantida janela180s e dispositivos da referência. Não reproduziu incidente.
- Socket final inicia agora: 10quedas reais de10s só receptor, mesmas janelas e
  método da referência, log candidate-socket-final.log. Não trocar API durante teste.
- Nova leitura remota de service logs (2h, cap100000 não atingido) retornou32
  stream_errors em evoapi1 e0 em evoapi3; não continha logs de eventos do logger
  da aplicação, portanto NÃO permite concluir ausência de Completed. Consulta
  subsequente busca somente contagens dos arquivos instance.log via LOG_DIRECTORY,
  sem imprimir caminhos, dados livres, telefones ou mensagens; sem temporários.
- Revisão4 em andamento; duração contínua ainda não começou.

## Rechecagem de produção somente por contagens (18:12 BRT)

- Leitura remota processada no servidor, sem conteúdo livre/telefones/IDs em claro.
  LOG_DIRECTORY foi consultado isoladamente (somente caminho não secreto), arquivos
  instance.log lidos via tail limitado e filtrados por timestamp JSON das últimas2h.
  Nenhum arquivo temporário criado na EC2; nenhum estado, serviço ou banco alterado.
- evoapi1: 104 arquivos, 249871 linhas examinadas; contagens filtradas por2h:
  Connected46, Preview41, Completed9, callbacks de restart45. Cinco instâncias com
  pelo menos uma conclusão; 14 com mais previews que conclusões. **Há truncamento
  possível em arquivos que atingiram tail10000**: estes são totais de amostra, não
  censo/medida de taxa nem prova de congelamento por instância. Nenhuma mensagem de
  produção enviada ou lida; nenhuma ação de recuperação.
- evoapi3: 3 arquivos,26linhas, nenhum evento de sync/restart nessa janela, sem
  cap atingido. Isso não prova saúde/recebimento porque tráfego não foi testado.
- Leitura separada de service logs (sem cap atingido) contou32 ocorrências de
  stream:error em evoapi1 nas2h e0 em evoapi3. Não atribuir cada linha a uma conexão
  ou telefone, nem misturar com ciclos induzidos do laboratório.
- A evidência de produção continua compatível com o relato de sincronização que
  não conclui em parte das instâncias; a correção do contador local não invalida
  aquele relato. Não confirma causalidade da SDK e não substitui reprodução local.
- JSONs sanitizados em production-log-counts-2h.json e
  production-instance-log-counts-2h.json no estado ignorado. Nenhuma nova leitura
  de produção necessária para continuar os testes locais neste momento.

## Quarta revisão e lifecycle compartilhado (18:26 BRT)

- Candidata5b0e96e: socket after-socket-af051f2f passou10/10 Completed,30/30 entrada,
  10/10 saída, dez restarts induzidos, sem panics/streams. Prova curta mídia
  media-after-c5e7d566 passou6/6 nas duas vias. Receptor foi reiniciado sozinho após
  ciclos para carregar allowlist de Completed; API/DB/sockets permaneceram ativos.
- Rodada4 Codex: 2P2, sem P1. Ambos aceitos/corrigidos com regressão RED/GREEN.
  Reserva do worker não impedia outro StartClient de publicar antes de terminar
  limpeza do chamador: mutex porID agora cobre StartClient, StartInstance,
  reconexão e ClearInstanceCache por operação completa. Usado KeyedMutex de util
  já presente (agora importação direta), com refcount e descarte de locks ociosos.
- Pedido Connect durante inicialização antes perdia webhook/subscriptions novos.
  Agora run.data guarda pedido mais recente e é lido sob mesmo mutex antes da
  publicação. Se publicação acabou enquanto pedido aguardava, aplica também ao
  MyClient/cache existente. Casos anterior/posterior à publicação testados.
- Complemento: Disconnect antes confirmava ao receber kill, embora limpeza ainda
  pendente. Teste demonstrou isso; agora aguarda aposentadoria via ClearInstanceCache
  antes de retornar e persiste Connected=false. Espera de kill limitada a5s quando
  worker já foi cancelado. Contexto termina antes de drenar SDK/handlers na saída.
- Repetir checks completos/race e rodada5; reconstruir imagem e repetir ambos
  ciclos antes da duração. Duração de2h ainda NÃO iniciada. Código alterou depois
  dos resultados de5b0e96e, portanto eles ficam intermediários, não prova final.
- Produção permanece sem mutações, sem novos acessos além das contagens registradas.

## Checks da correção da rodada4 (18:26 BRT)

- go build ./..., go vet ./..., go test ./... passaram, código0.
- go test -race dos três pacotes alterados passou, código0. Regressões da rodada4
  tiveram vermelho/verde antes da suíte completa. Iniciar rodada5 com mesmas opções.
- Importação direta de go.mau.fi/util apenas para KeyedMutex já distribuído pela
  SDK, sem nova versão baixada; go mod tidy atualizado. Zero valor funciona e
  remove locks por referência quando não existem usuários/esperas.
- Relatórios de5b0e96e conservados como intermediários; nova candidata terá outro
  source/imageID e repetirá ambos ciclos/mídia/duração. Não houve publicação.

## Quinta revisão e compatibilidade da consulta de números (18:38 BRT)

- Rodada5 encerrou com1P2: novaSDK responde IsOnWhatsApp com canonicalJID=LID e
  PhoneNumber=PN; performCheckUser antigo consultava GetLIDForPN com LID e alterava
  os campos públicos JID/RemoteJID. Achado aceito, sem novos achados de lifecycle.
- Extraído mapper sem mudar comportamento para prova. Teste RED mostrou PN-only
  lookup recebendo LID e campo público retornandoLID. GREEN após preferir PN
  conhecido e usar LID fornecido direto; formato antigo e usuário ausente cobertos.
- Prova HTTP local na imagem1bd56bf (antes do fix) confirmou: usuário de teste
  encontrado, JID/RemoteJID não preservamPN e LID não fornecido. Não imprimir os
  valores. Repetir após rebuild e conferir envio com formatação padrão, além dos
  ciclos comparáveis com formatJid=false.
- API da imagem1bd56bf after-4e718ba0 passou10/10 Completed, entrada30/30, saída10/10,
  sem panics/streams. Socket1bd em andamento (log candidate-socket-1bd56bf.log).
  O novo fix é de resposta HTTP; ainda assim imagem final deve identificar o novo
  commit e repetir comparação antes da duração.
- Checks/revisão6 e rebuild a seguir. Duração de2h continua pendente, sem abreviar.

## Checks após adaptação PN/LID (18:39 BRT)

- Build/vet/suíte completos código0, race dos três serviços código0.
- Socket1bd after-socket-4ec7cd29 passou10/10 Completed, entrada30/30, saída10/10,
  sem panics/streams, dez restarts induzidos e remetente autenticado em todas quedas.
- Relatórios1bd preservados como intermediários porque /user/check foi adaptado
  depois. Próxima imagem deve validar HTTP PN/LID verde, envio com formatação
  padrão, repetição dos ciclos e mídia e duração contínua≥7200s, sem abreviar.
- Relatório consolidado preparado como RASCUNHO em whatsmeow-validation.md;
  campos pendentes permanecem explícitos e serão preenchidos com execução final.

## Sexta revisão e proxy global (18:52 BRT)

- Rodada6: 1P2, globalproxy perdido quando ForceReconnect passou ao caminho comum
  e instância tinha Proxy="null". Aceito e corrigido; demais caminhos reviewer não
  apontou novos achados. Roteamento global preservado inclusive string vazia/objeto
  vazio e sem credenciais (proxy pode não usar autenticação).
- Teste real de seleção StartInstance pausa inicialização antes de SQL/SDK, captura
  ClientData, cancela/aguarda worker sem rede. RED nas3formas vazias com globalproxy;
  GREEN nos5casos (global3, semproxy, proxy de instância). Construção do cliente
  aceita configuração de instância omitida e usa fallback global já existente.
- Imagemea877fb passou HTTP PN/LID verde e envio textual defaultformat recebido.
  API after-450d363f passou10/10 Completed, entrada30/30 e saída10/10; sem panics,
  streams ou callbacks indevidos. Código de proxy alterado depois, logo manter
  relatório intermediário. Preparar checks/rodada7/rebuild e repetir comparação.
- Nenhuma duração de2h foi iniciada. Nenhuma alteração em produção/publicação/push.

## Checks do fallback global (18:55 BRT)

- Build/vet/suíte completos e race dos três serviços passaram após ajuste do proxy.
- Preparar rodada7 no próximo commit, mesma configuração do Codex, e rebuildlocal.
  Sem novas alterações de estratégia/flags da SDK. Referência continua válida;
  repetir os10ciclos de cada método na imagem que vier com revisão limpa.

## Esclarecimento ao Tuan e comparação final em curso (19:12 BRT)

- Tuan perguntou sobre o teste que o sandbox do revisor restringiu e sobre tráfego
  contínuo. Esclarecido: o pacote completo foi repetido no Mac com -count=1 e passou;
  ambiente principal sempre foi o repositório/lab local, não produção.
- Duração planejada: conexão contínua≥2h, lote de6mensagens (texto/PNG/tom1s em
  cada sentido) a cada300s, até25lotes/150mensagens; estado conferido a cada2s,
  entregas pelo webhook local e hashes/tipos. Sem quedas induzidas durante duração.
- Finalf072 API after-07bec535 concluiu10/10 Completed, entrada30/30 e saída10/10,
  sem panics/streams e0callbacks espúrios. Socket after-socket-b8739baa em execução,
  sessão2131, em7/10ciclos com7conclusões na última amostra. Só iniciar mídia/duração
  depois da conclusão. Código da imagem não mudou após revisão limpa.

## Início da duração final (19:15 BRT /22:15 UTC)

- Mesma imagem/código f072697 com revisão7limpa e checks completos verdes.
- Media-after-7c526e36 prova curta passou6/6 em6,322s: texto/imagem/áudio duas vias.
- Iniciado o comando de duração7200s/interval300s sob caffeinate -i temporário,
  sem alterar preferências de energia. PTY permite interrupção controlada; aplicativo,
  PostgreSQL e webhook continuam exclusivamente locais. Nenhuma queda induzida.
- Previsão aproximada:21:15BRT, incluindo último lote. Só marcar pass após relatório
  completo com elapsed≥7200, entregas, amostras de autenticação e logs conferidos.
- Ao concluir: consolidar tabela, revisar docs/PRbody, commitar só evidências/docs,
  push apenas academia e abrirPR no fork. Sem merge, publicação ou deploy.

## Duração — primeiro checkpoint (19:25 BRT)

- e282b2eb em andamento, aproximadamente10min:2lotes/12entregas, dois clientes
  autenticados,0restarts/0panics/0stream_errors desde início. Medição em progresso,
  não conclusão de2h. Relatório e JSON atualizados automaticamente por lote.
- Código/harness comparados comf072697: nenhum diff em pkg, Dockerfile, go.mod/sum
  ou scriptsPython. Somente docs/evidências mudaram após revisão7limpa.
- Relatório consolidado com comparação final de20ciclos preenchido; duração continua
  pendente. PRbody rascunhado em .code-review-log/pr-body-draft.md, com marcadores
  de duração pendentes. Não publicar PR com esses marcadores nem antes do teste.

## Recibos durante a duração (19:38 BRT)

- Metadados do receptor confirmaram eventos Receipt desde o início da janela:
  20 no receptor e 15 no remetente nesta amostra. São contagens de eventos, não
  garantia de exatamente um recibo por mensagem. Nenhum ID/telefone/conteúdo foi
  exposto. Estado seguro em soak-receipt-check.json, ignorado.
- Essa observação complementa as entregas correlacionadas por ID/tipo. A duração
  continua em andamento e ainda não foi considerada aprovada.

## Duração — 30 minutos (19:46 BRT)

- Sete lotes concluídos, 42/42 entregas, ambos clientes autenticados.
- Desde o início: zero reconexões, panics e erros de stream nos logs locais.
- A comparação válida de ciclos, mídia curta e revisão está concluída; a execução
  longa continua na mesma imagem. Não antecipar aprovação do período de duas horas.
- Permissão de push no fork confirmada por metadados do GitHub; branch remota ainda
  não existe. Nenhum push ou PR executado. Main remoto continua na base 8d77799.

## Interrupção real e pedido de decisão (19:59 BRT)

- Janela:22:15:21.142212UTC até22:56:30.022120UTC;2468,498s. Script encerrou2 com
  STOP:authenticationlost. Último lote40min foi entregue: total54/54,9lotes.
- Log estrutural sanitizado: stream:error com código503 às22:56:28.428517730UTC;
  nenhuma tag/atributo de ackstatus/media. Não é a assinatura exata relatada na
  produção. Nenhuma mensagem bruta/telefone/token foi exposto na análise.
- O próprio aplicativo fez recuperação natural do receptor; logs mostram Preview1
  e Completed1 após o início da janela, conectado/autenticado de novo. Sem panic.
  Não foi enviado novo probe após essa recuperação; não afirmar recebimento validado
  depois dela, nem estabilidade de2h. Script não fez intervenção de recuperação.
- Estado preservado; pergunta ao Tuan enviada antes de retomar, trocar critério,
  modificar biblioteca ou publicar PR. Esta parada decorre da regra expressa do
  usuário e do critério do roteiro, não de sandbox nem de achado pendente do Codex.
- Código f072697 continua com revisão7limpa/build/vet/test/race verdes. Somente
  documentação/evidência é atualizada. Nenhuma alteração ou novo acesso à produção.

## Esclarecimento: quem fez a reconexão automática

- Tuan perguntou se a reconexão foi manual, da EvolutionGo ou da whatsmeow, e se a
  versão em produção já faria isso. Código atual, base main e duas versões fixadas
  da biblioteca foram comparados; nenhuma nova intervenção no laboratório/produção.
- No evento 503 da duração, não houve chamada manual a endpoint, restart, controle
  de proxy ou comando de recuperação. O roteiro de mídia apenas envia, monitora e
  para na perda de conexão. Diagnóstico registrou um restart do handler da EvolutionGo.
- A biblioteca emite events.Disconnected. A lógica interna da EvolutionGo recebe o
  evento e chama ReconnectClient; a biblioteca executa a nova conexão/sincronização.
  EnableAutoReconnect=false permanece tanto na base main (linha431) quanto na
  candidata (linha559), desativando o ciclo nativo de autoreconexão da whatsmeow.
- O mesmo handler automático existe na imagem de produção 0.7.2-0.1.0. No teste
  local da referência before-socket-a70c1164, ela realizou dez reconexões automáticas,
  com dez conclusões de sincronização e todas as entregas. SDK b572 também encaminha
  stream:error503 para Disconnected; sua rotina nativa retorna quando o flag é false.
- Portanto, a capacidade de reconectar sozinha já existia. A candidata altera a
  coordenação/limpeza da geração anterior e atualiza a SDK. Reconectar não comprova,
  sozinho, recebimento estável: após o 503 observado falta enviar novo probe, e a
  duração continua interrompida. Perguntas do Tuan não autorizaram retomar o teste;
  a escolha anteriormente solicitada permanece pendente.

### 2026-11-11, 22:34 BRT — Medição de pools: preparação e regressões

- Plano registrado antes dos testes. API original instalada localmente, preservando
  PostgreSQL tmpfs/licença/pareamentos. Ao parar a API candidata, contagem de
  offline_sync_auth caiu a0; a medição não inclui o observador no banco postgres.
- Primeiro roteiro e01acf67 parou antes da amostra inicial: o marcador criado pelo
  agente não seguia a allowlist do receptor. Não é falha de entrega da aplicação
  nem evidência de vazamento. Nenhuma reconexão medida nessa tentativa.
- Regressão Python verificou o contrato com receiver.MARKER: RED falhou no warm-up;
  GREEN passou após usar o formato EVOSYNC existente. Limite de ciclos10..99.
- TestDeviceStoreIsReusedAcrossSequentialReconnects cobre início+20reconexões.
  RED com get retornando open() sem cache: reconnect1 criou outro store, exit1.
  GREEN restaurando inicializador compartilhado: todos TestDeviceStore passaram, exit0.
- Não houve mudança adicional no código da aplicação; inicializador já estava na
  imagem f072697. Apenas teste de regressão e roteiro de medição foram adicionados.
- A primeira troca confirmou licença ativa e ambos os dispositivos autenticados.
  Próximo passo: repetir a referência com marcadores válidos, depois candidata.

### 2026-11-11, 22:37 BRT — Referência acumula pools, medição concluída

- Execução b014b243, harness86eb808, imagem original30cfa84:20reconexões do receptor.
  Inicial4, sequência6,8,...,44; final44 após30s; delta+40. Todas ociosas nas amostras.
- Completed20/20, entregas20/20, remetente autenticado20/20, sem restart espontâneo,
  panic ou stream:error. --expect-stable terminou exit2 como esperado: RED real.
- Defeito confirmado na integração original: sqlstore.New abre pool por início,
  sem Close do container aposentado. Não atribuir automaticamente o congelamento
  de produção a este achado. Não foi consultado banco de produção.
- Próximo passo: trocar somente API pela candidata4dc9496 e repetir vinte ciclos.

### 2026-11-11, 22:43 BRT — Pools concluídos e nova duração autorizada

- ca27b001 terminou stable, exit0:3→2, faixa2..3,20sync/20provas, remetente
  autenticado em todas as amostras, sem panics/stream errors/restarts espontâneos.
- Referência b014b243:4→44, delta+40, exit2 esperado. Relatório consolidado
  2026-11-11-whatsmeow-auth-pools.md e tabelas completas por execução.
- Ambos os números autenticados ao final, candidata4dc9496 restaurada, proxy aberto.
  Nenhum acesso a produção ou mudança adicional no aplicativo.
- Tuan autorizou repetir2h com quedas aceitas somente se reconexão+Completed+entrega
  ocorrerem até60s; pediu contagem. Planejamento registrado antes de mudar roteiro.
- Próximo passo: observador de eventos/estado e prova imediata após cada queda,
  testes de regressão incluindo queda muito breve não percebida na amostra de auth,
  falha em sync/entrega/timeout; revisão do Codex; execução longa.

### 2026-11-11 — Roteiro de recuperação preparado, antes de iniciar2h

- Novo modo explícito --recovery-seconds60; padrão estrito preservado. Observa
  Disconnected/autenticação, exige Connected+Completed+prova recebida no limite,
  conta quedas por papel e compara com restart logs. Sem reconexão manual/queda forçada.
- Mensagens periódicas continuam texto/imagem/áudio nas duas vias,6/lote a cada300s.
  Provas de recuperação extras e tentativas interrompidas têm contagens separadas.
- Regressores temporais sem rede real: queda normal, queda entre amostras, ambos
  os dispositivos, webhook atrasado/deduplicação, sync ausente, entrega ausente,
  limite ultrapassado e divergência entre observador/logs.
- RED recriando critério estrito anterior: recuperação normal lança authentication
  lost, exit1. GREEN com modo novo:11testes Python passaram, exit0. Um caso de
  evento atrasado que antecipava o início da queda falhou antes do ajuste e passou
  depois; limite60s revalidado mesmo para queda previamente marcada recuperada.
- Próximos passos: conferir smoke real6mensagens, commitar roteiro e rever com
  CodexCLI gpt-6.1-sol high até limpo. Então iniciar7200s; ainda não iniciado.

### 2026-11-11 — Confirmação de sync pelo log e preflight separado

- Fonte real: handler registra Completed, mas dispatchEvent não tem rota desse
  evento. Metadados do receptor não continham Completed nem na recuperação503
  anterior. Corrigido o novo observador para usar timestamps do log Docker local.
- Parser retorna apenas papel/horário; leitura incremental com sobreposição1s e
  deduplicação. Nenhum log bruto persistido/impresso. RFC3339Nano do Docker exigiu
  truncar nanosegundos para Python3.9; fixture RED0eventos, GREEN1evento, leitura
  real GREEN7Completed locais. Todos12testes Python passaram após os ajustes.
- RED com suposição de Completed via webhook: recovery limit; GREEN usando log.
- Antes de iniciar2h, fazer preflight local de30s:6mensagens e uma única queda
  TCP controlada do receptor por2s, com gate restaurado em finally. Validar
  observador/Completed/prova/contagem1; separar essa queda induzida das naturais
  da duração. Mesmo ambiente/números exclusivos já autorizados; nenhum acesso remoto.
- Review9 ainda roda no snapshot14b5fa5; ajustes de parser serão nova rodada após
  seu resultado. O teste de7200s só inicia após revisão limpa do roteiro ajustado.

### 2026-11-11 — Preflight aprovado e achadoR9 corrigido

- Preflight f21d35c7:31.887s,6/6mensagens periódicas; uma ação de queda TCP induzida,
  proxy fechou2túneis,1restart/1queda do receptor e0do remetente. Recuperação com
  Connected+Completed+prova recebida em3.943s. Sem panics/stream errors. Não conta
  como duração/natural. Gate restaurado, sem comando manual de reconexão.
- R9 trouxe1P2 no roteiro: webhook atrasado após a prova gerava outra queda falsa.
  RED reproduziu (amostra12s, recuperação14.5s, recibo15s). GREEN13testes após usar
  horários originais dos logs locais para Disconnected/Connected/Completed.
  Leitura incremental/deduplicada; não expõe linhas brutas nem altera a API.
- Todos os14achados do Codex até aqui corrigidos com regressão; nenhum rejeitado.
  Nova rodada necessária no roteiro corrigido antes de iniciar7200s.

### 2026-11-11, 23:04 BRT — Preflight final no código revisado emR10

- 4a5f41a2, harness098d8bd, controlado:6/6mensagens,1queda induzida do receptor,
 0remetente,1recuperação automática com sync/prova em4.573s,32.479s de execução.
 0panics/stream errors. Gate aberto após controle, pareamentos preservados.
- Timestamps originais dos logs confirmados em execução real; nenhum comando de
 reconexão manual. Relatório marcado controlled_preflight para não misturar taxas.
- R10 ainda em execução no snapshot098d8bd; nenhum teste longo iniciado ainda.

### 2026-11-11 — R10: janela final de medição alinhada

- R10 encontrou1P2 no roteiro: check final podia validar queda nova depois da
  captura antiga de contadores e reprovar por divergência. RED reproduziu; GREEN
  com14testes Python após alinhar os horários de corte com Docker --until.
- Finalização observa/recupera primeiro, registra observed_until_utc e coleta
  contadores no mesmo intervalo. Leitura de lifecycle usa corte fixo por amostra;
  eventos posteriores ao corte final ficam fora do intervalo concluído.
  Diagnóstico de erro não sobrescreve contadores usados no resultado.
- Nenhuma mudança no aplicativo/imagem. Próximo: smoke do novo finalizador,
  commit e revisão seguinte até limpa; só então iniciar7200s.

### 2026-11-11, 23:16 BRT — Smoke do finalizador passou; R11 em andamento

- 5b135557, harness46fa181:6/6entregas,8.032s,semquedas. Novo observed_until_utc
  compartilhado entre observador e contadores funcionou contra logs Docker reais.
- go build ./... e go vet ./... passaram novamente; go test ./... já passou
  com a regressão nova de store. Nenhuma alteração adicional no aplicativo Go.
- R11 em andamento em46fa181 (sessão77929); arquivo .code-review-log/round-11.txt.
  Não trocar snapshot enquanto rodar. Ainda não iniciar7200s até vir limpa.

### 2026-11-11, 23:22 BRT — R11 limpa; início autorizado da duração

- R11exit0: sem novos achados, snapshot46fa181.15achados totais corrigidos,
  3P1/12P2, nenhum rejeitado/adiado. Registro consolidado atualizado.
- Smoke5b135557 passou6/6 e finalizador com corte fixo contra Docker real.
- Próxima ação imediata: caffeinate -i python3 -u scripts/offline-sync/media_traffic.py
  --label after --duration-seconds7200 --interval-seconds300 --recovery-seconds60.
  Sem injeção de falhas nessa execução. Logs privados: soak-recovery-46fa181.log.
- Registrar ID da execução/sessão após iniciar, checkpoints/contagens ao longo,
  resultado final antes de abrir PR. Imagem do aplicativo permanece4dc9496/f072697.

Execução longa iniciada: d147ec0f, sessãoPTY49229, started_utc=2026-11-12T02:23:38.873122Z.
Harnês3abf955 (código revisto46fa181), imagem4dc9496/f072697.
Não provocar falha, chamar reconexão manual, parear, trocar API ou rodar outro teste.
Monitorar report/status/heartbeat, registrar quedas/resultados; aguardar exit antes de PR.

Checkpoint02:26UTC: d147ec0frunning,2.6min,1lote,6aceitas/6entregues,
quedas target0/sender0, heartbeat02:26:14UTC. Monitorar até terminar; sessão49229.

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 5.1, "batches": 2, "accepted": 12, "delivered": 12, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.1}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 10.5, "batches": 3, "accepted": 18, "delivered": 18, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.8}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 15.5, "batches": 4, "accepted": 24, "delivered": 24, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.9}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 20.6, "batches": 5, "accepted": 30, "delivered": 30, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.6}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 25.6, "batches": 6, "accepted": 36, "delivered": 36, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.2}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 30.6, "batches": 7, "accepted": 42, "delivered": 42, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.8}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 35.6, "batches": 8, "accepted": 48, "delivered": 48, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.4}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 40.6, "batches": 9, "accepted": 54, "delivered": 54, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.5}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 45.6, "batches": 10, "accepted": 60, "delivered": 60, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.0}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 50.7, "batches": 11, "accepted": 66, "delivered": 66, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.8}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 55.7, "batches": 12, "accepted": 72, "delivered": 72, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.3}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 60.7, "batches": 13, "accepted": 78, "delivered": 78, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.1}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 65.7, "batches": 14, "accepted": 84, "delivered": 84, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.9}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 70.7, "batches": 15, "accepted": 90, "delivered": 90, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.6}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 75.7, "batches": 16, "accepted": 96, "delivered": 96, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.5}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 80.8, "batches": 17, "accepted": 102, "delivered": 102, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.1}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 85.8, "batches": 18, "accepted": 108, "delivered": 108, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.0}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 90.8, "batches": 19, "accepted": 114, "delivered": 114, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 1.8}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 95.8, "batches": 20, "accepted": 120, "delivered": 120, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.6}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 100.8, "batches": 21, "accepted": 126, "delivered": 126, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.1}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 105.0, "batches": 21, "accepted": 126, "delivered": 126, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.1}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 110.0, "batches": 23, "accepted": 133, "delivered": 133, "drops": {"target": 0, "sender": 0}, "recovered": 0, "health_age_seconds": 0.3}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 115.0, "batches": 24, "accepted": 140, "delivered": 140, "drops": {"target": 1, "sender": 0}, "recovered": 1, "health_age_seconds": 0.1}

Duração d147ec0f — checkpoint: {"status": "running", "minutes": 120.1, "batches": 25, "accepted": 146, "delivered": 146, "drops": {"target": 1, "sender": 0}, "recovered": 1, "health_age_seconds": 0.7}

Duração d147ec0f — checkpoint: {"status": "pass", "minutes": 120.1, "batches": 25, "accepted": 150, "delivered": 150, "drops": {"target": 1, "sender": 0}, "recovered": 1, "health_age_seconds": 46.9}

### 2026-11-12,01:26BRT — Duração final passou e gates de PR concluídos

- d147ec0fstatuspass,elapsed7206.791s,25lotes/150entregues+1prova,3660amostras.
 1queda natural receptor,0remetente, recuperada5.181s.0panics/stream errors.
 Sessão49229exit0 e watcher427encerrados; sem tráfego adicional após término.
- Ambosautenticados; authDBlocal2idle; proxyaberto/rejected_auth0. Labpreservado.
- SSH somente camposNome/Image: ambosserviços seguem no digest5c413...3c68.
 Nenhuma consultaDB/segredo/temporário/escritaEC2.
- Forkmain8d77799, PR/branch ainda ausentes. Remotoacademiaexato conferido;
 gofmt11arquivosGo limpo. Próximaação: commit/pushacademia/PR e parada.

### 2026-11-12 — PR aberto e parada

- Push exclusivamente para academia/fix/whatsmeow-offline-sync concluído.
- PR inglês convencional aberto no fork, base main: https://github.com/performance-academia-lendaria/evolution-go/pull/2
- Corpo contém problema/causa demonstrada e hipótese aberta, tabela antes/depois,
 2h aprovadas, testes,11rodadas de revisão, riscos/migração e rollback5c413...3c68.
- Nenhum pushorigin, merge, publicação de imagem, deploy ou escrita em produção.
 Tráfego encerrado, ambos os números autenticados, PG/licença/pareamentos preservados.
- PARADA conforme fase5. Próximas ações exigem solicitações explícitas individuais.
