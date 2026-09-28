# PRD — Gestão de Brindes

**Versão:** 1.0  
**Data:** 28/09/2026  
**Status:** Base funcional implementada; homologação, migração final e deploy pendentes

## 1. Visão do produto

O Gestão de Brindes centraliza catálogo, estoque e solicitações de brindes em um fluxo controlado por perfil, departamento e trilha de auditoria. O produto substitui o uso fragmentado do sistema legado por uma API transacional e uma aplicação web responsiva.

O primeiro release deve permitir que um solicitante escolha itens, envie uma solicitação e acompanhe seu status; que aprovadores validem solicitações do seu escopo; e que a operação reserve, atenda parcial ou totalmente e mantenha o estoque rastreável.

## 2. Objetivos

- Reduzir solicitações manuais e perda de rastreabilidade.
- Evitar aprovação, reserva ou baixa de estoque fora do escopo autorizado.
- Exibir saldo disponível com distinção entre quantidade física e reservada.
- Migrar os dados essenciais do legado sem alterar a origem.
- Publicar uma primeira versão web na Vercel com banco PostgreSQL persistente.

## 3. Fora do escopo do primeiro release

- Aplicativo nativo/Tauri.
- Integração com ERP, compras ou transportadora.
- Notificações por e-mail, WhatsApp ou push.
- Upload de anexos e assinatura eletrônica.
- Configuração de permissões por tela feita pelo próprio administrador.
- Importação completa do histórico de movimentações, solicitações e auditoria do legado.

## 4. Perfis e responsabilidades

| Perfil | Responsabilidade principal | Visibilidade esperada |
|---|---|---|
| Administrador | Configurar e supervisionar o sistema | Todos os dados e operações |
| Aprovador | Analisar solicitações do escopo de aprovação | Próprio departamento e, quando autorizado, todos |
| Operador de estoque | Cadastrar/atualizar catálogo, movimentar estoque e atender solicitações | Estoque e solicitações operacionais |
| Solicitante | Criar e acompanhar pedidos próprios | Catálogo e próprios pedidos |
| Indústria | Consultar catálogo e informações autorizadas | Catálogo e próprios pedidos |

## 5. Requisitos funcionais

### RF-01 — Autenticação e perfil

- Login por e-mail e senha via JWT.
- Consulta do usuário autenticado, perfil e departamento.
- Expiração e renovação de token.
- Navegação e ações condicionadas às permissões do perfil.

**Status:** Implementado no backend e frontend. Falta homologar cenários de erro, recuperação de senha e política definitiva de sessão.

### RF-02 — Controle de acesso

- Permissões separadas para dashboard, catálogo, estoque, solicitações e auditoria.
- Escopo próprio, departamento ou global para leitura de solicitações.
- Usuário não pode acessar ou alterar dados fora do seu escopo.
- Ações sensíveis devem ser bloqueadas no backend, mesmo que o frontend oculte o botão.

**Status:** Implementado com matriz estática por perfil. Falta decidir se permissões customizáveis serão necessárias após a homologação.

### RF-03 — Catálogo

- Listar categorias e produtos ativos.
- Exibir SKU, nome, descrição, unidade e estoque mínimo.
- Criar e atualizar categorias/produtos para perfis autorizados.
- Impedir exclusão que quebre histórico; preferir desativação.

**Status:** API e tela inicial implementadas. Falta completar edição, filtros avançados, paginação, validações de formulário e testes de aceite.

### RF-04 — Estoque

- Exibir quantidade física, reservada e disponível.
- Registrar entrada, saída e ajuste.
- Bloquear saldo disponível negativo.
- Manter movimentação vinculada ao usuário, produto, referência e observação.
- Reservar itens durante o processamento de uma solicitação.

**Status:** Regras transacionais e tela inicial implementadas. Falta validar com dados reais e completar filtros, histórico visual e fluxo de transferência, se necessário.

### RF-05 — Solicitações

- Criar rascunho com um ou mais produtos.
- Enviar solicitação com justificativa.
- Aprovar ou rejeitar com motivo.
- Reservar estoque de solicitações aprovadas.
- Atender parcialmente ou totalmente.
- Cancelar solicitação elegível e liberar reservas.
- Exibir histórico/status ao solicitante.

**Status:** Backend implementado, incluindo rejeição, cancelamento e atendimento parcial. Frontend possui listagem e ações básicas; falta fechar formulário completo, detalhe da solicitação e confirmação das transições.

### RF-06 — Auditoria

- Registrar ações relevantes com ator, entidade, data, metadados e request id quando disponível.
- Permitir consulta restrita a perfis autorizados.
- Filtrar por período, usuário, entidade e ação.

**Status:** Registro backend implementado. Tela frontend ainda é placeholder e o endpoint precisa de filtros e paginação para uso operacional.

### RF-07 — Migração

- Ler pacote exportado do legado sem escrita na origem.
- Validar campos obrigatórios, duplicidades, perfis e saldos.
- Executar simulação antes da aplicação.
- Aplicar em transação única somente após conferência.
- Comparar totais antes/depois.

**Status:** Importador validado para usuários, perfis, departamentos, categorias, produtos e saldos. Histórico de movimentações, solicitações e auditoria ainda precisa de mapeamento e implementação.

## 6. Fluxo principal

1. Solicitante entra no sistema.
2. Consulta o catálogo e cria um pedido.
3. Envia o pedido para aprovação.
4. Aprovador aprova ou rejeita informando o motivo.
5. Operação reserva o estoque.
6. Operação atende parte ou toda a quantidade reservada.
7. O sistema baixa o estoque, atualiza o status e registra auditoria.
8. Solicitante acompanha o resultado.

Estados suportados: `draft`, `submitted`, `approved`, `reserved`, `partially_fulfilled`, `fulfilled`, `rejected` e `cancelled`.

## 7. Critérios de aceite do MVP

- Um usuário autenticado vê somente os menus e dados compatíveis com seu perfil.
- Uma solicitação sem itens não pode ser enviada.
- Um aprovador não aprova uma solicitação já atendida, rejeitada ou cancelada.
- Uma rejeição exige motivo e fica registrada.
- Um atendimento parcial atualiza quantidades, estoque e status sem consumir mais do que foi reservado.
- Um cancelamento libera a reserva correspondente.
- A API rejeita saldo reservado maior que o saldo físico.
- O importador executa simulação sem gravar e interrompe a aplicação diante de inconsistência.
- O frontend compila e consegue autenticar, listar catálogo, estoque e solicitações contra a API publicada.
- O ambiente produtivo usa PostgreSQL persistente, segredo configurado e `DEBUG=false`.

## 8. Plano de sprints

Cada sprint considera uma semana de trabalho. A duração pode ser ajustada sem alterar os entregáveis.

### Sprint 0 — Fundação e alinhamento

**Objetivo:** fechar decisões de ambiente, escopo e dados.

Entregas:

- Revisar perfis, departamentos e regras de aprovação com o negócio.
- Confirmar ambiente PostgreSQL e projeto Vercel.
- Obter exportação oficial do legado.
- Definir responsáveis pela aprovação e aceite.

Saída esperada: checklist de homologação e pacote legado versionado fora do repositório, quando contiver dados pessoais.

**Status:** Parcial. Arquitetura e decisões iniciais existem; autenticação Vercel, banco persistente e exportação oficial ainda faltam.

### Sprint 1 — Acesso e autenticação

**Objetivo:** garantir identidade, perfil e escopo de dados.

Entregas:

- Validar matriz de permissões com usuários reais.
- Testar isolamento por usuário/departamento/global.
- Completar mensagens de erro e estados de sessão no frontend.
- Criar massa de usuários de homologação.

**Status:** Base implementada; testes funcionais e homologação pendentes.

### Sprint 2 — Catálogo e estoque

**Objetivo:** disponibilizar catálogo confiável e saldo operacional.

Entregas:

- Completar CRUD/edição de categorias e produtos.
- Adicionar filtros, busca e paginação.
- Completar entradas, ajustes e histórico visual.
- Validar regras de estoque mínimo e concorrência.

**Status:** Base implementada; acabamento de UX, filtros e validação com dados reais pendentes.

### Sprint 3 — Solicitações e aprovações

**Objetivo:** fechar o ciclo pedido-aprovação-atendimento.

Entregas:

- Completar carrinho/formulário de solicitação.
- Criar tela de detalhe com itens e histórico de status.
- Implementar telas de aprovação, rejeição e cancelamento.
- Implementar atendimento parcial por item.
- Testar todos os estados e transições.

**Status:** Regras de domínio implementadas; frontend e aceite ponta a ponta pendentes.

### Sprint 4 — Migração e auditoria

**Objetivo:** carregar dados confiáveis e garantir rastreabilidade.

Entregas:

- Receber e normalizar o export do legado.
- Executar simulação e relatório de divergências.
- Implementar histórico de movimentos, solicitações e auditoria, se aprovado no escopo.
- Conectar tela de auditoria com filtros e paginação.
- Fazer ensaio de migração e reconciliação.

**Status:** Importação base implementada; histórico e tela detalhada pendentes.

### Sprint 5 — Deploy, segurança e go-live

**Objetivo:** publicar uma versão homologada e observável.

Entregas:

- Configurar Vercel, PostgreSQL, variáveis e domínios.
- Executar migrações em preview e produção controlada.
- Configurar `DEBUG=false`, CORS, hosts e segredos.
- Executar testes de regressão e smoke test.
- Publicar runbook de rollback e suporte.
- Fazer carga inicial e obter aceite do negócio.

**Status:** Pendente. O código está no GitHub; deploy ainda aguarda autenticação/configuração da Vercel.

## 9. Métricas de sucesso

- 100% das solicitações com status rastreável.
- 0 aprovações ou baixas fora do escopo autorizado nos testes de segurança.
- 100% das baixas vinculadas a uma solicitação ou referência operacional.
- Divergência de produtos, usuários e saldos explicada antes da carga final.
- Tempo de resposta percebido aceitável nas telas principais, a ser definido após dados reais.
- Primeiro ciclo de solicitação concluído em homologação sem intervenção manual no banco.

## 10. Riscos e dependências

| Risco/dependência | Impacto | Mitigação |
|---|---|---|
| Exportação legada incompleta | Alto | Rodar simulação e relatório antes da carga |
| Permissões não validadas pelo negócio | Alto | Homologar matriz por perfil e departamento |
| SQLite em produção | Alto | Bloquear go-live sem PostgreSQL |
| Deploy sem autenticação Vercel | Alto | Concluir login e configurar projeto/banco |
| Histórico legado sem chave de relacionamento | Médio | Importar primeiro dados mestres; tratar histórico em lote separado |
| Frontend parcial | Médio | Priorizar detalhe de solicitação, auditoria e estados de erro |

## 11. Pendências priorizadas

### Bloqueadoras do go-live

1. Autenticar e configurar o projeto Vercel.
2. Provisionar PostgreSQL persistente.
3. Configurar variáveis de ambiente de produção.
4. Executar migrações e smoke test no ambiente publicado.
5. Validar permissões com usuários reais.
6. Executar importação oficial e reconciliar totais.

### Importantes antes da primeira operação

1. Finalizar formulário/detalhe de solicitações.
2. Conectar auditoria detalhada.
3. Completar filtros e paginação.
4. Criar testes de integração no backend e testes de jornada no frontend.
5. Definir recuperação de senha e suporte operacional.

### Evoluções posteriores

1. Permissões configuráveis por administrador.
2. Notificações automáticas.
3. Importação histórica completa.
4. Relatórios e indicadores de consumo.
5. Aplicativo distribuído/Tauri.
