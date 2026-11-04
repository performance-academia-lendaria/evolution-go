# Versionamento do fork da Academia Lendária

Este repositório é um fork do Evolution Go. A Academia mantém seu código e suas versões em `performance-academia-lendaria/evolution-go`; ele não publica alterações no repositório ou na imagem do projeto original.

## Formato

```text
<VERSÃO-DO-EVOLUTION-GO>-<VERSÃO-DA-ACADEMIA>
        0.7.2                  0.1.0
```

Exemplo inicial: **`0.7.2-0.1.0`**. A primeira parte identifica a versão estável do Evolution Go usada como base; a segunda é a versão das alterações mantidas pela Academia. A base inicial é a tag oficial `0.7.2`, commit `9337afc47e10b86cc896a6f432240e40fee95dd1`. Publicar uma imagem não cria uma release Git nem autoriza, por si só, implantação em produção.

Este formato é um SemVer válido, mas tem uma consequência: para ferramentas SemVer, `0.1.0` é o identificador de **pré-lançamento de `0.7.2`**, e não uma segunda versão SemVer independente. Assim, `0.7.2-0.1.0` tem precedência menor que `0.7.2`; ferramentas e restrições de dependência podem ignorar pré-lançamentos. Informe a versão completa explicitamente ao selecionar a release ou imagem. A Academia usa os três números após o hífen como convenção própria de evolução do fork.

## Como incrementar a versão da Academia

| Alteração do fork | Exemplo | Critério |
|---|---|---|
| Correção compatível | `0.7.2-0.1.0` → `0.7.2-0.1.1` | Corrige comportamento sem mudar o contrato público. |
| Funcionalidade compatível | `0.7.2-0.1.1` → `0.7.2-0.2.0` | Adiciona capacidade mantendo o contrato público. |
| Mudança incompatível | `0.7.2-0.2.0` → `0.7.2-1.0.0` | Exige adaptação de consumidores da API ou de configurações. |

Ao incrementar o número principal, zere os dois seguintes; ao incrementar o intermediário, zere o último. Enquanto a versão própria estiver em `0.x.y`, ela representa desenvolvimento inicial e não promete a estabilidade de uma API `1.0.0`. A regra de mudanças incompatíveis acima é a convenção adotada por este fork; o padrão SemVer não oferece as mesmas garantias para `0.x.y`.

Quando atualizar o Evolution Go de base, altere a primeira parte para a nova versão oficial efetivamente incorporada e registre no changelog a tag e o commit usados. A versão da Academia continua sua própria sequência e deve ser incrementada conforme o impacto da atualização; não a reinicie automaticamente. Por exemplo, após `0.7.2-0.1.1`, uma atualização compatível da base com nova funcionalidade poderia resultar em `0.7.3-0.2.0`. Avalie cada atualização; mudar a base pode introduzir incompatibilidades.

Use apenas números inteiros sem zeros à esquerda. O formato acima se aplica a bases oficiais estáveis `X.Y.Z`; caso seja necessário adotar uma base oficial com sufixo de pré-lançamento, defina e revise a convenção antes de criar a versão.

## Onde alterar e como identificar uma build

1. Atualize `VERSION` com a versão completa, sem prefixo `v` nem espaços. Esse arquivo é a fonte de verdade das builds do fork.
2. Adicione uma entrada correspondente no início de `CHANGELOG.md`, com as mudanças, compatibilidade e a versão/commit da base quando esta mudar. Mantenha-a identificada como não publicada até a release ser efetivamente criada.
3. Valide o código e a imagem em ambiente isolado. `make build` e `make docker-build` usam `VERSION`; um `docker build` sem `--build-arg VERSION` também usa o arquivo. Uma substituição explícita de `VERSION` serve para builds de teste e deve ser identificada como tal.
4. Ao preparar uma release aprovada, use a versão completa do arquivo para a tag Git e para a tag da imagem no registry **da Academia**. Registre também o commit e o digest da imagem. Não crie tags ou publique versões no projeto ou registry oficiais.
5. Uma vez publicada, não substitua o conteúdo da mesma versão; para outra alteração, gere uma nova versão. Em produção, prefira a versão exata e o digest aprovado em vez de depender de `latest`.

O destino escolhido para as imagens do fork é o Docker Hub `tuanmedeiros/evolution-go`. A automação herdada que publicava em `evoapicloud/evolution-go` é removida nesta branch; uma futura automação deve ser revisada e apontar somente para o destino escolhido antes de ser ativada. Alterar `VERSION` ou fazer build local não publica uma imagem nem cria uma release.

## Fluxo de código e imagem

1. Crie uma branch a partir da `main` atualizada do repositório da Academia. Implemente a alteração, atualize `VERSION` e o changelog, rode os testes pertinentes e abra um PR para a `main` da Academia.
2. Revise o PR e valide a mudança em ambiente isolado. Imagens de teste geradas antes do merge devem usar uma identificação de teste distinta da tag definitiva. Registre suas limitações.
3. Após a revisão e as aprovações necessárias, integre o PR à `main`. Faça checkout da `main`, confira que acompanha o remoto da Academia e atualize-a. Confirme o commit e a versão antes do build.
4. Construa a imagem de release a partir desse commit da `main`, em árvore limpa, incluindo a versão e o commit de origem como metadados. Valide a imagem exata que será publicada; se usar staging, teste o mesmo digest. Não use uma tag já publicada para outra imagem.
5. Publique somente no Docker Hub `tuanmedeiros/evolution-go`, usando a versão completa de `VERSION`. Registre a tag, o digest retornado pelo registry, o commit de origem e os resultados dos testes; confirme o pull pelo digest. Uma tag Git ou release, quando criada, deve apontar para o commit que originou a imagem.
6. Após aprovação do deploy, implante o digest validado, verifique o serviço e mantenha registrado o digest anterior e o procedimento de retorno. Atualize a fonte operacional de implantação para evitar que um redeploy posterior restaure uma imagem antiga. A publicação da imagem não implica deploy automático.
7. Após confirmar o merge, atualize a `main` local e remova as branches de trabalho quando não forem mais necessárias. Preserve arquivos locais que não façam parte do PR.

### Registro da primeira imagem

A imagem `0.7.2-0.1.0` foi publicada antes do merge do PR, a partir do commit `3994d1027d957d19bb92b105069061b4123300cc`. Seu digest é `sha256:5c41352292072d0f533596389cc9445fc6d3ce1ce551aeb29dfe8b8e923a3c68`. A versão já está em produção; não reconstrua nem substitua essa tag para alinhar o histórico. A integração posterior do PR preserva o commit de origem e documenta essa exceção ao fluxo acima. Alterações futuras devem receber uma nova versão.

Referências: [Semantic Versioning 2.0.0](https://semver.org/lang/pt-BR/) e [referência de tags de imagem Docker](https://docs.docker.com/reference/cli/docker/image/tag/).
