# Plano de correção da sincronização offline do WhatsApp

Atualizado em 2026-11-11, 16:20 BRT. Branch: `fix/whatsmeow-offline-sync`, criada a partir de
`main` em `8d7779988d435842570460f7aeb07ecb953ba548`.

## Objetivo e condição de conclusão

Restabelecer o recebimento estável depois de quedas e reconexões com a menor
mudança sustentada por evidência. A biblioteca whatsmeow defasada é uma hipótese,
não uma causa confirmada. O trabalho termina com um PR no fork, resultados
comparáveis antes/depois e uma proposta de implantação. Merge, publicação de
imagem e deploy ficam fora da autorização atual.

**Estado atual:** após as duas execuções sem reprodução, Tuan propôs prosseguir com
a correção na biblioteca. Fase 2 retomada como **candidata experimental**, mantendo
explícito que a causa de produção não foi confirmada. Primeiro avaliar/aplicar a
versão oficial mais recente; só criar patch próprio da biblioteca se houver defeito
específico demonstrado que a versão oficial não cubra. Produção continua somente
leitura; merge/publicação/deploy continuam sem autorização.

O [diário da investigação](../investigations/2026-11-11-whatsmeow-offline-sync.md)
é o ponto de retomada. Deve ser atualizado após cada etapa, decisão, experimento,
falha ou bloqueio, antes de interromper a sessão. Resultados não executados ficam
explicitamente pendentes; preparação de um teste não equivale à sua execução.

## Limites obrigatórios

- Produção é somente leitura. Não executar deploy, `docker service update`,
  restart, logout, exclusão de instância ou qualquer escrita na EC2 ou nos bancos
  `evolution-auth` e `evolution-instances`.
- Nunca testar em instâncias de produção, `evoapi1` ou `evoapi3`. Usar apenas
  Docker local, PostgreSQL descartável e número exclusivo de teste pareado pelo
  Tuan. Webhook exclusivamente local, nunca `api.superagentes.ai`.
- Não abrir arquivos de segredos, inspecionar ambientes completos de containers
  nem imprimir licença, tokens, credenciais ou connection strings. Comparações
  necessárias usam somente comprimento ou SHA-256. Credenciais novas do laboratório
  são geradas e consumidas automaticamente sem aparecer nos relatórios.
- Se for necessário ler logs da EC2, processar no servidor e retornar somente
  contagens e trechos sanitizados, com telefones substituídos por `<n>` e nenhum
  conteúdo de mensagem. Não deixar arquivos temporários no servidor.
- Push somente para `academia`, repositório
  `performance-academia-lendaria/evolution-go`, nesta branch. Nunca enviar para
  `origin`, que corresponde ao upstream `evolution-foundation/evolution-go`.
- Preservar os ajustes de versão/handshake dos commits `8b5ee5b`, `ac201ae`,
  `cc91d72`, `66734e1` e `3994d10`, e os testes existentes.
- Commits e PR em inglês, com assuntos conventional commits. Conversa em português.
- Se não houver reprodução, número de teste disponível, licença local ativa ou
  outra condição necessária, registrar o bloqueio e perguntar ao Tuan antes de
  contornar. Não avançar automaticamente à correção.

## Estado inicial e evidência disponível

Fonte histórica local, sem nova verificação em produção:
`~/Documents/GitHub-Projects/legendsagents/.local/investigations/2026-11-10-agente-nao-responde-whatsapp.md`,
seção de 2026-11-11.

- Imagem informada em produção: `tuanmedeiros/evolution-go:0.7.2-0.1.0`.
- Serviços informados: `evogoevoapi1_evogoevoapi1` e
  `evogoevoapi3_evogoevoapi3`, no alias SSH `aws-superagentes-evolution`.
- Incidente relatado: `Connected` seguido de `OfflineSyncPreview`, sem
  `OfflineSyncCompleted`; envio continua e recebimento/recibos param.
- Investigação anterior: cerca de 18 quedas/h no servidor, frequentemente após
  `stream:error` com ack de status/media; novo QR não resolve de forma duradoura.
- Panic relatado em `events.Archive`: conversão indevida para
  `map[string]interface{}`.
- Dependência em `main`:
  `go.mau.fi/whatsmeow v0.0.0-20260630180629-b572e5bcb92b`.
- A investigação anterior descartou bloqueio da fila pelo envio de webhook,
  que ocorre de forma assíncrona.
- O relato de 117 commits novos até 2026-11-10 será conferido contra o upstream
  quando a Fase 2 estiver autorizada pelo resultado da reprodução.

## Fase 0 — Documentação e preparação

- [x] Conferir branch, estado da árvore, remotos, versão de Go e Docker local.
- [x] Ler as instruções do repositório, a investigação e a skill de revisão.
- [x] Criar a branch solicitada a partir de `main`.
- [x] Registrar o plano completo, limites, critérios e ponto de retomada.
- [x] Confirmar disponibilidade do número de teste e de outro remetente. Tuan
  disponibilizou e pareou ambos; usar remetente local para tráfego automatizado.
- [x] Preparar bootstrap do laboratório e conferir estado da licença sem expor chave.
- [x] Resolver com o Tuan o bloqueio de licença local inativa. Ativada por ele e
  conferida pelo agente em 2026-11-11, 14:43 BRT. Pareamento e ciclos pendentes.

## Fase 1 — Reprodução antes da correção

### Ambiente e roteiro

1. Criar o roteiro reproduzível em `scripts/`, sem segredos versionados, com
   comandos de preparação, estado, pareamento, ciclos, relatório e limpeza.
2. Fixar a imagem de referência local por ID/digest, registrar arquitetura e
   relação com o commit de `main`. Não comparar uma referência de código incerta.
   Caso seja necessário build, usar contexto obtido de arquivos rastreados,
   sem copiar `.env` nem dados locais para o Docker.
3. Usar nomes exclusivos e identificação de propriedade dos recursos Docker.
   Validar que o daemon é local. Subir PostgreSQL temporário e receptor local,
   sem montar dados, arquivos, volumes ou segredos de produção.
4. Manter API, banco e receptor em rede interna e uma segunda rede para a saída
   da API. Com dois números no mesmo processo, usar inicialmente a rota local
   `/instance/reconnect` para disparar `ReconnectClient` somente no receptor,
   preservando remetente, banco e webhook. Se um teste de rede separado for
   autorizado posteriormente, garantir restauração mesmo em interrupção.
5. Restringir portas publicadas ao loopback. Guardar estado sensível somente em
   diretório local ignorado (`build/offline-sync-lab/`) com acesso restrito.
6. Consultar apenas o estado da licença. Se inativa, parar e pedir orientação;
   não copiar licença de produção, ativar automaticamente ou alterar o gate.
7. Após os pré-requisitos, parear o número exclusivo por QR. Conferir recebimento
   inicial e acesso do container ao webhook local.

### Medição

- Executar pelo menos dez ciclos confirmados de queda/reconexão na referência.
  Fixar duração da queda e janela de recuperação antes do primeiro ciclo, depois
  de conferir a semântica dos eventos da versão instalada. Registrar os valores.
- Enviar do outro número marcadores exclusivos antes, durante e depois de cada
  queda. Registrar confirmação do remetente; mensagem não enviada não pode ser
  contada como perda. Aguardar e conferir entrega ao webhook local.
- Correlacionar por ciclo a queda observada, o novo `Connected`, a prévia e a
  conclusão da sincronização, os marcadores recebidos e os panics. Separar eventos
  de pareamento inicial dos eventos de reconexão.
- Guardar apenas metadados necessários: horários, contagens, tipo de mensagem,
  hash de identificadores e marcadores artificiais do teste. Não guardar payloads
  completos, telefone, tokens, mídia ou mensagens pessoais.
- Registrar tentativas inconclusivas separadamente, inclusive queda não observada,
  falha do remetente, indisponibilidade do receptor ou expiração da janela.
- Separar quedas forçadas das espontâneas. Expressar a taxa espontânea por
  instância-hora local; as 18 quedas/h históricas são agregadas do servidor e não
  constituem o resultado local de referência.
- Se o defeito não aparecer em pelo menos dez ciclos, registrar o observado e
  parar para decisão do Tuan, sem atualizar a dependência.

**Saída obrigatória:** script, identidade da referência, configuração não sensível,
tabela por ciclo, resultado consolidado e decisão explícita de reprodução.

**Resultado da primeira execução:** concluída em 2026-11-11, 15:32 BRT;
[tabela por ciclo](../investigations/2026-11-11-offline-sync-before-588b5cb3.md).
Não reproduziu; nenhuma autorização inferida para atualizar a biblioteca. Pergunta
pendente: quedas reais de socket dirigidas ao receptor, teste de duração na versão
atual ou manter parado. Tuan escolheu quedas reais de socket. O roteiro inicial chama a rota de reconexão, não simula
`stream:error` de servidor nem o ack de status/media visto em produção.

### Extensão autorizada — queda real do socket do receptor

1. Acrescentar proxy HTTP CONNECT descartável, sem porta publicada, somente para
   o receptor; remetente permanece direto. O túnel encaminha bytes TLS sem
   descriptografar, imprimir ou salvar seu conteúdo.
2. Validar o proxy primeiro com TCP de eco sintético local: conexão, transporte,
   encerramento real de sockets, bloqueio temporário de novas conexões e restauração.
   Ainda não usar WhatsApp nessa verificação.
3. Aplicar proxy somente em `offline-sync-target` pela API local, reutilizando
   pareamento existente. A própria rota reconecta para aplicar; registrar essa
   preparação separadamente dos ciclos medidos. Não reiniciar a API/banco nem
   parear novamente. Confirmar remetente sem proxy e ambos autenticados.
4. Novo método do roteiro: fechar túneis ativos do receptor e segurar novos CONNECT
   por dez segundos. Confirmar queda observada, envio aceito durante a queda e
   remetente autenticado. Liberar túneis em `finally`; controle independente libera
   automaticamente em vinte segundos se o processo de teste morrer.
5. Aguardar a reconexão disparada pelo handler `Disconnected` original, sem chamar
   a rota `/instance/reconnect` nos ciclos. Registrar número de sockets fechados,
   restart automático e estado do proxy, além dos indicadores anteriores.
6. Manter dez ciclos, limites de 30/180 segundos e marcadores antes/durante/depois
   mais prova de envio do receptor. Salvar nova execução distinta da primeira.
7. Se reproduzir, preservar a sessão com falha e diagnosticar. Se não reproduzir
   ou houver outro bloqueio, parar novamente e consultar o Tuan antes de Fase 2.

**Resultado da extensão:** dez sockets efetivamente encerrados, dez `Disconnected`
com restart automático, remetente autenticado durante todas as quedas, entrega
completa nos dois sentidos. 32min29s de execução, encerrada em 2026-11-11, 16:20 BRT
como `not_reproduced`. [Tabela final](../investigations/2026-11-11-offline-sync-before-socket-1d697be3.md).
Nenhuma alteração de biblioteca autorizada por esse resultado. Pergunta pendente:
teste de pelo menos duas horas com texto/áudio/imagem, reconexões concorrentes
dirigidas ao receptor, ou manter parado.

## Fase 2 — Correção mínima condicionada à reprodução

**Alteração de sequência autorizada em 2026-11-11, após os testes:** Tuan sugeriu
prosseguir com correção na biblioteca apesar da não reprodução. Isso permite
preparar e validar a atualização como candidata; não transforma testes locais
verdes em prova de que o incidente em produção foi resolvido. Preservar os dois
resultados antigos e apresentar essa limitação nos resultados e no eventual PR.

Plano desta etapa: documentar os 117 commits e opções, provar o panic Archive com
teste na versão antiga, atualizar para `c88388f983b4` via `@latest`, ajustar a
compilação/Go mínimo, corrigir Archive com vermelho/verde e avaliar o ciclo de vida
de reconexão com teste antes/depois caso alterado. Depois retomar as Fases 3–5,
incluindo duração mínima de duas horas, mídia, imagem local e revisão obrigatória.

1. Registrar a evidência que permite iniciar esta fase.
2. Executar `go get go.mau.fi/whatsmeow@latest` e `go mod tidy`; registrar versão
   exata e commit resolvido, sem presumir que o upstream permanece igual ao relato.
3. Ler os commits primários entre `b572e5bcb92b` e a nova versão. Relacionar commit,
   alteração e impacto em sincronização offline, acks/`SynchronousAck`, sessão
   unificada no connect, keepalive/reconexão e app state.
4. Ajustar incompatibilidades de compilação. Decidir e registrar, com fundamento
   no código e na evidência do teste, se alguma opção nova precisa ser ativada.
   Não ligar opções por suposição.
5. Sempre que viável, medir primeiro a atualização isolada para distinguir o
   efeito da biblioteca dos outros ajustes. Uma melhoria no conjunto, sozinha,
   não prova qual mudança resolveu a causa.
6. Reproduzir o panic de `events.Archive` com teste unitário sobre o caminho real,
   registrar a falha na implementação antiga, corrigir e registrar o teste verde.
7. Examinar o ciclo de vida de `ReconnectClient`, inclusive callbacks atrasados e
   pedidos simultâneos. Garantir desconexão do cliente anterior e remoção do handler
   antes de iniciar outro para o mesmo device. Se precisar mudar, provar o defeito
   e a correção com teste apropriado, incluindo concorrência quando relevante.
8. Conferir o diff e os testes de versão/handshake do fork. Não fazer alterações
   alheias à correção sustentada pela investigação.

## Fase 3 — Validação antes e depois

- [ ] Formatar o código Go conforme `gofmt`/`make fmt` e conferir o diff resultante.
- [ ] `go build ./...` limpo.
- [ ] `go vet ./...` limpo.
- [ ] `go test ./...` limpo, inclusive testes de versão/handshake existentes.
- [ ] Registrar para cada regressão o comando e os resultados vermelho/verde.
- [ ] Se houver mudança concorrente, rodar teste com detector de race apropriado.
- [ ] Repetir o roteiro com o mesmo número exclusivo, número de ciclos, tempos,
  remetente, receptor e critérios da referência; registrar diferenças inevitáveis.
- [ ] Comparar conclusão de sincronização por reconexão, mensagens únicas recebidas
  por janela, perdas/atrasos, quedas espontâneas por hora e panics.
- [ ] Fazer teste de duração de pelo menos duas horas conectado, com tráfego
  periódico; fixar e registrar a cadência e todas as interrupções.
- [ ] Conferir envio de texto e mídia; recebimento de texto, áudio e imagem;
  QR/pareamento funcionando. Registrar cada resultado e lacuna de cobertura.
- [ ] Gerar imagem candidata local `linux/amd64`, registrar tag/ID/digest quando
  disponível, sem publicar. Não usar novamente a tag de produção.

Se a atualização não resolver, não declarar a hipótese confirmada nem produzir
um PR como correção comprovada. Registrar o resultado e consultar o Tuan antes
de ampliar o escopo ou contornar o teste.

## Fase 4 — Revisão obrigatória em ciclos

Usar a skill local
`~/.agents/skills/tm-codex-review-loop/SKILL.md`. O Tuan já escolheu o modelo e
esforço para todas as rodadas; não é necessário perguntar novamente.

```sh
codex review --base main -c model="gpt-6.1-sol" -c model_reasoning_effort="high"
```

Rodar em background, conferir branch/árvore/diff e não trocar de branch durante
a revisão. Registrar cada rodada e achado em
`.code-review-log/fix-whatsmeow-offline-sync.md` (diretório já ignorado).
Para cada achado: conferir evidência, aceitar e corrigir com teste que falha
antes/passa depois, ou rejeitar com justificativa. Repetir até o veredito limpo.
Manter no diário o resumo durável de convergência, decisões, rejeições e lacunas;
incluir as decisões operacionais e riscos no PR. A revisão não substitui os testes
com WhatsApp real.

## Fase 5 — PR e parada

1. Obter somente a referência da imagem em execução nos dois serviços por SSH,
   usando saída formatada de `docker service inspect` para o campo de imagem.
   Não inspecionar ambiente ou segredos. Registrar o digest efetivamente observado
   para rollback; um digest local da mesma tag não prova o digest de produção.
2. Concluir self-review, commits em inglês e conventional commits. Não incluir
   `AGENTS.md` não rastreado, credenciais ou dados brutos do laboratório.
3. Conferir o destino e fazer push exclusivamente de
   `fix/whatsmeow-offline-sync` para `academia`.
4. Abrir PR em inglês no fork seguindo `.github/pull_request_template.md`, com
   problema, causa demonstrada/hipóteses descartadas, mudanças, comparação
   antes/depois, testes, revisão Codex, riscos e rollback pelo digest observado.
   Não inventar número de issue nem resultados ausentes.
5. Entregar link do PR, resumo em português, tabela antes/depois e proposta de
   implantação. Parar sem merge, publicação ou deploy.

Proposta a validar posteriormente: publicar somente mediante pedido explícito;
primeiro `evoapi3`, observar 24 horas com métricas de recepção e sincronização,
depois `evoapi1` em janela combinada, com rollback pelo digest registrado.
Cada merge, publicação e deploy depende de pedido explícito do Tuan.

## Rotina de atualização e retomada

Antes de cada etapa, ler o estado atual do diário e conferir branch/árvore.
Depois de cada etapa, atualizar o checklist deste plano e acrescentar ao diário:
horário, ação, evidência, resultado, decisões, arquivos alterados e próximo passo.
Antes de encerrar ou interromper, registrar recursos locais ainda ativos,
processos em execução, arquivos sensíveis locais somente pelo caminho, bloqueios
e comando seguro de retomada/limpeza. Nunca depender apenas do histórico do chat.
