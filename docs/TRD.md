# TRD — Gestão de Brindes

**Versão:** 1.1
**Data:** 29/09/2026
**Escopo:** estado técnico atual, decisões, entregas e plano de conclusão

## 1. Resumo técnico

O sistema é um monólito modular Django com API REST versionada, autenticação JWT, PostgreSQL como banco oficial e React/TypeScript/Vite como frontend. O usuário informa que já publicou na Vercel, mas o ambiente/URL, runtime da API, banco e smoke test não foram verificados neste trabalho. Também é possível hospedar a API e/ou o sistema completo em VM seguindo os requisitos deste documento.

Em Vercel, o runtime Python é provisionado pelo ambiente de hospedagem. Em VM, a equipe opera o runtime Python e o servidor WSGI; Docker é opcional, útil para padronizar serviços e ambiente.

## 2. Estado atual da implementação

| Área | Implementado | Pendente |
|---|---|---|
| Backend Django | Apps `core`, `accounts`, `catalog`, `inventory`, `orders`, `audit`; API, migrations, serviços; 50 testes Django e 10 testes Node executados; build e checks locais aprovados | Validar transações críticas no PostgreSQL e homologar no ambiente publicado; Ruff local bloqueado pelo Controle de Aplicativo |
| Autenticação | Usuário por e-mail, JWT, `/auth/me/`, refresh e autorização por perfil | Homologar matriz/isolamento com usuários reais; definir recuperação de senha e política de sessão |
| Autorização | CD tem fila TRADE/posições globais; perfil indústria vê indústria vinculada; saldo/posições/locais globais negados ao papel industry | Alçadas por regra original, escopos por evento/warehouse e aceitação de todos os perfis |
| Catálogo | API e tela de produtos com listagem, criação, edição, ativação/desativação lógica, busca e filtros | Paginação; manutenção de categorias na UI, se requerida; aceite dos dados reais |
| Estoque | Saldos globais e posições por local; transferências atômicas com movimentos `−qty/+qty`; entradas/saídas atualizam posição; saída genérica QR e TRADE com chamado/NF numérica/retirada assinada | Anexo NF, PDF, eventos/cotas, ajustes UI, retornos e concorrência PostgreSQL |
| Solicitações | API e UI para múltiplos itens, envio, aprovação/rejeição, reserva, cancelamento e atendimento parcial por item | Homologação de ponta a ponta, testes automatizados de jornada e aceite operacional |
| Auditoria | Registro, endpoint protegido com filtros e paginação e página web conectada | Validar visibilidade/conteúdo e definir retenção/monitoramento |
| Migração | Validação, simulação e aplicação transacional de usuários, perfis, departamentos, categorias, produtos e saldos | Pacote oficial, ensaio/reconciliação; histórico adicional depende de aprovação de escopo |
| Frontend | React: login, dashboard, catálogo, estoque/setor/local, transferência, TRADE criação/aprovação/recebimento/retirada assinada, solicitações e auditoria | Walkthrough restante, leitor físico, PDF, eventos/feirões e restantes páginas/filas originais |
| CI/CD | Workflow de CI e deploys anteriores registrados no GitHub; CI backend/frontend confirmado no commit `b7f58b9` | Confirmar o deploy atualmente publicado, smoke test real, backup/restore, monitoramento e rollback |

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
   +--> PostgreSQL persistente (produção; ainda confirmar/configurar)
   +--> Auditoria transacional
   +--> Importador JSON controlado (JSON é formato de importação, não banco da aplicação)
```

Alternativa em VM: navegador → HTTPS/proxy reverso (Nginx/Caddy) → Django servido por Gunicorn → PostgreSQL. O frontend pode ser servido como arquivos estáticos nessa VM ou continuar na Vercel. Essa alternativa está documentada, mas não foi provisionada nem testada.

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
- `src/lib/api.ts`: cliente HTTP da API Django e armazenamento local dos tokens JWT; o banco de domínio permanece no backend.
- `src/lib/access.ts`: helpers de visibilidade por permissão.
- `src/components/`: layout, cabeçalhos e cards.
- `src/pages/`: login, dashboard, catálogo, estoque, solicitações e auditoria; TRADE também usa endpoints do backend.

A implementação local JSON foi removida do caminho ativo; `seed.json` remanescente não contém senhas nem é importado pela aplicação. Dados `localStorage` de versões anteriores não sincronizam automaticamente.
## 4. Decisões técnicas

1. **Monólito modular:** mantém transações simples entre estoque, pedidos e auditoria sem custo operacional de microserviços.
2. **PostgreSQL em produção:** oferece persistência e concorrência adequadas; SQLite existe somente como fallback local. Arquivo JSON local não é banco operacional em Vercel e não foi implementado como fonte de verdade. JSON continua aceito para importação/exportação validada; eventual armazenamento JSON externo exige definir atomicidade, concorrência, backup e recuperação antes de implementação.
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
- `accounts.UserProfile`: papel, departamento, telefone e vínculo opcional `industry_id` para escopo server-side.

### Catálogo

- `catalog.Industry`: nome e ativo; manutenção por API `catalog.manage`.
- `catalog.Category`: nome e ativo.
- `catalog.Product`: SKU, nome, descrição, categoria, unidade, estoque mínimo e ativo.

### Estoque

- `inventory.StockLocation`, `StockPosition` e `StockTransfer`: locais, posição por produto/local e transferências auditáveis.
- `inventory.StockBalance`: quantidade física global e reservada por produto.
- `inventory.StockExitOrder`: produto, indústria/local opcional, quantidade, solicitante, token QR, confirmação/cancelamento.
- `inventory.StockMovement`: produto, indústria/local/destino opcional, tipo/delta, transferência, referência, autor e data.

### Solicitações

- `orders.GiftRequest`/`GiftRequestItem`: solicitação interna do frontend reconstruído.
- `orders.TradeRequest`/`TradeRequestItem`: fluxo TRADE com indústria, chamado, NF numérica e recebimento por linha.
- `orders.TradeRequestHistory`: ator, transições e comentários.
- `orders.TradeDelivery`/`TradeDeliveryItem`: protocolo TRADE sequencial, recebedor, assinatura PNG registrada no banco e saldo após baixa.

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
- `GET|PATCH /auth/profiles/{id}/` (apenas admin; atribui perfil/indústria)
- `GET|POST /catalog/industries/`
- `GET|POST /catalog/categories/`
- `GET|POST /catalog/products/`
- `GET /inventory/balances/` (saldo físico global; não concedido ao papel industry)
- `GET /inventory/industry-balances/` (agregado por movimentos; escopo da indústria vinculada aplicado no backend)
- `GET|POST /inventory/locations/` (leitura CD/transfer; escrita apenas admin)
- `GET /inventory/positions/` (posições CD/evento; industry sem acesso global)
- `GET|POST /inventory/transfers/` (saldo total invariável; movimentos `−qty/+qty`)
- `GET|POST /inventory/movements/` (API rejeita saída imediata; usar ordem QR em duas etapas)
- `GET|POST /inventory/exit-orders/` (autorização/listagem por perfil)
- `POST /inventory/exit-orders/{id}/cancel/` (autor/admin; libera reserva)
- `POST /inventory/exit-orders/confirm-by-qr/` (CD envia o token escaneado)
- `GET|POST /orders/requests/`
- `POST /orders/requests/{id}/submit/`
- `POST /orders/requests/{id}/approve/`
- `POST /orders/requests/{id}/reject/` com `{ "reason": "..." }`
- `POST /orders/requests/{id}/reserve/`
- `POST /orders/requests/{id}/fulfill/` com itens opcionais `{ "items": [{ "item_id": "...", "quantity": 1 }] }`
- `POST /orders/requests/{id}/cancel/`
- `GET|POST /trade/requests/` (fluxo separado por indústria)
- `POST /trade/requests/{id}/approve/` (chamado obrigatório)
- `POST /trade/requests/{id}/reject/` (motivo obrigatório)
- `POST /trade/requests/{id}/receive/` (NF numérica e quantidades por item)
- `POST /trade/requests/{id}/withdraw/` (public_code QR, recebedor, assinatura PNG e quantidades)
- `GET /audit/events/`
- `GET /api/docs/`
- `GET /api/schema/`

Pendências de contrato: paginação também no catálogo, documentação padronizada de filtros/erros e endpoints específicos para dashboard/relatórios, conforme prioridade do produto.

## 9. Migração do legado

Origem inspecionada em modo somente leitura no commit `857747a199dc73d2e7ab1f0cd872424a59ca46c0`.

Mapeamento atual:

| Origem | Destino |
|---|---|
| `users` | `accounts.User` + `UserProfile` |
| `roles` | `UserProfile.role` |
| `departments` | `UserProfile.department` |
| `categories` | `catalog.Category` |
| `items` | `catalog.Product` |
| `stock` | `inventory.StockBalance` global; `StockPosition` por local será preenchida no backfill do schema |
| `stock_movements` | `inventory.StockMovement` com indústria/local; importação histórica não implementada |
| solicitações TRADE | `orders.TradeRequest`/itens/histórico/entregas; migração do legado ainda pendente |
| solicitações internas | `orders.GiftRequest`/itens; completar campos/estados e migrar histórico |
| auditoria | `audit.AuditEvent`; importação histórica pendente |

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

Implementado no repositório: CI de backend/frontend, configuração de produção validada por checks e documentação de go-live. Pendente no ambiente real: smoke test pós-deploy, monitoramento de erros, rollback testado, confirmação de backups e teste PostgreSQL concorrente de reserva/atendimento.

## 11. Verificação técnica já realizada

- Nesta atualização documental: backend `25 passed in 7.95s`; Ruff `All checks passed!`; `manage.py check` sem problemas; `makemigrations --check --dry-run` sem mudanças; `npm run build` concluído com sucesso (TypeScript/Vite).
- CI remoto do commit `b7f58b9` teve checks backend/frontend aprovados, conforme verificação registrada anteriormente.
- Esses resultados são evidência de código/CI, não comprovam banco, URL, variáveis ou estado do deploy atual da Vercel.

## 12. Status técnico por sprint

| Sprint | Implementado no repositório | Falta / dependência para concluir |
|---|---|---|
| 0 — Fundação | Arquitetura, requisitos, contratos e checklist documentados | Confirmar Vercel/domínios/runtime, persistência durável, responsáveis, regras finais e export legado |
| 1 — Acesso | JWT, perfis, permissões e escopo de solicitações; testes automatizados | Homologação com contas reais, matriz aprovada e política de sessão/recuperação |
| 2 — Catálogo/estoque | CRUD de produtos, busca/filtros, saldos, movimentações, reservas e validações | Paginação e testes de concorrência em PostgreSQL; aceitar histórico/transferência com negócio |
| 3 — Solicitações | UI/API do ciclo principal, múltiplos itens, aprovação, rejeição, reserva, parcial e cancelamento | Teste de jornada no ambiente publicado e aceite de usuário |
| 4 — Auditoria/migração | Auditoria filtrável/paginada e importador transacional com simulação | Export oficial, ensaio/reconciliação e decisão sobre histórico legado |
| 5 — Deploy/operação | Configuração de produção, CI, documentação operacional; usuário relata deploy Vercel | Verificação independente, DB persistente, env vars, migrations, smoke, backup/restore, rollback e monitoramento |

## 13. Requisitos de VM

Sizing inicial para implantação pequena; revisar por teste de carga e métricas reais.

| Uso | CPU | RAM | Disco |
|---|---:|---:|---:|
| Dev/homologação | 2 vCPU | 4 GB | 40 GB SSD persistente |
| Produção inicial recomendada | 4 vCPU | 8 GB | 100 GB SSD/NVMe; PostgreSQL preferencialmente gerenciado/separado |
| Piloto tudo-em-um | 4 vCPU | 8 GB | 150 GB SSD/NVMe, com DB e API na VM; não é alta disponibilidade |

**Software:** Ubuntu Server 24.04 LTS x86_64; Python 3.13 e Django 5.2; PostgreSQL 16; Node.js 22 somente para build do frontend; Gunicorn como WSGI; Nginx ou Caddy como proxy TLS. `gunicorn` não consta nas dependências atuais e precisa ser adicionado/configurado/testado antes da hospedagem da API em VM.

**Rede/segurança/operação:** publicar somente 443 (e 80 para redirecionamento/ACME); restringir SSH por IP/chave; não expor 5432; usar segredos fora do Git; banco persistente; backup cifrado fora da VM com restore ensaiado; monitorar disco, CPU, RAM, disponibilidade e logs; manter preview e produção isolados. Definir RPO/RTO, retenção e responsável operacional. O sizing não implica HA nem comprova adequação a qualquer volume de usuários.

**Pré-requisitos para VM:** revisar `docker-compose.yml` antes de produção (as credenciais atuais são apenas locais e não devem ser reutilizadas); preparar serviço de aplicação/health check, proxy/TLS, migrations sob processo controlado, firewall, backups e runbook de rollback. O frontend pode permanecer na Vercel via `VITE_API_BASE_URL` apontando à API da VM.
