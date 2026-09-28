# TRD — Gestão de Brindes

**Versão:** 1.0  
**Data:** 28/09/2026  
**Escopo:** estado técnico atual, decisões, entregas e plano de conclusão

## 1. Resumo técnico

O sistema é um monólito modular Django com API REST versionada, autenticação JWT, PostgreSQL como banco oficial e React/TypeScript/Vite como frontend. O deploy planejado separa o frontend em um projeto Vercel com Root Directory `frontend` e mantém a API Django em um projeto/runtime compatível, usando o mesmo domínio ou roteamento configurado.

O sistema não depende de Docker ou Python instalado na máquina do usuário para o deploy. O runtime Python é provisionado pelo ambiente de hospedagem. Docker e Python continuam úteis apenas para desenvolvimento local, testes e operação controlada.

## 2. Estado atual da implementação

| Área | Implementado | Pendente |
|---|---|---|
| Backend Django | Apps `core`, `accounts`, `catalog`, `inventory`, `orders`, `audit`; URLs, serializers, migrations e serviços | Executar testes com Python disponível e homologar em ambiente publicado |
| Autenticação | Usuário por e-mail, JWT, endpoint `/auth/me/`, refresh | Recuperação de senha, política de sessão e mensagens finais |
| Autorização | Matriz estática em `apps/accounts/access.py`, permission class e filtros de queryset | Validar matriz com negócio; avaliar RBAC configurável |
| Catálogo | Categorias, produtos, SKU, unidade, estoque mínimo, API e tela inicial | Formulários completos, filtros, paginação e desativação pela UI |
| Estoque | Saldo físico/reservado, movimentações transacionais, reserva e baixa | Histórico visual completo, filtros, transferência e testes concorrentes |
| Solicitações | Estados, envio, aprovação, rejeição, cancelamento, reserva e atendimento parcial | Jornada visual completa e testes ponta a ponta |
| Auditoria | Evento imutável com ator, ação, entidade e metadados | Consulta filtrada/paginada no frontend |
| Migração | Validação, simulação e aplicação transacional de mestres e saldos | Histórico e pacote oficial do legado |
| Frontend | React, rotas protegidas, login, dashboard, catálogo, estoque e solicitações | Detalhes, estados de erro, auditoria e acabamento de fluxo |
| CI/CD | Código versionado e push realizado | Pipeline, deploy Vercel, banco, smoke test e rollback |

## 3. Arquitetura

```text
Navegador
   |
   | HTTPS + JWT
   v
React/TypeScript/Vite (Vercel, frontend/)
   |
   | REST /api/v1/
   v
Django + DRF (Vercel/runtime Python)
   |
   +--> PostgreSQL gerenciado (produção)
   +--> Auditoria transacional
   +--> Importador JSON controlado
```

### 3.1 Organização do backend

- `config/`: settings, WSGI/ASGI e roteamento.
- `apps/core/`: health check e comandos operacionais.
- `apps/accounts/`: usuário, perfil, autenticação e autorização.
- `apps/catalog/`: categorias e produtos.
- `apps/inventory/`: saldo e movimentações.
- `apps/orders/`: solicitações, itens e workflow.
- `apps/audit/`: eventos de auditoria.

### 3.2 Organização do frontend

- `src/context/AuthContext.tsx`: sessão, login, refresh e logout.
- `src/lib/api.ts`: cliente HTTP e armazenamento dos tokens.
- `src/lib/access.ts`: helpers de visibilidade por permissão.
- `src/components/`: layout, cabeçalhos e cards.
- `src/pages/`: login, dashboard, catálogo, estoque, solicitações e auditoria.

## 4. Decisões técnicas

1. **Monólito modular:** mantém transações simples entre estoque, pedidos e auditoria sem custo operacional de microserviços.
2. **PostgreSQL em produção:** oferece persistência e concorrência adequadas; SQLite existe somente como fallback local.
3. **JWT:** adequado para o frontend separado e para a comunicação via API.
4. **Serviços de domínio:** transições de solicitação e movimentações ficam em serviços reutilizáveis, não apenas em views.
5. **Saldo + movimentação:** `StockBalance` permite leitura rápida; `StockMovement` preserva a trilha de alterações.
6. **Importação explícita:** o legado é somente leitura; o novo sistema recebe um JSON validado e só grava com `--apply`.
7. **Frontend desacoplado:** pode ser publicado separadamente e aponta para a API por `VITE_API_BASE_URL`.

## 5. Autorização

As permissões são definidas atualmente em `ROLE_PERMISSIONS`:

| Domínio | Permissões principais |
|---|---|
| Dashboard | `dashboard.view` |
| Catálogo | `catalog.view`, `catalog.manage` |
| Estoque | `stock.view`, `stock.entry`, `stock.exit`, `stock.adjust`, `stock.transfer`, `stock.receive`, `stock.exit_confirm` |
| Solicitações | `requests.create`, `requests.view_own`, `requests.view_department`, `requests.view_all`, `requests.approve`, `requests.process`, `requests.cancel_any` |
| Auditoria | `audit.view` |

Regras de escopo:

- `view_own`: filtra por `requester` igual ao usuário autenticado.
- `view_department`: filtra pelo departamento do perfil do usuário.
- `view_all`: permite leitura global.
- Cancelamento próprio é permitido apenas para o solicitante e em estados elegíveis; cancelamento global exige `requests.cancel_any`.
- O backend é a autoridade final. A ocultação de menus no React é apenas UX.

Pendência técnica: transformar a matriz em entidades persistidas somente se houver necessidade de administrar permissões sem nova publicação.

## 6. Modelo de dados resumido

### Usuários

- `accounts.User`: e-mail único, nome, ativo e credenciais.
- `accounts.UserProfile`: papel, departamento e telefone.

### Catálogo

- `catalog.Category`: nome e ativo.
- `catalog.Product`: SKU, nome, descrição, categoria, unidade, estoque mínimo e ativo.

### Estoque

- `inventory.StockBalance`: produto, quantidade física, quantidade reservada e atualização.
- `inventory.StockMovement`: produto, tipo, delta, referência, observação, usuário e data.

### Solicitações

- `orders.GiftRequest`: solicitante, status, justificativa, aprovador, datas e motivo de rejeição.
- `orders.GiftRequestItem`: produto, quantidade solicitada, reservada e atendida.

### Auditoria

- `audit.AuditEvent`: ator, ação, tipo/id da entidade, metadados JSON, request id e data.

## 7. Regras transacionais críticas

### Reserva

1. Bloquear a solicitação e os saldos relacionados.
2. Calcular `available = quantity - reserved_quantity`.
3. Rejeitar se o disponível for menor que o restante solicitado.
4. Incrementar reserva no saldo e no item.
5. Registrar evento de auditoria.

### Atendimento

1. Aceitar solicitação reservada ou parcialmente atendida.
2. Validar quantidade por item contra o restante.
3. Registrar saída com delta negativo.
4. Reduzir reserva e aumentar quantidade atendida.
5. Definir `partially_fulfilled` ou `fulfilled`.
6. Registrar evento de auditoria.

### Cancelamento

1. Bloquear solicitação e itens.
2. Liberar toda reserva não atendida.
3. Marcar como cancelada.
4. Registrar evento de auditoria.

Todas as etapas ficam dentro de `transaction.atomic`; saldos relacionados usam `select_for_update`.

## 8. Contrato de API atual

Base: `/api/v1/`

- `GET /health/`
- `POST /auth/token/`
- `POST /auth/token/refresh/`
- `GET /auth/me/`
- `GET|POST /catalog/categories/`
- `GET|POST /catalog/products/`
- `GET /inventory/balances/`
- `GET|POST /inventory/movements/`
- `GET|POST /orders/requests/`
- `POST /orders/requests/{id}/submit/`
- `POST /orders/requests/{id}/approve/`
- `POST /orders/requests/{id}/reject/` com `{ "reason": "..." }`
- `POST /orders/requests/{id}/reserve/`
- `POST /orders/requests/{id}/fulfill/` com itens opcionais `{ "items": [{ "item_id": "...", "quantity": 1 }] }`
- `POST /orders/requests/{id}/cancel/`
- `GET /audit/events/`
- `GET /api/docs/`
- `GET /api/schema/`

Pendências de contrato: paginação padronizada, filtros documentados, erros com código estável e endpoints específicos para dashboard/relatórios.

## 9. Migração do legado

Origem inspecionada em modo somente leitura no commit `c8a9dd3`.

Mapeamento atual:

| Origem | Destino |
|---|---|
| `users` | `accounts.User` + `UserProfile` |
| `roles` | `UserProfile.role` |
| `departments` | `UserProfile.department` |
| `categories` | `catalog.Category` |
| `items` | `catalog.Product` |
| `stock` | `inventory.StockBalance` |
| `stock_movements` | Pendente: `inventory.StockMovement` |
| solicitações | Pendente: `orders.GiftRequest` e itens |
| auditoria | Pendente: `audit.AuditEvent` |

Comandos previstos:

```powershell
python manage.py import_legacy docs/legacy-import.example.json
python manage.py import_legacy caminho/para/pacote.json --apply
```

O primeiro comando valida e simula; o segundo grava dentro de uma transação. Antes da aplicação oficial, gerar contagens de usuários, produtos, categorias, saldo físico e saldo reservado e comparar com a origem.

## 10. Segurança e operação

Obrigatório em produção:

- `DJANGO_SECRET_KEY` forte e fora do repositório.
- `DATABASE_URL` apontando para PostgreSQL persistente.
- `DJANGO_DEBUG=false`.
- `DJANGO_ALLOWED_HOSTS` restrito aos domínios usados.
- `CORS_ALLOWED_ORIGINS` restrito ao frontend.
- Banco de preview separado do banco de produção.
- Backup e política de retenção definidos pelo provedor.
- Logs sem senha, token ou dados pessoais desnecessários.

Pontos a implementar:

- pipeline de lint, testes e build;
- smoke test pós-deploy;
- monitoramento de erros;
- procedimento de rollback;
- gestão de segredos e banco documentada;
- testes de carga e concorrência para reserva/atendimento.

## 11. Verificação técnica já realizada

- `npm install` executado com sucesso.
- `npm run build` do frontend executado com sucesso.
- `npm audit --omit=dev --audit-level=high` sem vulnerabilidades altas encontradas.
- Tela de login verificada visualmente em execução local.
- Código versionado no GitHub no commit `05f5f2d`.

Limitação atual: não foi possível executar Django migrations/testes backend nesta máquina porque o runtime Python não está instalado. Isso deve ser executado no CI ou no ambiente de desenvolvimento/deploy antes do go-live.

## 12. Plano técnico de conclusão

1. Provisionar PostgreSQL e autenticar na Vercel.
2. Configurar projeto da API e projeto do frontend.
3. Adicionar variáveis de ambiente e restringir CORS/hosts.
4. Executar migrations, criar usuário administrador e validar health check.
5. Publicar frontend apontando para a API.
6. Conectar formulário e detalhe completo de solicitações.
7. Conectar consulta de auditoria.
8. Criar testes backend para permissões, isolamento, reserva, cancelamento e atendimento parcial.
9. Criar testes de jornada do frontend.
10. Rodar simulação de migração, corrigir divergências e executar carga oficial.
11. Fazer aceite com usuários dos cinco perfis.
12. Publicar release e acompanhar o primeiro ciclo operacional.
