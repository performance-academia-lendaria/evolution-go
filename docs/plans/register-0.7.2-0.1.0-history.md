# Registro histórico da release 0.7.2-0.1.0

## Pedido e condição

Tuan pediu registrar a release anterior do fork em ordem cronológica; se isso não
for possível, prefere manter a página como está. Registrar somente metadados Git/
GitHub. Não reconstruir/publicar imagens, mover tags existentes ou fazer deploy.
Origem permanece protegida: push apenas academia. Arquivos pessoais e alterações
locais sobre banco compartilhado devem ser preservados.

## Evidência antes de qualquer escrita remota

- Docker Hub0.7.2-0.1.0: digest5c41352292072d0f533596389cc9445fc6d3ce1ce551aeb29dfe8b8e923a3c68,
  tag_last_pushed2026-11-03T19:16:36.991969Z, active.
- Fonte já documentada da imagem:3994d1027d957d19bb92b105069061b4123300cc,
  VERSION0.7.2-0.1.0, commit2026-11-03T19:12:29Z.
- Git tag0.7.2-0.1.0 e GitHub release correspondentes ausentes.
- Release0.7.2-0.1.1:ID442750116, created_at2026-11-12T09:46:39Z,
  published_at2026-11-12T09:49:10Z, prerelease=true. Tag anotada aponta11bb6e4.
  Não modificar essa release/tag/imagem.

## Plano

1. Salvar snapshot dos metadados da0.1.1 para comparação posterior.
2. Criar referência leve0.7.2-0.1.0 para o commit original3994d10, sem inventar
   data de criação de tag anotada. A data do commit original fica intacta.
3. Preparar release histórica em draft, prerelease=true/make_latest=false,
   com data real de publicação original da imagem e indicação explícita de que
   o registro GitHub é retrospectivo, criado hoje. Não retrodatá-lo artificialmente.
4. Conferir created_at e ordenação na API antes de publicar; confirmar que fica
   abaixo da0.1.1. Se não atender à condição, não publicar e desfazer somente os
   metadados novos deste trabalho, sem tocar0.1.1.
5. Publicar apenas se ordem correta; conferir a página pública e os metadados/
   tags/imagens0.1.1 e0.1.0. Não mover releases existentes para conseguir a ordem.
6. Registrar resultado/links. Atualização de changelog sobre o registro histórico
   pode ser preparada localmente, preservando a informação de origem da imagem.

Fontes primárias consultadas: documentação GitHub de releases e sua API; suporte
GitHub informa ordenação pela data da tag/commit. A ordenação será confirmada na
API/página real, sem confiar apenas nesse comportamento documentado.

## Checkpoint

CONCLUÍDO. Release histórica publicada:
https://github.com/performance-academia-lendaria/evolution-go/releases/tag/0.7.2-0.1.0

- Referência leve aponta ao commit original3994d10, sem alterar data do commit
  ou inventar uma data de criação de tag anotada.
- GitHub calculou created_at2026-11-03T19:12:29Z pela referência histórica;
  published_at2026-11-12T12:57:31Z registra corretamente a publicação atual.
- Primeiro fetch da página padrão ainda tinha cache; a página pública atualizada
  e a API confirmaram ordem0.7.2-0.1.1 acima de0.7.2-0.1.0.
- Snapshot da release0.1.1 (campos, hash do corpo e assets) permaneceu idêntico.
  Nenhuma imagem reconstruída, retaggeada ou publicada, sem deploy/acesso EC2.
- Prova e snapshot público em build/release-history-0.7.2-0.1.0/ (ignorado).
- Atualizar apenas changelog/política com o registro histórico. A data de03/11
  refere-se à imagem original; não declarar que a GitHub release existia nessa data.
