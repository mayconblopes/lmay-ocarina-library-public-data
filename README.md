# L.May Ocarina Library — dados públicos

Este repositório distribui arquivos JSON públicos para a Library e seus aplicativos. Os clientes os consultam por HTTP GET; a publicação e a edição são feitas por commits no GitHub.

## Arquivos

- [notifications.json](./notifications.json): avisos e comunicados exibidos pelos clientes.
- [schema/notifications.schema.json](./schema/notifications.schema.json): contrato do arquivo de notificações (JSON Schema Draft 2020-12).

## Notificações

Cada item em `notifications` tem um `id` estável, um `type` (`info`, `warning` ou `maintenance`), `startsAt` e `expiresAt` em ISO 8601 UTC, além de `title` e `message` com textos para `pt-BR` e `en`. O campo opcional `url` deve usar HTTPS. Os clientes devem ignorar avisos fora do intervalo de publicação e escolher o idioma disponível com fallback para `pt-BR`.

A lista começa vazia. Para publicar um aviso, edite o JSON, valide contra o schema e faça commit. Para removê-lo, remova o item ou ajuste sua expiração. Cada aplicativo pode controlar localmente quais avisos cada pessoa já leu; este repositório não armazena dados dos usuários.

## Acesso e privacidade

Todo conteúdo deste repositório e qualquer arquivo publicado pelo GitHub Pages é público. Não inclua tokens, credenciais, dados pessoais, conteúdo privado ou regras de segurança. Configurações distribuídas ao cliente servem apenas para controlar a interface, nunca para autorizar acesso a recursos.

## Expansão

Outros dados públicos podem ser adicionados em arquivos próprios, com schema e documentação. Mantenha os contratos existentes compatíveis; mudanças incompatíveis devem receber uma nova versão de schema e ser coordenadas com os clientes.
