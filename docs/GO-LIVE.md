# Checklist de homologação e go-live

Este checklist separa o que pode ser validado no código do que depende do negócio e das contas/provedores. **Não execute a carga oficial nem aponte previews para o banco de produção.**

## Sprint 0 — decisões e insumos

- [ ] Negócio confirma os cinco perfis, nomes de departamentos e escopo de aprovação.
- [ ] Responsáveis nomeados para homologação e aceite operacional.
- [ ] Projeto Vercel da API e projeto Vercel do frontend identificados.
- [ ] PostgreSQL persistente criado para preview e outro para produção.
- [ ] Exportação oficial do legado recebida e armazenada fora do Git quando contiver dados pessoais.

## Sprint 1 — acesso

- [ ] Criar usuários de homologação para administrador, aprovador, operador, solicitante e indústria.
- [ ] Confirmar que aprovadores só veem solicitações do próprio departamento.
- [ ] Confirmar que solicitantes veem apenas as próprias solicitações.
- [ ] Confirmar as exceções globais de leitura com o negócio; por padrão, operador e administrador têm o escopo definido em `apps/accounts/access.py`.
- [ ] Validar login, expiração/renovação do JWT e encerramento de sessão no navegador.

## Sprint 2 — catálogo e estoque

- [ ] Criar/editar/desativar produtos em preview e confirmar que desativação preserva referências históricas.
- [ ] Reconciliar produtos e saldo físico/reservado com a origem.
- [ ] Fazer teste operacional de entrada, ajuste, saída bloqueada por saldo insuficiente e reserva concorrente.
- [ ] Aprovar nomes, unidades e limites de estoque mínimo.

## Sprint 3 — solicitações

- [ ] Executar uma solicitação com vários produtos, aprovação e reserva.
- [ ] Rejeitar com motivo e conferir a trilha de auditoria.
- [ ] Atender parcialmente por item e depois concluir o restante.
- [ ] Cancelar antes e depois da reserva; confirmar liberação apenas da quantidade não atendida.
- [ ] Confirmar que usuário fora do departamento não acessa nem altera a solicitação.

## Sprint 4 — migração e auditoria

- [ ] Validar o mapeamento e a versão do pacote oficial do legado.
- [ ] Rodar primeiro a simulação: `python manage.py import_legacy caminho/para/pacote.json`.
- [ ] Revisar divergências e comparar contagens de usuários, categorias, produtos, saldo físico e reservado.
- [ ] Fazer snapshot/backup do banco destino antes de `--apply`.
- [ ] Aplicar somente após aprovação explícita: `python manage.py import_legacy caminho/para/pacote.json --apply`.
- [ ] Reconciliar novamente após a carga. Solicitações/movimentações históricas não fazem parte do importador mestre atual.

## Sprint 5 — configuração segura e publicação

Configure no ambiente da API (sem commitar segredos):

- `DJANGO_SECRET_KEY`: segredo aleatório, exclusivo por ambiente, com pelo menos 50 caracteres.
- `DJANGO_DEBUG=0`.
- `DATABASE_URL`: PostgreSQL persistente. Na Vercel este campo é obrigatório; SQLite é recusado em produção.
- `DJANGO_ALLOWED_HOSTS`: hosts concretos da API, separados por vírgula; não use `*` nem `.vercel.app` global.
- `CORS_ALLOWED_ORIGINS`: origens HTTPS exatas do frontend, sem curingas.
- `CSRF_TRUSTED_ORIGINS`: origens HTTPS exatas necessárias ao admin.
- `VITE_API_BASE_URL`: URL pública base da API, terminando em `/api/v1`, no projeto frontend.

Antes de publicar:

- [ ] Verificar que preview e produção usam bancos distintos.
- [ ] Executar `python manage.py check --deploy` no ambiente de configuração (alguns alertas dependem de proxy/domínio do provedor).
- [ ] Confirmar migrações aplicadas e criar conta administrativa por canal seguro.
- [ ] Smoke test: `GET /api/v1/health/`, login JWT, `/api/v1/auth/me/`, catálogo, estoque, solicitação e `/api/v1/audit/events/` com perfil autorizado.
- [ ] Testar rollback com backup/snapshot e documentar responsável de plantão.
- [ ] Obter aceite explícito dos usuários representantes dos perfis.

As alterações locais não publicam nenhum serviço. Nenhuma URL de produção, credencial Vercel/PostgreSQL, pacote legado oficial ou aprovação dos usuários foi disponibilizada nesta execução; esses itens continuam bloqueando go-live.
