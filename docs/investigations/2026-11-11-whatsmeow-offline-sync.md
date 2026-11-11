# Diário da investigação da sincronização offline do WhatsApp

## Ponto de retomada

Atualizado em 2026-11-11, 14:26 BRT / 17:26 UTC.

- **Etapa atual:** preparação da Fase 1 **bloqueada por licença local inativa**.
- **Branch:** `fix/whatsmeow-offline-sync`.
- **Base:** `8d7779988d435842570460f7aeb07ecb953ba548` (`main`). Consultar
  `git log -3 --oneline` para os commits locais de documentação/preparação.
- **Plano completo:** [plano de trabalho](../plans/fix-whatsmeow-offline-sync.md).
- **Próximo passo:** aguardar orientação do Tuan sobre licença própria de teste e
  disponibilidade dos dois números. Não fazer ativação nem contornar o gate. Após
  a resposta, consultar `python3 scripts/offline-sync/lab.py status` e retomar
  preparação do pareamento/ciclos. Não iniciar Fase 2 sem reprodução registrada.
- **Dependência do Tuan:** confirmar número exclusivo de teste disponível para QR
  e outro remetente para enviar mensagens nas janelas de queda/recuperação. A
  pergunta foi feita; a resposta recebida pediu documentação prévia e ainda não
  confirmou a disponibilidade dos números.
- **Recursos locais ativos:** containers `evo-offline-sync-lab-api`,
  `evo-offline-sync-lab-receiver` e `evo-offline-sync-lab-postgres`; redes
  `evo-offline-sync-lab-data` (interna) e `evo-offline-sync-lab-egress` (saída).
  PostgreSQL temporário usa tmpfs. Nenhum recurso de produção montado.
- **Acesso local:** `http://127.0.0.1:18080/manager`; somente a API publica porta,
  restrita a `127.0.0.1:18080`. Banco e receptor não publicam portas.
- **Estado local restrito e ignorado:** `build/offline-sync-lab/`; `api.env` e
  `postgres.env` contêm apenas credenciais novas do laboratório e não devem ser
  impressos. Diretórios 0700; arquivos de configuração/identidade 0600.
- **Processos em execução:** os três containers acima; nenhum comando de teste
  ou revisão em background. O bootstrap terminou com código 1 pelo gate de licença.
- **Segredos:** nenhum arquivo de segredos aberto; nenhuma licença ou credencial
  de produção lida ou copiada.
- **Produção:** nenhum acesso à EC2 ou aos bancos nesta sessão; nenhuma alteração.
- **Push, PR, build Go, suíte Go e revisão Codex:** ainda não executados.
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

## Comparação antes e depois

| Medida | Referência `main` / imagem atual | Candidato |
|---|---|---|
| Identidade | `8d77799`; imagem local identificada acima | Não criado |
| Licença local | **Inativa — bloqueio confirmado** | Não executado |
| QR/pareamento do número de teste | Não executado | Não executado |
| Ciclos confirmados de reconexão | 0 / mínimo 10 | Não executado |
| Reconexões com `OfflineSyncCompleted` | Não executado | Não executado |
| Mensagens antes/durante/depois recebidas no webhook | Não executado | Não executado |
| Quedas espontâneas por instância-hora | Não medido localmente | Não executado |
| Panics | Não medido localmente | Não executado |
| Teste de duração ≥ 2 horas | Não executado | Não executado |
| Envio texto/mídia e recepção texto/áudio/imagem | Não executado | Não executado |
| Build, vet e suíte Go | Não executado | Não executado |
| Revisão Codex | Não executado | Não executado |

## Conclusões e decisões em aberto

A hipótese da whatsmeow defasada permanece sem teste causal. Não há reprodução
local, correção, conclusão de estabilidade ou autorização para contornar etapas.
Confirmar número de teste, licença e execução da referência antes de decidir a
atualização. O plano completo define o que deve ser medido e o que exige parada.
