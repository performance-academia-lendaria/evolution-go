# Release 0.7.2-0.1.1 — plano e checkpoint

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

Planejamento registrado; ainda sem bump, merge, build final ou publicação.
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
