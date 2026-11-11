# Diário da investigação da sincronização offline do WhatsApp

## Ponto de retomada

Atualizado em 2026-11-11, Fase 2 em andamento. SDK oficial atualizado no código;
lab ainda roda imagem de referência, com licença e dois pareamentos preservados.

- **Etapa atual:** adaptar incompatibilidades de compilação e concluir checks;
  preparar imagem candidata para validação local. A causa de produção não foi provada.
- **Branch:** `fix/whatsmeow-offline-sync`.
- **Base:** `8d7779988d435842570460f7aeb07ecb953ba548` (`main`). Consultar
  `git log -3 --oneline` para os commits locais de documentação/preparação.
- **Plano completo:** [plano de trabalho](../plans/fix-whatsmeow-offline-sync.md).
- **Próximo passo:** concluir build/vet/suíte; commitar candidata; construir imagem
  linux/amd64 com contexto Git sem segredos; preservar bancos temporários internamente
  e trocar somente API local. Repetir os dois experimentos, mídia e duração ≥2h.
  [Análise dos commits/opções](2026-11-11-whatsmeow-upgrade-analysis.md).
- **Antes:** API `588b5cb3` e socket `1d697be3` encerrados, 10 ciclos cada,
  sem congelamento/perda. Preview 20/20, Completed 0/20. Tuan autorizou prosseguir
  com candidata experimental apesar da não reprodução. Não há experimentos ativos.
- **Dependência do Tuan:** dois números exclusivos de teste confirmados e ambos
  pareados. Não é necessário novo QR para as sessões já salvas.
- **Recursos locais ativos:** containers `evo-offline-sync-lab-api`,
  `evo-offline-sync-lab-receiver`, `evo-offline-sync-lab-postgres` e
  `evo-offline-sync-lab-proxy`; redes
  `evo-offline-sync-lab-data` (interna) e `evo-offline-sync-lab-egress` (saída).
  PostgreSQL temporário usa tmpfs. Nenhum recurso de produção montado.
- **Acesso local:** `http://127.0.0.1:18080/manager`; somente a API publica porta,
  restrita a `127.0.0.1:18080`. Banco e receptor não publicam portas.
- **Estado local restrito e ignorado:** `build/offline-sync-lab/`; `api.env` e
  `postgres.env` contêm apenas credenciais novas do laboratório e não devem ser
  impressos. Diretórios 0700; arquivos de configuração/identidade 0600.
- **Proxy de falha:** somente `target` está configurado para seu túnel local.
  Remetente direto, sem proxy. Controle em loopback 8083 dentro do container;
  sem porta publicada. Configuração/credenciais geradas em `proxy.json` e
  `proxy.env`; prova de validação em `proxy-validated.json`.
- **Processos em execução:** os quatro containers acima e a página auxiliar
  `python3 scripts/offline-sync/lab.py qr-page`, loopback 18081, sessão de execução
  `57886`. Experimentos socket `46833` e API `58062` encerrados; nenhum teste ou
  revisão Codex em execução. Containers preservados com os dois pareamentos e licença.
- **Segredos:** nenhuma licença ou credencial de produção lida ou copiada. A chave
  administrativa do laboratório foi copiada para a área de transferência e, após
  autorização explícita do Tuan às 14:42 BRT, exibida no chat. Seu valor não consta
  em arquivos versionados. A exceção vale somente para essa chave de teste.
- **Produção:** nenhum acesso à EC2 ou aos bancos nesta sessão; nenhuma alteração.
- **Push, PR e revisão Codex:** ainda não executados. Build/vet/suíte em validação.
- **Teste de regressão Archive:** primeiro vermelho confirmado na biblioteca
  antiga e após atualização; fix já verde nos três casos. Regressões de reconexão
  também com vermelho/verde; suíte completa e testes com imagem candidata pendentes.
- **Limpeza disponível, não executada:**
  `python3 scripts/offline-sync/lab.py down`; apaga o banco temporário e preserva
  arquivos locais para limpeza explícita. Não rodar durante a ativação/medição.

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

## Comparação dos dois métodos na referência atual

| Indicador | Rota ReconnectClient | Queda TCP real só no receptor |
|---|---|---|
| Execução | `before-588b5cb3` | `before-socket-1d697be3` |
| Ciclos com queda e reconexão confirmadas | 10/10 | 10/10 |
| Sockets encerrados pelo controle | Não se aplica | 10 |
| Reinícios automáticos por Disconnected | 0 | 10 induzidos |
| Envio aceito durante queda confirmada | 10/10 | 10/10 |
| Entrada antes/durante/depois no webhook | 30/30 | 30/30 |
| Saída do receptor recebida no remetente | 10/10 | 10/10 |
| Preview / Completed | 10 / 0 | 10 / 0 |
| Panics / erros de stream nas janelas | 0 / 0 | 0 / 0 |
| Duração | 31min12s | 32min29s |
| Incidente de recebimento congelado | Não reproduzido | Não reproduzido |

Ambos os testes usam a mesma imagem e dependência originais. Esta tabela compara
métodos de queda, **não** uma correção antes/depois. As provas iniciais adicionais
também chegaram; não estão somadas aos 30 marcadores por execução.

## Comparação antes e depois

| Medida | Referência `main` / imagem atual | Candidato |
|---|---|---|
| Identidade | `8d77799`; imagem local identificada acima | Não criado |
| Licença local | **Ativa — ativação pelo Tuan, conferida às 14:43 BRT** | Não executado |
| QR/pareamento dos dois números de teste | Concluído; ambos autenticados após preparação | Não executado |
| Ciclos confirmados de reconexão | **10/10 por API + 10/10 por socket**; detalhes nas tabelas acima | Não executado |
| Reconexões com `OfflineSyncCompleted` | **Medição anterior inválida — contador corrigido e referência em repetição** | Não executado |
| Mensagens antes/durante/depois recebidas no webhook | **30/30 por método (60/60)**, além das provas iniciais | Não executado |
| Mensagens de saída recebidas no remetente | **10/10 por método (20/20)** | Não executado |
| Reinícios por Disconnected | 0 no método API; **10 induzidos** no método socket | Não executado |
| Panics e erros de stream do processo | **0 e 0** nas janelas | Não executado |
| Teste de duração ≥ 2 horas | Não executado | Não executado |
| Envio texto/mídia e recepção texto/áudio/imagem | Não executado | Não executado |
| Build, vet e suíte Go | Não executado | Não executado |
| Revisão Codex | Não executado | Não executado |

## Conclusões e decisões em aberto

A hipótese da whatsmeow defasada permanece sem teste causal. Dez reconexões por
API e dez quedas reais de TCP não reproduziram a perda de recebimento, apesar da
falta de Completed. Não há correção nem conclusão de estabilidade de duas horas.
Tuan propôs seguir com a correção na biblioteca; a Fase 2 foi retomada como
candidata experimental. Fases 3 a 5 permanecem pendentes. A conclusão final e o
eventual PR deverão distinguir validação local de confirmação da causa de produção.

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
