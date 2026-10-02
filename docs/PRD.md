# PRD — Gestão de Brindes Reestruturado

**Versão:** 1.1
**Data:** 02/10/2026
**Status:** Reestruturação em andamento; a versão atual ainda não tem paridade com o Gestão de Brindes legado.

## 1. Objetivo e princípio de paridade

O projeto reestruturado deve reproduzir as funcionalidades e regras de negócio do sistema Gestão de Brindes existente, usando uma stack diferente. O legado é a referência funcional e permanece somente para consulta durante a migração.

Não reduzir o escopo a login, catálogo, saldo e solicitação básica. A paridade inclui usuários e perfis, cadastros, estoque, solicitações internas, TRADE, aprovações, atendimento, eventos, retirada, comprovantes, relatórios, importação, notificações, auditoria e configurações, respeitando os limites de infraestrutura desta fase.

O inventário comparativo e o estado real por módulo estão em [PARIDADE-FUNCIONAL.md](./PARIDADE-FUNCIONAL.md). Um módulo só é considerado entregue se estiver acessível na interface, funcionar no modo ativo e aplicar suas regras de negócio.

## 2. Decisão atual de armazenamento

Por enquanto, o sistema roda como frontend React/TypeScript na Vercel, com `seed.json` para carga inicial e `localStorage` para alterações locais. Não instalar Docker nem depender de Python para esta fase.

Essa decisão permite desenvolver e demonstrar fluxos sem banco, mas não cria um banco compartilhado: cada navegador mantém sua própria cópia. Mudanças não aparecem automaticamente para outras pessoas ou dispositivos; limpar os dados do navegador pode apagá-las. Credenciais e permissões executadas somente no frontend não formam autenticação segura de produção.

Assim, a meta imediata é recuperar a paridade de interface e de regras no modo local, documentando operações que dependem de serviço externo. Persistência multiusuário, e-mail real e integrações externas ficam condicionados à futura inclusão de um serviço central, sem alterar o escopo funcional desejado.

## 3. Usuários e perfis

| Perfil | Responsabilidade |
|---|---|
| Administrador | Usuários, perfis, permissões, configurações e supervisão global |
| TRADE / Gestor | Solicitações de compra, aprovações, estoque autorizado, eventos e relatórios |
| CD / Estoque | Recebimento, armazenamento, confirmação de saídas, transferências, retiradas e protocolos |
| Solicitante | Criar e acompanhar as próprias solicitações |
| Indústria | Consultar e operar somente os dados associados à sua indústria |

Os recortes de acesso devem ser equivalentes aos do legado: próprio usuário, departamento, perfil e indústria. Esconder um menu não substitui validação da ação e do dado acessado.

## 4. Escopo funcional

O escopo-alvo inclui todos os módulos listados na [matriz de paridade](./PARIDADE-FUNCIONAL.md), incluindo:

- Autenticação, perfil, usuários e permissões administráveis.
- Catálogo de brindes, categorias e demais cadastros auxiliares.
- Saldo por local, livro de movimentações, entrada, saída, fila de confirmação do CD, ajuste/estorno e transferência.
- Solicitações internas, aprovações configuráveis, separação, atendimento parcial/total, retirada e comprovante.
- Fluxo TRADE de compra, recebimento de itens/notas fiscais e retirada por QR/assinatura.
- Eventos/feirões, alocação e saldo de evento.
- Relatórios e exportações, importação validada, notificações, auditoria, busca, configurações e rotinas de cópia/restauração compatíveis com o modo local.

Integrações que exigem servidor (envio real de e-mail, sincronização Lecom e persistência central) precisam ser identificadas como dependências; não podem ser representadas como concluídas por uma tela demonstrativa.

## 5. Fluxos centrais de aceite

### Solicitação interna

Solicitante cria e envia pedido; o mecanismo aplica as regras de aprovação; aprovador aprova ou rejeita com motivo; operação separa e registra atendimento, inclusive parcial; o saldo é atualizado; solicitante e operação consultam o histórico e o comprovante conforme sua permissão.

### TRADE e recebimento

Solicitante registra necessidade de compra; gestor aprova e acompanha; chegada é recebida no CD com quantidades e dados da nota; o estoque é atualizado; a retirada é autorizada e registrada; QR, assinatura e protocolo preservam a evidência.

### Estoque

Entrada, saída, ajuste, estorno e transferência atualizam posições e livro de forma rastreável. Registro de saída pelo gestor e confirmação física pelo CD são etapas distintas. Não permitir saldo físico/reservado inconsistente.

## 6. Requisitos não funcionais

- Interface responsiva em português e acessível por teclado.
- Preservar histórico e impedir exclusão acidental de registros referenciados.
- Validar campos, transições, permissões e quantidades antes de persistir.
- Permitir exportar/cópia de dados JSON para recuperação durante o modo local.
- Marcar claramente os limites de sincronização, autenticação e armazenamento local.
- Preparar contratos e modelos para substituir o adaptador local por persistência central sem redesenhar fluxos.

## 7. Plano de sprints

As sprints são organizadas por dependência funcional; estimativas devem ser revistas após homologação detalhada dos formulários e regras do legado.

### Sprint P0 — Paridade e fundação

- Fechar matriz com o legado em modo somente leitura.
- Corrigir o PRD/TRD e declarar o armazenamento local como temporário.
- Implementar base local de usuários, cadastros auxiliares e permissões configuráveis.
- Centralizar validação local de acesso, escopo e mudanças auditáveis.

**Status:** em andamento. Gestão local inicial de usuários/cadastros/permissões foi adicionada; falta revisar escopos, segurança do modo temporário e homologar os perfis.

### Sprint P1 — Catálogo e estoque completo

- Brindes: sequência de código, cadastro, foto, detalhe, histórico e lixeira.
- Estoque: posições por local, NF/anexos compatíveis, saídas/fila CD, ajustes, estornos e transferências.
- Estoque por indústria e filtros do livro de movimentos.

**Status:** pendente. A implementação atual cobre apenas CRUD básico de catálogo, saldo agregado, entrada simples e movimentos básicos.

### Sprint P2 — Solicitações e operação interna

- Formulário/detalhe/histórico e estados equivalentes aos do legado.
- Regras de aprovação editáveis por perfil e escopo.
- Filas de aprovação e picking, separação, entrega e comprovantes.

**Status:** pendente. A tela atual tem um fluxo simplificado, sem a operação completa.

### Sprint P3 — TRADE, recebimento e eventos

- Solicitação de compra e acompanhamento TRADE.
- Recebimento pelo CD com conferência de item, quantidade e nota fiscal.
- QR, assinatura e retirada; eventos/feirões e controle de alocação.

**Status:** pendente.

### Sprint P4 — Protocolos, relatórios e administração

- Protocolos consultáveis e exportáveis.
- Relatórios do legado com exportação.
- Importação de planilha com validação, simulação e reconciliação.
- Notificações, busca, configurações, auditoria completa e cópia/restauração local.

**Status:** pendente; auditoria é apenas parcial e os demais módulos não estão na interface atual.

### Sprint P5 — Homologação de paridade

- Percorrer a matriz com representantes de cada perfil.
- Comparar cada jornada e regra com o sistema legado.
- Validar importação em cópia e reconciliar cadastros, estoque e históricos.
- Definir infraestrutura central antes de liberar operação compartilhada.

**Status:** pendente.

## 8. Definição de pronto

Para cada item funcional: tela navegável, validação e estados corretos, restrição por perfil/escopo, persistência coerente com o modo escolhido, registro de auditoria quando aplicável e documentação atualizada. Recursos dependentes de backend devem estar explicitamente identificados como indisponíveis no modo local, não descritos como entregues.
