# Migração do sistema legado

O sistema legado foi inspecionado em modo somente leitura no commit `c8a9dd3`.
Nenhum arquivo ou banco de origem é alterado pelo novo projeto.

## Mapeamento inicial

| Legado | Novo backend | Tratamento |
|---|---|---|
| `users` | `accounts.User` + `UserProfile` | E-mail, nome, ativo, perfil e departamento |
| `roles` | `UserProfile.role` | `admin`, `approver`, `operations`, `requester`, `industry` |
| `departments` | `UserProfile.department` | Preservado como texto na primeira carga |
| `categories` | `catalog.Category` | Nome e ativação |
| `items` | `catalog.Product` | `code -> sku`, nome, descrição, unidade e estoque mínimo |
| `stock` | `inventory.StockBalance` | Saldo físico e reservado |
| `stock_movements` | `inventory.StockMovement` | Será importado em uma etapa posterior de histórico |
| solicitações | `orders.GiftRequest` | Requer pacote histórico com itens e estados |
| auditoria | `audit.AuditEvent` | Requer normalização de ação e entidade |

## Processo seguro

1. Exportar uma cópia do legado sem executar escrita na origem.
2. Converter para o contrato de `legacy-import.example.json`.
3. Executar `python manage.py import_legacy caminho.json` para validação/simulação.
4. Conferir duplicidades, perfis, produtos e saldos.
5. Executar com `--apply` somente após a conferência.
6. Comparar totais de produtos, usuários, saldo físico e saldo reservado.

O importador falha antes de gravar se houver e-mails/códigos duplicados, perfil
desconhecido, produto inexistente ou saldo reservado maior que o saldo físico.

