# Matriz de paridade funcional

**Referência:** projeto legado `GestaoBrinde`, analisado em modo somente leitura.  
**Objetivo:** reimplementar suas funções em React/TypeScript, preservando fluxos e regras de negócio; não reduzir o produto a um MVP de catálogo e solicitações.

## Como ler esta matriz

- **Parcial:** há uma tela ou regra básica, mas falta parte relevante do fluxo legado.
- **Ausente:** o módulo não está disponível no modo executado no navegador.
- O Django existente no repositório reestruturado não conta como entregue para o usuário enquanto o frontend local publicado não o consome.
- JSON em `seed.json` é apenas a carga inicial; `localStorage` guarda uma cópia independente por navegador/perfil. Isso não sincroniza usuários, computadores ou navegadores.

## Comparação por módulo

| Módulo do Gestão de Brindes | Estado reestruturado | O que falta para paridade |
|---|---|---|
| Login, sessão, perfil e recuperação de senha | Parcial | Perfil editável, troca/recuperação de senha e sessão com controles equivalentes. Credenciais e autorização no frontend não oferecem segurança de produção. |
| Dashboard operacional | Parcial | Indicadores e atalhos equivalentes, com filtros e dados de eventos, recebimentos, retiradas, aprovações e relatórios. |
| Usuários | Parcial | Gestão local inicial adicionada; faltam vínculo com indústria, lixeira, regras completas de status/sessão e confirmação do fluxo legado. |
| Perfis e permissões | Parcial | Permissões locais configuráveis adicionadas; faltam catálogo completo de permissões e barreiras confiáveis no servidor. |
| Catálogo de brindes | Parcial | CRUD básico existe; faltam código sequencial legado, fotos, detalhe/histórico, exclusão lógica e lixeira. |
| Cadastros auxiliares | Parcial | Categorias, departamentos, indústrias, locais e fornecedores com CRUD local inicial; faltam campos e validações próprios de cada cadastro e relacionamentos. |
| Livro de estoque | Parcial | Saldo agregado e movimentos simples; falta trilha completa filtrável, reversões e posições por local. |
| Entrada de estoque / recebimento | Parcial | Entrada simples existe; falta recebimento TRADE, nota fiscal/anexo e confirmação operacional do CD. |
| Saída e fila de confirmação do CD | Ausente | Registro da saída pelo gestor separado da confirmação pelo CD, QR e estados da ordem de saída. |
| Ajuste, estorno e transferência | Ausente | Ajuste auditável, estorno de movimento e transferência entre locais com validação de origem/destino. |
| Estoque por indústria | Ausente | Vínculo de saldo/solicitação à indústria e filtros de acesso e consulta. |
| Solicitações internas | Parcial | Criar, submeter, aprovar/rejeitar, reservar, atender parcial e cancelar em uma tela; faltam fluxos/status legados, detalhe e histórico formal. |
| Aprovações e regras configuráveis | Parcial | Ação básica de aprovar/rejeitar; faltam fila própria, regras por perfil/departamento/valor e histórico de decisão. |
| Separação e entrega interna | Ausente | Fila de picking, separação, entrega e confirmação do recebedor. |
| TRADE / compras | Ausente | Solicitação de compra, aprovação, acompanhamento da compra, código do chamado e integração/outbox Lecom quando habilitada. |
| Recebimento de compra no CD | Ausente | Conferir itens/quantidades e registrar NF/entrada contra solicitação TRADE. |
| Retirada, QR e assinatura | Ausente | Validar QR, registrar retirada e capturar assinatura. |
| Eventos e feirões | Ausente | Cadastro do evento, alocação de brindes, saldo do evento e modo de retirada. |
| Protocolos / comprovantes | Ausente | Histórico de entregas, protocolo PDF com QR/assinatura e reenvio/consulta. |
| Relatórios e exportação | Ausente | Estoque, entradas/saídas, movimentação, distribuições, pedidos, aprovações, mínimos, protocolos, eventos e exportação CSV/Excel. |
| Importação de planilha | Ausente | Leitura, pré-validação, simulação, relatório de inconsistências e aplicação confirmada. |
| Notificações | Ausente | Caixa de notificações, alertas operacionais e entrega por e-mail quando existir serviço de servidor. |
| Auditoria | Parcial | Eventos básicos e filtros existem; faltam cobertura de todos os módulos, identidade completa do ator, histórico consultável e exportação. |
| Configurações, logo e backup/restauração | Ausente | Preferências, identidade visual, teste de e-mail e exportação/restauração controlada do JSON. |
| Busca global e saúde operacional | Ausente | Pesquisa entre módulos e diagnóstico visível do estado dos dados locais. |

## Plano de recuperação de paridade

### Sprint P0 — Fundação e critérios de paridade

- Manter o legado como referência somente leitura e mapear telas, permissões, estados e regras.
- Corrigir PRD/TRD para declarar paridade como objetivo e JSON/localStorage como modo temporário atual.
- Criar base de cadastros, usuários e permissões por perfil no modo local.
- Impedir que ações de domínio ignorem as permissões selecionadas na interface.

**Estado:** em andamento. Gestão local inicial de usuários, cadastros e permissões foi adicionada; revisão e validação de regras continuam pendentes.

### Sprint P1 — Catálogo e estoque

- Completar cadastro/detalhe/histórico de brindes e campos de referência.
- Implementar posições por local, entrada, saída/ordem, confirmação pelo CD, ajuste/estorno e transferência.
- Registrar referências, documentos e trilha de cada movimento.

**Estado:** pendente; saldo, entrada simples e movimentos básicos são apenas uma base.

### Sprint P2 — Solicitações e operação interna

- Reproduzir os fluxos e estados legados de solicitação interna.
- Implementar regras configuráveis de aprovação, filas, picking, entrega e comprovante.
- Validar permissões e recortes por usuário, departamento e indústria.

**Estado:** pendente; ações básicas de solicitação não equivalem aos fluxos completos.

### Sprint P3 — TRADE, recebimento, retirada e eventos

- Implementar compra TRADE, recebimento no CD e registro de nota fiscal.
- Implementar QR, retirada, assinatura e protocolo.
- Implementar eventos/feirões, alocação e saldo dedicado.

**Estado:** pendente.

### Sprint P4 — Relatórios, importação e administração

- Reproduzir relatórios e exportações do legado.
- Implementar importação validada e reconciliável.
- Completar notificações, configurações, auditoria, backup/restauração e busca.

**Estado:** pendente.

### Sprint P5 — Homologação e saída do modo local

- Comparar uma jornada de cada perfil com o sistema legado.
- Importar uma cópia validada dos dados e reconciliar produtos/saldos.
- Definir persistência central e autenticação de servidor antes de operação multiusuário.

**Estado:** pendente. LocalStorage não compartilha dados entre pessoas ou dispositivos, e não deve ser tratado como banco multiusuário ou mecanismo seguro de autenticação.

## Critério de conclusão

Um módulo só muda para **Parcial** ou **Concluído** mediante tela acessível, regras de negócio funcionais, permissões correspondentes e dados persistidos no modo ativo. Uma rota vazia, documentação de API ou código desconectado do frontend não é paridade entregue.

## Referências do legado consultadas

- `docs/Mapa-de-Modulos.md`
- `docs/Perfis-e-Permissoes.md`
- `docs/AppFlow.md`
- `app/pages.php` e `app/Support/Menu.php`
- Views em `resources/Views/pages/`
