# Diário da investigação da sincronização offline do WhatsApp

## Ponto de retomada

Atualizado em 2026-11-11, 14:22 BRT / 17:22 UTC.

- **Etapa atual:** Fase 0 concluída quanto à documentação; preparação da Fase 1.
- **Branch:** `fix/whatsmeow-offline-sync`.
- **Base e HEAD inicial:** `8d7779988d435842570460f7aeb07ecb953ba548` (`main`).
- **Plano completo:** [plano de trabalho](../plans/fix-whatsmeow-offline-sync.md).
- **Próximo passo:** preparar o roteiro de laboratório local e verificar somente
  o estado da licença. Não iniciar a Fase 2 sem reprodução registrada.
- **Dependência do Tuan:** confirmar número exclusivo de teste disponível para QR
  e outro remetente para enviar mensagens nas janelas de queda/recuperação. A
  pergunta foi feita; a resposta recebida pediu documentação prévia e ainda não
  confirmou a disponibilidade dos números.
- **Recursos criados até este checkpoint:** branch e os dois documentos de plano
  e diário. Nenhum container, rede, volume ou banco de teste criado.
- **Processos em execução:** nenhum iniciado por esta investigação.
- **Segredos:** nenhum arquivo de segredos aberto; nenhuma licença ou credencial
  de produção lida ou copiada.
- **Produção:** nenhum acesso à EC2 ou aos bancos nesta sessão; nenhuma alteração.
- **Push, PR, build, testes e revisão Codex:** ainda não executados.

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

## Comparação antes e depois

| Medida | Referência `main` / imagem atual | Candidato |
|---|---|---|
| Identidade | `8d77799`; imagem local identificada acima | Não criado |
| Licença local | Não verificada | Não executado |
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
