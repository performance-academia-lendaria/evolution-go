# Release 0.7.2-0.1.1 — plano e checkpoint

## Ponto de retomada atual

**Passos1–4 concluídos: merge, versão/tag/release, imagem publicada e rollback prontos.**
Sem deploy autorizado ou executado. Restam somente os registros finais no repositório.

- PR #2 integrado; origem imutável da imagem/tag: `11bb6e4514e0a40b9b0445941e1164acef29f830`.
- Versão0.7.2-0.1.1; tag Docker `tuanmedeiros/evolution-go:0.7.2-0.1.1`.
- Digest publicado e confirmado pelo Docker Hub: `sha256:57b22a4245695c10772915d3ceeef60a6eec06275bdf63ceec539deaf27a815c`.
- Image ID/config: `sha256:4e8d5a8d290166443669c6ec71514140f093f25cdb6105344473b8a288685940`; binárioSHA256 `76d5c51d032266c3697837ff52a615f9e0ebb95f8bad0ab6e91b661ec08f6c36`.
- GitHub release: https://github.com/performance-academia-lendaria/evolution-go/releases/tag/0.7.2-0.1.1 (pré-release conforme formatoSemVer do fork).
  Tag Git aponta ao commit da imagem; assets manifest/runbook/checksums conferidos.
- Imagem final testada: mídia6/6; API10+TCP10, Completed20/20, entrada60/60,
  saída20/20;0panics/stream errors; authDB2idle. Relatórios01255b29/55495343/5512b7fa.
- Duas tentativas do daemon deram timeout sem subir camadas; cliente temporário
  cranev0.22.1 no host publicou usando credenciais existentes, sem novo login.
  Pull imutável/config/labels/plataforma e Dockerload confirmaram artefato idêntico.
  Não houve rebuild, alteração de rede/proxy/TLS ou restartDocker.
- Runbook completo em `docs/releases/0.7.2-0.1.1.md` e assetrollback.md na release.
  Rollback: `tuanmedeiros/evolution-go:0.7.2-0.1.0@sha256:5c41352292072d0f533596389cc9445fc6d3ce1ce551aeb29dfe8b8e923a3c68`, manifesto disponível. Preservar ratchets atuais.
- Progresso detalhado local: build/release-0.7.2-0.1.1/metadata.json e progress.md.
  Publicação, tag e pull já terminaram; não aguardar sessões anteriores.
- Próximo: registrar changelog publicado, plano/resultados/runbook via PR de docs
  apenas no fork; limpar uploader temporário e parar. Não alterar/mover tag ou
  reconstruir versão publicada. Não fazer deploy. Proposta futura: evoapi3/24h,
  depois evoapi1 em janela combinada, cada um com autorização explícita.

## Autorização e limites

Tuan autorizou seguir até o passo4 do fluxo apresentado: merge do PR, preparação
version/tag/release, build/verificação/publicação da imagem, digest e rollback.
A etapa5 (deploy em produção) continua sem autorização. EC2 e bancos de produção
permanecem somente leitura. Nunca fazer push para origin; código e tags apenas
no fork pelo remoto academia. Não alterar a tag publicada0.7.2-0.1.0 ou latest.
Preservar arquivos pessoais AGENTS.md/untitled.md e todo estado privado do laboratório.
Não ler/imprimir credenciais. Docker/GitHub usam seus gerenciadores locais existentes.
Se faltar autenticação/permissão ou uma validação falhar, registrar e consultar Tuan.

## Estado antes desta etapa

- PR #2 aberto e mergeable, head0be09709c998242ca09ea4f6b71e68d09a6d50e9.
- Main do fork8d77799; VERSION0.7.2-0.1.0. Nenhuma GitHub release no fork.
- Política: docs/wiki/desenvolvimento/versionamento-fork.md. Correção compatível
  incrementa o patch próprio para0.7.2-0.1.1; VERSION é fonte de verdade.
- Código candidato f072697; roteiro revisto46fa181, R11limpa.15achados corrigidos.
  Build/vet/test/race e14testes Python verdes. Duração d147ec0f7206,791s aprovada:
 150/150+1prova, uma queda natural recuperada5,181s. Pool original4→44/candidata3→2.
- Imagem candidata local4dc9496; não publicada. A imagem final terá VERSIONnovo e
  metadados OCI do commit da main; não reaproveitar a tag definitiva para build de teste.
- Rollback registrado e reconfirmado nos dois serviços, sem alteração:
  tuanmedeiros/evolution-go:0.7.2-0.1.0@sha256:5c41352292072d0f533596389cc9445fc6d3ce1ce551aeb29dfe8b8e923a3c68.

## Execução planejada (documentada antes das mudanças)

1. Conferir PR/head/main, ausência da nova tag Git/release e tag Docker, destino
   academia e daemon Unix local. Não ler arquivos de configuração de credenciais.
2. Atualizar VERSION e changelog no PR ainda aberto; changelog inicialmente indica
   não publicado. Documentar autorização nova. Rodar teste de versão/changelog e
   checks pertinentes. Mudança de metadados não altera o código runtime revisto.
3. Enviar apenas academia; merge PR #2 com head esperado, preservando histórico.
   Atualizar main local com academia/main, preservando arquivos pessoais e laboratório.
4. Construir Linux/amd64 a partir do commit exato da main em árvore/contexto limpo
   obtido de git archive. Usar tag local de validação distinta. Incluir versão,
   source e revision OCI. Nenhum .env/estado privado entra no build.
5. Inspecionar VERSION interno, arquitetura, SDK/Go e rótulos de origem. Comparar
   runtime com candidato: somente metadados/versionamento devem diferir. Validar
   imagem final no mesmo lab: licença, pareamentos salvos, texto/imagem/áudio nas
   duas vias e ciclos de reconexão API/TCP com sync/provas. Preservar PostgreSQL,
   licença e ratchets; trocar somente API local, webhook exclusivamente local.
   Não repetir2h sem mudanças de lógica: a duração aprovada cobre o mesmo código;
   registrar essa limitação e os testes específicos na imagem exata final.
6. Manter o changelog não publicado durante preparação. Após publicar a release,
   atualizar somente docs/changelog em commit posterior, sem mover a tag ou
   reconstruir a imagem publicada. Tag Git/release e imagem apontam ao mesmo
   commit de main usado no build. Registrar o digest nas notas e no runbook.
7. Publicar somente tuanmedeiros/evolution-go:0.7.2-0.1.1, sem latest; capturar digest
   do registry. Confirmar pull por digest e comparar identidade/binário/labels com
   artefato validado. Não confundir image ID local com digest do manifesto.
8. Criar tag Git com versão exata e GitHub release no fork para o mesmo commit,
   com notas em inglês, resultados, digest e rollback. Sem tags no upstream.
9. Registrar evidências finais, links e runbook de rollback, com versão/digest
   antigos e novos, pré-requisitos e proposta evoapi3/24h→evoapi1. Não executar
   comandos de implantação ou rollback. Parar após passo4 do fluxo do usuário.

## Checkpoint

PR #2 integrado em 2026-11-12T07:06:02Z. Main local acompanha academia/main no
commit11bb6e4514e0a40b9b0445941e1164acef29f830, VERSION0.7.2-0.1.1.
Imagem final construída do git archive desse commit:
sha256:4e8d5a8d290166443669c6ec71514140f093f25cdb6105344473b8a288685940.
Tag localdechecagem:tuanmedeiros/evolution-go:0.7.2-0.1.1-check-11bb6e4.
Metadados OCI e binário confirmados: Go1.26.5, SDKc883, Linux/amd64, CGO1,
VERSIONembutido0.7.2-0.1.1. SHA256binário76d5c51d032266c3697837ff52a615f9e0ebb95f8bad0ab6e91b661ec08f6c36.

Validação exata em andamento, sessão96520: mídia01255b29passou6/6; API55495343
passou10ciclos/10Completed/30entrada/10saída. TCP5512b7fa em andamento.
Troca somente da API local; licença ativa e dois pareamentos salvos autenticados.
Estado detalhado e progresso durável em build/release-0.7.2-0.1.1/metadata.json e
progress.md. Ainda não publicar atéTCPpassar. Nenhuma tag Git/release nova criada.
Não alterar produção; próxima etapa autorizada após teste: publicar imagem exata,
confirmar pull/digest, tag/release no mesmo commit, runbook e parada.
Atualizar este documento após cada etapa e antes de qualquer interrupção.

### Preparação da versão

- PR #2 mergeable/CLEAN, head0be0970 antes do bump. PermissãoWRITE e merge commits
  permitidos. Tag Git0.7.2-0.1.1 ausente; GitHub releases do fork ausentes.
- Próxima versão compatível0.7.2-0.1.1 conforme política do fork. VERSION e
  changelog atualizados no PR; entrada ainda Unreleased. Nenhum código runtime alterado.
- Novo pedido do Tuan substitui a parada anterior: merge, release e publicação
  autorizados; deploy continua proibido. Preservar tags antigas e não tocar latest.

- TestForkVersionAndChangelog passou, exit0. Diff runtimeGo/Python/dependências/
  Dockerfile contra46fa181 é vazio; apenas VERSION/changelog e documentação novos.
  R11limpa continua cobrindo o código; bump de metadados não requer nova revisão
  de implementação. Próximo: enviar bump, merge com head esperado, build da main.

## Bloqueio de publicação — parar antes de contornar

Imagem final validada: mídia6/6; API55495343 e TCP5512b7fa passaram10ciclos cada,
20Completed,60entrada e20saída, sem panics/stream errors. AuthDB continua2ociosas.
Tentativa de docker push para a tag nova falhou antes de subir camadas; não há
digest publicado registrado e nenhuma Git tag/release criada. Categorias sanitizadas:
{'registry_access_denied': False, 'credential_helper_error': False, 'credential_helper_missing': False, 'network_or_tls_error': True}

Merge #2 e build/validação completos. Estado preciso em
build/release-0.7.2-0.1.1/metadata.json (publish_failed), progress.md e push.log
privado (não imprimir seu conteúdo bruto). Diagnóstico exato: Client.Timeout exceeded / request canceled, sem erro de
credencial ou certificado. Uma repetição idêntica da operação já autorizada será
feita para distinguir falha transitória; sem mudar imagem, tag, endpoint, TLS ou
credenciais. Se persistir, parar e consultar Tuan sobre o acesso. Não fazer deploy.

### Bloqueio confirmado após repetição idêntica

- Segunda tentativa de docker push falhou com Client.Timeout exceeded/request
  canceled ao acessar registry-1.docker.io. Sem mensagem de credencial negada,
  sem camadas publicadas, sem digest. Metadados: publish_blocked, attempts2.
- Buildx imagetools (cliente no host) consegue consultar a tag ausente; o push
  pelo daemon local OrbStack sofre timeout. Isso sugere diferença de caminho
  de rede host/daemon; não prova causa de proxy/DNS. Nenhuma configuração alterada.
- Parar antes de contornar. Pode-se propor uploader no host para o mesmo artefato
  exportado, verificando image ID/digest; sem rebuild, reinício do Docker, TLS
  desabilitado ou credenciais lidas. Aguardar decisão do Tuan.
- Merge e validação completos. Tag Git/GitHub release/publicação ainda pendentes.
  Produção continua imagem antiga,1réplica,stop-first,parallelism1, sem alterações.

- Não há crane/skopeo/regctl/oras instalados. Pergunta enviada ao Tuan para
  autorizar download temporário de cliente no host ou aguardar correção de rede.
  Não baixar/usar uploader alternativo antes da resposta. Exportação somente
  leitura da imagem validada preparada em validated-image.tar; config/versão/
  source confirmados contra4e8d5a8..., arquivo local protegido.

### Diagnóstico solicitado pelo Tuan: timeout versus autenticação

- Ambas as falhas ocorreram aguardando headers no GETregistry-1.docker.io/v2/,
  antes de qualquer atividade de camadas. Marcadores: Client.Timeout exceeded,
  awaiting headers; sem unauthorized/denied/authentication required.
- Provas somente leitura no host: registry/v2 respondeuHTTP401 em0,417s ao acesso
  anônimo (desafio de autenticação esperado); endpoint de token pull anônimo
  respondeuHTTP200 em0,205s. Corpo do token descartado em/dev/null, não lido/impresso.
- Daemon29.8.2/OrbStack responde localmente. Flags de proxyHTTP/HTTPS presentes;
  URLs/credenciais de proxy não foram lidas/mostradas. Diferença de caminho de
  rede/proxy host→registry versus daemon→registry é hipótese, não causa provada.
- Não há evidência de login inválido; não pedir reautenticação como primeiro passo.
  Não houve logout/login, ajuste de proxy/TLS/rede, restart ou tentativa de contorno.
  Decisão anterior sobre uploader temporário continua pendente.

### Continuação solicitada pelo Tuan após o diagnóstico

Tuan confirmou que deseja publicar no repositório existente do Docker Hub.
Prosseguir pelo cliente temporário no host, como explicado em resposta, mantendo
imagem exata e sem restart/configuração de Docker, sem deploy. Fonte oficial do
uploader: google/go-containerregistry, releasev0.22.1; documentação crane push
aceita Docker tarball. Downloads terão SHA256 verificado antes da execução.

### Publicação concluída

**Passos1–4 concluídos: merge, versão/tag/release, imagem publicada e rollback prontos.**
Sem deploy autorizado ou executado. Restam somente os registros finais no repositório.

- PR #2 integrado; origem imutável da imagem/tag: `11bb6e4514e0a40b9b0445941e1164acef29f830`.
- Versão0.7.2-0.1.1; tag Docker `tuanmedeiros/evolution-go:0.7.2-0.1.1`.
- Digest publicado e confirmado pelo Docker Hub: `sha256:57b22a4245695c10772915d3ceeef60a6eec06275bdf63ceec539deaf27a815c`.
- Image ID/config: `sha256:4e8d5a8d290166443669c6ec71514140f093f25cdb6105344473b8a288685940`; binárioSHA256 `76d5c51d032266c3697837ff52a615f9e0ebb95f8bad0ab6e91b661ec08f6c36`.
- GitHub release: https://github.com/performance-academia-lendaria/evolution-go/releases/tag/0.7.2-0.1.1 (pré-release conforme formatoSemVer do fork).
  Tag Git aponta ao commit da imagem; assets manifest/runbook/checksums conferidos.
- Imagem final testada: mídia6/6; API10+TCP10, Completed20/20, entrada60/60,
  saída20/20;0panics/stream errors; authDB2idle. Relatórios01255b29/55495343/5512b7fa.
- Duas tentativas do daemon deram timeout sem subir camadas; cliente temporário
  cranev0.22.1 no host publicou usando credenciais existentes, sem novo login.
  Pull imutável/config/labels/plataforma e Dockerload confirmaram artefato idêntico.
  Não houve rebuild, alteração de rede/proxy/TLS ou restartDocker.
- Runbook completo em `docs/releases/0.7.2-0.1.1.md` e assetrollback.md na release.
  Rollback: `tuanmedeiros/evolution-go:0.7.2-0.1.0@sha256:5c41352292072d0f533596389cc9445fc6d3ce1ce551aeb29dfe8b8e923a3c68`, manifesto disponível. Preservar ratchets atuais.
- Progresso detalhado local: build/release-0.7.2-0.1.1/metadata.json e progress.md.
  Publicação, tag e pull já terminaram; não aguardar sessões anteriores.
- Próximo: registrar changelog publicado, plano/resultados/runbook via PR de docs
  apenas no fork; limpar uploader temporário e parar. Não alterar/mover tag ou
  reconstruir versão publicada. Não fazer deploy. Proposta futura: evoapi3/24h,
  depois evoapi1 em janela combinada, cada um com autorização explícita.
