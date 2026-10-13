# L.May Ocarina Library — dados públicos

Este repositório distribui arquivos JSON públicos para a Library e seus aplicativos. Os clientes os consultam por HTTP GET; a publicação e a edição são feitas por commits no GitHub.

## Arquivos

- [notifications.json](./notifications.json): avisos e comunicados exibidos pelos clientes.
- [schema/notifications.schema.json](./schema/notifications.schema.json): contrato do arquivo de notificações (JSON Schema Draft 2020-12).
- [schema/validate_notifications.py](./schema/validate_notifications.py): verificação local sem dependências externas.

## Notificações

Cada item em `notifications` tem um `id` estável, um `type` (`info`, `warning` ou `maintenance`), além de `title` e `message`. `info` e `maintenance` aparecem na caixa de entrada/arquivo. `warning` aparece na aba Avisos, sem estado de leitura ou opção de arquivar, e exige `startsAt` e `expiresAt`. As datas usam ISO 8601 UTC; o aviso fica ativo a partir de `startsAt` e deixa de aparecer em `expiresAt`. Em qualquer tipo, quando as duas datas existem, `expiresAt` deve ser posterior a `startsAt`.

`title` e `message` são objetos localizados. `pt-BR` é obrigatório e `en` é opcional; quando a tradução em inglês não existir, os clientes usam o texto em `pt-BR`. Os valores de `message` aceitam Markdown, para que os clientes possam exibir links e formatação compatíveis.

O campo opcional `action` define um CTA localizado com `label` e `url`. Cada objeto exige `pt-BR` e aceita `en` como tradução opcional com fallback para `pt-BR`; todas as URLs do CTA devem usar HTTPS. Quando `action` existir, os clientes devem priorizá-lo para renderizar um botão. O campo legado `url` continua sendo uma URL HTTPS simples e serve como fallback quando não houver uma ação localizada.

Mantenha o array `notifications` ordenado do aviso mais novo para o mais antigo, para que os consumidores possam preservar a ordem do feed. O contrato não adiciona um campo `createdAt`; a posição no array representa essa ordem editorial.

Para validar o feed e o contrato localmente, execute `python schema/validate_notifications.py` usando Python 3. A verificação não instala dependências e também confere IDs duplicados, datas, URLs HTTPS, fallback de idioma e os campos exigidos pelo contrato.

A lista começa vazia. No L.May Ocarina Studio, use **Configurações da Library → Mensagens** para criar, consultar, editar e remover avisos. Salve as alterações localmente e use **Deploy das mensagens** para enviar somente `notifications.json` ao GitHub. A edição manual continua disponível: valide o feed antes de fazer commit. Cada aplicativo pode controlar localmente quais avisos cada pessoa já leu; este repositório não armazena dados dos usuários.

## Acesso e privacidade

Todo conteúdo deste repositório e qualquer arquivo publicado pelo GitHub Pages é público. Não inclua tokens, credenciais, dados pessoais, conteúdo privado ou regras de segurança. Configurações distribuídas ao cliente servem apenas para controlar a interface, nunca para autorizar acesso a recursos.

## Expansão

Outros dados públicos podem ser adicionados em arquivos próprios, com schema e documentação. Mantenha os contratos existentes compatíveis; mudanças incompatíveis devem receber uma nova versão de schema e ser coordenadas com os clientes.
