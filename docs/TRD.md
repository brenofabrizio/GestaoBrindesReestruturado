# TRD — Gestão de Brindes Reestruturado

**Versão:** 1.1
**Data:** 02/10/2026
**Estado:** aplicação executada em modo local no navegador; paridade funcional ainda incompleta.

## 1. Fonte da verdade e situação real

O sistema legado `GestaoBrinde` é a referência de requisitos e comportamentos. O modo atualmente conectado à interface é React + TypeScript + Vite, publicado como frontend estático e usando `frontend/src/data/seed.json` para carga inicial e `localStorage` para persistência daquele navegador.

O repositório também contém um backend Django/DRF e modelos/serviços parciais. O frontend local atual não consome essa API; por isso, endpoints e regras existentes no backend não são considerados funcionalidades disponíveis no site. A matriz completa de lacunas está em [PARIDADE-FUNCIONAL.md](./PARIDADE-FUNCIONAL.md).

Não é necessário instalar Docker ou Python para compilar/publicar o frontend atual. Isso não significa que a aplicação atual forneça armazenamento central ou autenticação segura.

## 2. Arquitetura ativa

```text
 navegador de cada pessoa
       |
       +--> frontend React/TypeScript/Vite publicado na Vercel
                |
                +--> seed.json (modelo de dados inicial)
                +--> adaptador frontend/src/lib/api.ts
                         |
                         +--> localStore.ts --> localStorage daquele navegador
```

O nome `api.ts` é uma interface de compatibilidade; neste modo não faz chamadas de rede. A camada de armazenamento guarda JSON local e atende a interface. Os dados não são compartilhados entre usuários, dispositivos ou navegadores, não têm backup automático e podem ser removidos pelo usuário ou pelo navegador.

## 3. Componentes do frontend

| Componente | Responsabilidade atual |
|---|---|
| `src/App.tsx` | Rotas ativas: dashboard, catálogo, estoque, solicitações, auditoria e gestão do sistema |
| `src/context/AuthContext.tsx` | Sessão local e usuário autenticado |
| `src/lib/api.ts` | Adaptador comum consumido pelas páginas; aponta para o modo local |
| `src/lib/localStore.ts` | Leitura/gravação de JSON no navegador, dados de demonstração e regras locais |
| `src/lib/access.ts` | Consulta às permissões armazenadas localmente para controlar menus/ações na interface |
| `src/data/seed.json` | Contas, produtos, saldos, movimentos, solicitações e referências de demonstração |
| `src/pages/ManagementPage.tsx` | Gestão inicial local de usuários, cadastros auxiliares e permissões |

Rotas existentes não cobrem a lista completa de páginas do legado. A lista de módulos a implementar está em `PARIDADE-FUNCIONAL.md` e deve orientar novas rotas/componentes.

## 4. Persistência local e modelo atual

Chave principal do banco local: `gestao_brindes_json_database_v1`. Sessão: `gestao_brindes_local_user`. O banco em memória é inicializado a partir de `seed.json` quando não existe conteúdo salvo.

Coleções atuais:

- `users` e `rolePermissions`;
- `categories`, `departments`, `industries`, `locations`, `suppliers`;
- `products`, `balances`, `movements`;
- `requests` e `audit`.

Os cadastros adicionados usam IDs locais; produto e saldo continuam modelos simplificados. Faltam, entre outros, posições por local, regras/histórico de aprovação, operações de compra TRADE, entradas contra NF, fila física do CD, deliveries/protocolos, assinatura, eventos, notificações e configurações.

Uma mudança do formato de `seed.json` só atualiza usuários com armazenamento vazio. Navegadores já utilizados podem manter uma versão anterior do JSON; mudanças de esquema devem incluir migração local versionada e preservar os dados existentes. O carregamento deve tratar JSON inválido sem sobrescrever silenciosamente dados recuperáveis.

## 5. Autenticação, permissões e segurança

O login atual compara e-mail/senha mantidos no JSON local. A cópia local de credenciais não tem hash ou proteção de servidor; qualquer código e dado embarcado no frontend é inspecionável pelo usuário. Permissões locais melhoram a consistência dos fluxos de demonstração, mas não resistem à alteração do navegador ou chamada direta do código.

Portanto:

- não usar as contas locais como credenciais corporativas ou de produção;
- não colocar segredos pessoais/reais em `seed.json`;
- o modo local deve ser tratado como protótipo/demonstração individual;
- para operação multiusuário, reimplementar autenticação e autorização no servidor e mover o armazenamento para uma fonte persistente central;
- validar escopo por usuário, departamento e indústria no servidor quando essa arquitetura for adotada.

## 6. Regras de negócio a preservar

As regras devem ser extraídas do legado e mantidas no adaptador de domínio, não espalhadas por componentes React. Escopo mínimo:

- transições válidas de solicitações e motivo obrigatório para rejeição;
- quantidade solicitada, reservada, atendida e restante por item;
- saldo disponível igual ao físico menos reservas;
- bloqueio de baixa além do saldo/reserva;
- solicitação e cancelamento próprios distintos de ações administrativas;
- registro de saída pelo gestor separado de confirmação pelo CD;
- transferência reduz a origem e aumenta o destino sem alterar o total;
- rastreabilidade por ator, data, entidade, referência e movimento correspondente;
- regras diferentes por perfil, departamento e indústria.

No modo local, essas regras são úteis para validar a experiência, mas não substituem transações e controles de concorrência de servidor.

## 7. Diferenças entre os modos

| Capacidade | LocalStorage atual | Necessária para paridade compartilhada |
|---|---|---|
| Sem banco/Docker/Python local | Sim | Continua possível no computador do usuário |
| Alteração persiste ao recarregar o mesmo navegador | Sim | Sim |
| Vários usuários veem os mesmos dados | Não | Serviço central e persistente |
| Credenciais protegidas contra inspeção do browser | Não | Autenticação no servidor e segredos fora do bundle |
| Operações simultâneas confiáveis | Não | Transações/controle de concorrência |
| Envio de e-mail, Lecom e processamento agendado | Não | Integração/backend ou serviço externo |
| Backup central e restauração administrativa | Não | Serviço e política de backup |

## 8. Plano técnico de paridade

### P0 — Fundação local

- Acoplar gestão de usuários, referências e permissões ao adaptador JSON.
- Aplicar permissões às operações locais e corrigir recortes de solicitações.
- Versionar migrações do JSON local e impedir perda silenciosa de dados.

### P1 — Catálogo e estoque

- Completar entidades de produto, imagem/histórico e posição por local.
- Introduzir tipos de movimento, NF/referência e fluxos distintos de registro/confirmação.
- Implementar estorno e transferência com integridade de saldos.

### P2 — Solicitações internas

- Adicionar estado/histórico formal, aprovações e regras configuráveis.
- Criar filas de separação/entrega e comprovantes.
- Aplicar escopos de acesso por perfil/departamento/indústria.

### P3 — TRADE e eventos

- Modelar compra, recebimento, QR, assinatura, protocolo e evento.
- Definir quais passos são demonstráveis em modo local e quais exigem integração externa.

### P4 — Relatórios e administração

- Relatórios/exportação, importação simulada/validada, auditoria completa, notificações, configurações e cópia/restauração.

### P5 — Persistência compartilhada (fase futura)

- Substituir o adaptador local por serviço central sem alterar os contratos usados pelas páginas.
- Implementar identidade, autorização, transações, backups e integrações em servidor.
- Importar e reconciliar dados somente após ensaio em cópia do legado.

## 9. Critérios técnicos de pronto

- Rota e controles correspondentes existem e são acessíveis pelos perfis autorizados.
- Regras inválidas são rejeitadas no adaptador de domínio; a interface não é a única proteção.
- Escrita gera auditoria quando aplicável e não deixa saldos incoerentes.
- Migração local de esquema preserva dados anteriores.
- Documentação diferencia explicitamente código presente, frontend conectado e serviço externo disponível.
- Para marcar paridade, validar fluxo equivalente no legado e no reestruturado com cenários por perfil.
