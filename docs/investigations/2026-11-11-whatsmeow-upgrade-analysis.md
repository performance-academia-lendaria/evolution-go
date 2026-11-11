# Análise da atualização oficial da whatsmeow

Estado: análise e implementação da candidata em andamento. Os testes da referência
não reproduziram o congelamento; as correções abaixo são relevantes pelo caminho
de código e não demonstram, por si, a causa do incidente de produção.

## Versões e fonte primária

- Atual: `v0.0.0-20260630180629-b572e5bcb92b`.
- `@latest` consultado em 2026-11-11:
  `v0.0.0-20261110152934-c88388f983b4`.
- Commit: `c88388f983b4bc43dfd0bcc2b46969fcde82d61f`, 2026-11-10 15:29:34 UTC.
- Exatamente 117 commits no intervalo, conferidos por `git rev-list --count` no
  [repositório oficial](https://github.com/tulir/whatsmeow).
- A nova dependência declara `go 1.26.0`; o build da Evolution atual usa Go 1.25.0
  no Dockerfile. O builder precisará acompanhar o novo mínimo. O host tem Go 1.26.5.

## Mudanças relevantes no intervalo

| Área | Commit oficial | Mudança e relação com o problema |
|---|---|---|
| Filas por conexão | [4fa3462](https://github.com/tulir/whatsmeow/commit/4fa3462) | Cria fila por handshake/conexão e a passa ao frame handler e ao loop; evita reaproveitar a fila de uma conexão encerrada ao reconectar o mesmo Client. A Evolution também recria clientes, portanto a aplicação direta depende do caminho de reconexão interno utilizado. |
| Erro de stream/reconexão | [28bfe53](https://github.com/tulir/whatsmeow/commit/28bfe53) | Drena stream errors pendentes após cancelamento e aguarda fim do loop no Disconnect. Relevante porque a produção relata stream errors imediatamente antes de reconectar. |
| Contexto do transporte | [0fadda7](https://github.com/tulir/whatsmeow/commit/0fadda7), [f1b7985](https://github.com/tulir/whatsmeow/commit/f1b7985) | Corrige contexto de frames Noise e verifica cancelamento ao entregar frames completos; reduz trabalho da conexão encerrada atravessando o ciclo de vida. |
| Callback de socket | [d5f354c](https://github.com/tulir/whatsmeow/commit/d5f354c) | Callback onDisconnect passa a variável atômica, relevante para fechamento e reset concorrentes. |
| Keepalive | [3d913f0](https://github.com/tulir/whatsmeow/commit/3d913f0) | ResetConnection evita sobrescrever intenção concorrente de desconexão. É condicional a auto-reconnect por keepalive; a Evolution hoje desativa EnableAutoReconnect e tem recuperação própria. |
| Handshake interrompido | [d24d079](https://github.com/tulir/whatsmeow/commit/d24d079), [2fc844f](https://github.com/tulir/whatsmeow/commit/2fc844f) | Para de aguardar resposta quando o socket fecha e classifica timeout/fechamento como erro recuperável. Não substitui os controles de versão/handshake do fork. |
| Status | [a238105](https://github.com/tulir/whatsmeow/commit/a238105) | Adiciona handler de stanza status para mensagens não criptografadas. Stanza status e ack rejeitado com class=status/type=media são caminhos distintos; isso não prova que o erro observado foi corrigido. |
| Ack de retry receipt | [bbe00cd](https://github.com/tulir/whatsmeow/commit/bbe00cd), [6bb48c0](https://github.com/tulir/whatsmeow/commit/6bb48c0) | Ack de retry ocorre após tratamento; respeita SynchronousAck ao decidir processamento síncrono. |
| Ack de app state | [56e5ad0](https://github.com/tulir/whatsmeow/commit/56e5ad0) | Com SynchronousAck, processa server_sync antes do ack e cancela ack quando desconectado; sem a opção mantém caminho assíncrono. |
| Ack e erro de decifração | [cf05480](https://github.com/tulir/whatsmeow/commit/cf05480), [f47dfe9](https://github.com/tulir/whatsmeow/commit/f47dfe9) | Chama handlers antes de ack em mensagens indecifráveis e propaga falha de processamento de partes de protocolo. |
| Sessão unificada | [1fbae98](https://github.com/tulir/whatsmeow/commit/1fbae98) | UnifiedSessionInterval positivo envia sessão unificada após Connected com limite de frequência. SendPresence(Available) já envia sessão; Unavailable não o faz. Evolution usa Unavailable quando alwaysOnline=false. Avaliar essa opção separadamente do estado online do telefone. |
| App state e segredos WASA | [398ef18](https://github.com/tulir/whatsmeow/commit/398ef18), [9127869](https://github.com/tulir/whatsmeow/commit/9127869), [8b41cfe](https://github.com/tulir/whatsmeow/commit/8b41cfe) | Armazenamento/distribuição de chaves de app state e suporte ao estado de envio; envolve schema e compatibilidade de armazenamento a revisar. |
| App state e falhas | [3bc895e](https://github.com/tulir/whatsmeow/commit/3bc895e), [5403881](https://github.com/tulir/whatsmeow/commit/5403881) | Emite AppStateSyncError e respeita backoff do servidor em rate limit, em vez de repetir fetch sem aguardar. |
| App state e LTHash | [2987013](https://github.com/tulir/whatsmeow/commit/2987013) | Aceita divergência de LTHash somente com MAC do patch válido e continuidade do estado; não desliga validação indiscriminadamente. |
| Protocolo/binário | [5d4657a](https://github.com/tulir/whatsmeow/commit/5d4657a), [bb54a07](https://github.com/tulir/whatsmeow/commit/bb54a07) | Atualiza proto até v1052556849 e tolera erro de conversão de tag no decoder; os demais bumps de protocolo também vêm na atualização. |

## Opções e sequência de validação

1. Aplicar primeiro a dependência oficial e ajustar somente incompatibilidades,
   preservando os controles de versão/handshake do fork.
2. Manter SynchronousAck no valor atual enquanto não houver teste que justifique
   a mudança: ele altera a relação entre ack e handlers que fazem operações de I/O.
   Confirmar defaults e registrar a decisão final após a compilação.
3. Avaliar UnifiedSessionInterval: há uma diferença concreta entre Available e
   Unavailable no código da biblioteca. Conferir efeito no laboratório, sem mudar
   alwaysOnline nem retirar o comportamento de notificações do telefone.
4. Provar e corrigir separadamente o panic Archive da Evolution. Atualizar biblioteca
   não corrige a conversão de tipo que existe no handler da aplicação.
5. Examinar serialização, remoção de handler, encerramento do cliente e goroutine
   antiga em ReconnectClient. Alterações exigem teste vermelho/verde.
6. Repetir os dois métodos de reconexão, validar texto/mídia/áudio/imagem e manter
   pelo menos duas horas de tráfego periódico. Resultados posteriores devem indicar
   compatibilidade/estabilidade local; causa em produção continua não comprovada
   enquanto o congelamento anterior não tiver sido observado.

## Estado das decisões

- Atualização oficial: selecionada como candidata pelo pedido de prosseguir do Tuan.
- Patch próprio/fork da biblioteca: nenhum criado; depende de falha concreta ainda
  presente na versão oficial e teste que a demonstre.
- Decisão: manter SynchronousAck=false e UnifiedSessionInterval=0, defaults da SDK.
  As imagens intermediárias com a SDK nova completaram 20/20 reconexões e receberam
  60/60 mensagens; QR novo também autenticou. Nenhum teste demonstrou necessidade de
  ligar opção. SynchronousAck faria ack depender de handlers com I/O; sessão unificada
  adicionaria outro comportamento sem isolar causa. Não mudar alwaysOnline/presença.
  Isto não prova que os defaults cubram a falha específica de produção ainda sem
  reprodução; rever opções somente com um caso que as demonstre necessárias.
- Causa do congelamento de produção: aberta; não declarar resolvida pelo simples
  fato de a candidata passar nos mesmos testes que já passaram na referência.

Ver [diário](2026-11-11-whatsmeow-offline-sync.md) e
[plano](../plans/fix-whatsmeow-offline-sync.md) para estado e limites completos.

## Adaptações de API da Evolution

Além das quatro mudanças de assinatura encontradas pelo compilador, a revisão
identificou dois contratos de resposta que precisavam de adaptação:

- Blocklist passou de JIDs para Items com LID/PN; a API preserva DHash/JIDs por um
  adapter próprio. Teste JSON demonstrou a regressão antes da correção.
- IsOnWhatsApp agora pede addressing_mode=lid e fornece PhoneNumber separado.
  user/check usa PN conhecido nos campos JID/RemoteJID e retorna o LID fornecido,
  sem chamar lookup restrito aPN com um LID. Formato legado e not-found preservados.
  A regressão foi observada também pela API local com os números exclusivos; só
  booleanos de validação foram registrados, sem identificadores ou respostas brutas.

SynchronousAck/UnifiedSessionInterval não corrigem esses contratos da aplicação.
O send service pode usar o JID canônico LID para SDK SendMessage; isso será conferido
com formatação padrão no laboratório, sem alterar a comparação que usa formatJid=false.
