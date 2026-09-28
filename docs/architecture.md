# Arquitetura inicial

## Contexto

O backend será um monólito modular. Cada domínio terá seu próprio app Django, modelos, regras e endpoints, compartilhando a mesma aplicação e o PostgreSQL.

## Decisões

1. PostgreSQL é a fonte persistente oficial.
2. O deploy inicial será feito na Vercel usando o runtime Python e um PostgreSQL gerenciado.
3. JSON não será usado como banco operacional; servirá apenas para fixtures e importação/exportação controlada.
4. A API será versionada em `/api/v1/`.
5. O usuário usa e-mail como identificador de autenticação.
6. Estoque será tratado como movimentações transacionais, com saldo derivado e trilha de auditoria.
7. React/TypeScript consumirá a API; Tauri será tratado como camada de distribuição futura.

## Limites de domínio planejados

- `accounts`: identidade, grupos e permissões.
- `catalog`: itens, categorias, fornecedores e unidades.
- `inventory`: entradas, saídas, reservas, ajustes e saldos.
- `orders`: solicitações, aprovação e atendimento.
- `audit`: ator, ação, entidade, alterações e contexto da requisição.

Usuários possuem um `UserProfile` com papel funcional (`requester`, `approver`,
`operator` ou `admin`), departamento e telefone. A autorização fina por papel será
consolidada junto com as permissões de cada domínio.

## Estoque

O saldo operacional é mantido em `StockBalance` e cada alteração gera um `StockMovement`.
Movimentações são registradas por `register_movement` dentro de `transaction.atomic`,
com bloqueio pessimista do saldo (`select_for_update`). Saídas não podem consumir
quantidade reservada nem deixar o saldo disponível negativo.

## Fluxo de solicitações

Uma solicitação segue o fluxo `draft -> submitted -> approved -> reserved -> fulfilled`.

- Envio valida que há itens e registra o momento da submissão.
- Aprovação exige um usuário operador (`is_staff`).
- Reserva bloqueia cada saldo por produto e incrementa `reserved_quantity` atomically.
- Atendimento gera movimentações de saída, reduz a reserva e registra o operador.

As transições são serviços de domínio para que a API, o admin e futuros comandos de
importação compartilhem as mesmas regras.

## Auditoria

Eventos imutáveis registram ação, ator, tipo e identificador da entidade, metadados
estruturados e, quando disponível, o identificador da requisição. A consulta é restrita
a operadores; gravações acontecem dentro da mesma transação da operação de negócio.
