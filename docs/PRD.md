# PRD — Gestão de Brindes

**Versão:** 1.1
**Data:** 29/09/2026
**Status:** Fluxos principais implementados no código; homologação e configuração de produção pendentes. O usuário informa que publicou na Vercel, mas o deploy não foi verificado neste trabalho.

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

**Status:** API e tela de produtos implementam listagem, criação, edição e desativação/reativação lógica, com busca e filtros por categoria/status. Ainda faltam paginação, validação de categorias pela interface e aceite com usuários/dados reais.

### RF-04 — Estoque

- Exibir quantidade física, reservada e disponível.
- Registrar entrada, saída e ajuste.
- Bloquear saldo disponível negativo.
- Manter movimentação vinculada ao usuário, produto, referência e observação.
- Reservar itens durante o processamento de uma solicitação.

**Status:** Saldos, movimentações e regras transacionais estão implementados; a interface permite consultar saldos/movimentações e registrar entrada conforme permissão. Faltam homologar ajustes/saídas e concorrência com PostgreSQL, filtros do histórico e confirmar se transferência entre locais pertence ao escopo.

### RF-05 — Solicitações

- Criar rascunho com um ou mais produtos.
- Enviar solicitação com justificativa.
- Aprovar ou rejeitar com motivo.
- Reservar estoque de solicitações aprovadas.
- Atender parcialmente ou totalmente.
- Cancelar solicitação elegível e liberar reservas.
- Exibir histórico/status ao solicitante.

**Status:** Backend e interface implementam solicitação com múltiplos itens, envio, aprovação, rejeição com motivo, reserva, atendimento parcial por item e cancelamento. Falta executar jornada ponta a ponta em ambiente de homologação e validar a matriz de acesso com os responsáveis do negócio.

### RF-06 — Auditoria

- Registrar ações relevantes com ator, entidade, data, metadados e request id quando disponível.
- Permitir consulta restrita a perfis autorizados.
- Filtrar por período, usuário, entidade e ação.

**Status:** Registro no backend, endpoint protegido com filtros/paginação e tela conectada estão implementados. Falta validar visibilidade e conteúdo dos eventos com perfis autorizados e definir retenção operacional.

### RF-07 — Migração

- Ler pacote exportado do legado sem escrita na origem.
- Validar campos obrigatórios, duplicidades, perfis e saldos.
- Executar simulação antes da aplicação.
- Aplicar em transação única somente após conferência.
- Comparar totais antes/depois.

**Status:** Importador oferece validação/simulação e aplicação transacional para usuários, perfis, departamentos, categorias, produtos e saldos. Falta receber o pacote oficial, aprovar o mapeamento, fazer ensaio e reconciliar a carga. Histórico legado de movimentações/solicitações/auditoria não está implementado e só deve entrar mediante aprovação de escopo.

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

Feito no repositório:

- Definição inicial da arquitetura, perfis, riscos, plano e checklist de go-live.

Falta:

- Negócio confirmar perfis/departamentos e regras de aprovação.
- Confirmar projetos/domínios/runtime Vercel e provisionar banco persistente.
- Obter export oficial do legado e definir responsáveis pelo aceite.

Saída esperada: checklist de homologação e pacote legado versionado fora do repositório, quando contiver dados pessoais.

**Status:** Parcial. Arquitetura e documentação estão definidas. O usuário informa deploy na Vercel, sem verificação independente. Ainda faltam confirmar os projetos/domínios e o runtime da API, decidir/provisionar persistência durável (recomendação: PostgreSQL; JSON gravado no filesystem da função não é fonte de dados de produção), obter export oficial e nomear aprovadores do aceite.

### Sprint 1 — Acesso e autenticação

**Objetivo:** garantir identidade, perfil e escopo de dados.

Feito no repositório:

- Login JWT, perfil e permissões por papel; menu/rota de solicitações ocultos para o CD; testes automatizados cobrem casos de solicitante, aprovador e operador.
- O perfil indústria tem vínculo por `industry_id`; saldo global é negado. Posições locais e transferências físicas são restritas a CD/admin; leituras setoriais usam movimentos/agregados da sessão. Ainda faltam escopo setorial em eventos e homologação completa.

Falta:

- Homologar matriz e isolamento com usuários reais, criar contas de teste e definir recuperação de senha/política de sessão.

**Status:** Parcial. Os gates locais de regressão passaram (testes de perfis incluídos), mas equivalência completa da matriz, escopo por indústria e validação com usuários/ambiente real continuam pendentes.

### Sprint 2 — Catálogo e estoque

**Objetivo:** disponibilizar catálogo confiável e saldo operacional.

Feito no repositório:

- API e tela para listar/criar/editar/desativar produtos; busca e filtros por texto/categoria/status.
- Backend com saldos, entradas/ajustes e ordens de saída em duas etapas: reserva ao autorizar, baixa única após QR do CD; cancelamento pendente libera a reserva. A tela registra entrada, autoriza/cancela saída, exibe QR ao autorizador e confirma com token lido pelo CD.

Falta:

- Completar campos do catálogo de brindes, código sequencial/foto/valor e manutenção de categorias.
- Integrar eventos/cotas e ajustes/estornos na UI; executar concorrência em PostgreSQL e aceitar transferências com dados reais.

**Status:** Parcial: saldo por indústria/local e transferência `−qty/+qty` estão implementados; saída genérica é bifásica; TRADE cobre compra/chamado, recebimento parcial por NF numérica, retirada QR e protocolo assinado. Faltam anexo durável da NF, PDF, eventos, ajustes UI, catálogo completo, PostgreSQL e aceite operacional. Ver `FEATURE-PARITY.md`.

### Sprint 3 — Solicitações e aprovações

**Objetivo:** fechar o ciclo pedido-aprovação-atendimento.

Feito no repositório:

- Formulário/carrinho com múltiplos itens, listagem, busca, filtros, detalhe expandido e ações de enviar, aprovar, rejeitar, reservar, atender parcialmente e cancelar.
- Regras de domínio transacionais e registro de auditoria nas transições.

Falta:

- Testar a jornada completa no ambiente publicado com perfis reais, automatizar testes de jornada e obter aceite das regras operacionais.

**Status:** Parcial. O TRADE agora tem fluxo separado de criação/aprovação/recebimento/retirada assinada; solicitações internas ainda não têm rascunho editável, histórico completo, fila/alçada configurável nem paridade com o original. Eventos/PDF e ambiente PostgreSQL/produção não homologados. Ver `FEATURE-PARITY.md`.

### Sprint 4 — Migração e auditoria

**Objetivo:** carregar dados confiáveis e garantir rastreabilidade.

Feito no repositório:

- Importador de mestres/saldos com validação, simulação e aplicação transacional controlada.
- Auditoria consultável por filtros/paginação, com tela conectada.

Falta:

- Receber o pacote oficial, simular, revisar divergências e reconciliar após aprovação.
- Importação histórica não está implementada; decidir escopo antes de planejá-la.

**Status:** Importador de dados mestres/saldos e consulta de auditoria filtrada/paginada estão implementados. Pendente pacote oficial, simulação e reconciliação aprovadas; importação histórica adicional não faz parte do release confirmado.

### Sprint 5 — Deploy, segurança e go-live

**Objetivo:** publicar uma versão homologada e observável.

Feito no repositório:

- Configuração de produção, CI backend/frontend e documentação de go-live/rollback.
- Verificações locais e checks remotos do commit `b7f58b9` registrados.

Falta:

- O usuário relata deploy na Vercel; validar URL, runtime, banco, variáveis e migrações sem presumir que estejam corretos.
- Executar smoke/regressão no ambiente real, confirmar backups/restore, rollback, monitoramento, carga inicial e aceite.

**Status:** Código, CI e verificações locais estão implementados. O usuário relata publicação na Vercel, não verificada independentemente. Pendente validar ambiente publicado, banco persistente, variáveis, migrações, CORS/domínio, smoke test, backups/restore, rollback, monitoramento e aceite. Não há persistência JSON local implementada; não usar arquivo local de função Vercel como fonte oficial.

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
| Projeto/runtime/banco Vercel não verificados | Alto | Confirmar configuração real e validar persistência/fluxos antes do go-live |
| Histórico legado sem chave de relacionamento | Médio | Importar primeiro dados mestres; tratar histórico em lote separado |
| Homologação/UX operacional pendente | Médio | Testar jornadas, erros, paginação e filtros com usuários reais |

## 11. Pendências priorizadas

### Bloqueadoras do go-live

1. Confirmar URL/projetos Vercel e validar o deploy real.
2. Confirmar/provisionar armazenamento persistente; recomendação atual é PostgreSQL externo. Não gravar JSON no filesystem efêmero da função.
3. Revisar variáveis, hosts, CORS/CSRF e separação de preview/produção.
4. Executar migrações e smoke test no ambiente publicado.
5. Validar permissões e fluxos com usuários reais.
6. Executar importação oficial somente após aprovação e reconciliar totais.

### Importantes antes da primeira operação

1. Completar paginação do catálogo e filtros operacionais do histórico de estoque.
2. Automatizar testes de jornada no frontend e testar as transações críticas contra PostgreSQL.
3. Definir recuperação de senha, retenção de auditoria e suporte operacional.

### Evoluções posteriores

1. Permissões configuráveis por administrador.
2. Notificações automáticas.
3. Importação histórica completa.
4. Relatórios e indicadores de consumo.
5. Aplicativo distribuído/Tauri.

## 12. Requisitos de VM para execução do projeto

Os tamanhos abaixo são recomendações iniciais para uma instalação pequena, não substituem medição de carga. O sistema usa Django 5.2/Python 3.13, PostgreSQL 16 e React/Vite; a interface pode continuar hospedada na Vercel e consumir a API na VM.

| Perfil | CPU | Memória | Disco persistente | Uso |
|---|---:|---:|---:|---|
| Desenvolvimento/homologação | 2 vCPU | 4 GB RAM | 40 GB SSD | API, banco de teste, build e testes; não usar como produção |
| Produção inicial pequena (recomendado) | 4 vCPU | 8 GB RAM | 100 GB SSD/NVMe | API e serviços operacionais; preferir PostgreSQL gerenciado ou em host separado |
| Produção tudo-em-um (contingência/piloto) | 4 vCPU | 8 GB RAM | 150 GB SSD/NVMe | API + PostgreSQL na mesma VM; ponto único de falha e exige backup externo rigoroso |

Requisitos de sistema e operação:

- Ubuntu Server 24.04 LTS x86_64 atualizado; Python 3.13 para API, PostgreSQL 16 e Node.js 22 apenas para build do frontend.
- Servidor WSGI (Gunicorn) e proxy reverso (Nginx ou Caddy) com TLS válido. A dependência/serviço WSGI ainda precisa ser incluída e validada antes de um deploy Django em VM.
- Disco de banco/dados persistente e monitorado; backup criptografado fora da VM, diário, com retenção acordada e teste periódico de restauração. Definir RPO/RTO antes do go-live.
- Firewall público apenas para SSH restrito por IP e HTTPS (443); HTTP (80) apenas para redirecionamento/ACME. PostgreSQL (5432) não deve ficar exposto à internet.
- Segredos em variáveis/secret manager, acesso administrativo individual, atualizações de segurança, logs/alertas de espaço, CPU, memória e disponibilidade.
- Banco de produção separado de desenvolvimento/preview. Não usar arquivo JSON no filesystem da função Vercel como persistência; caso JSON seja requisito, manter apenas como formato de importação/exportação ou usar serviço externo durável com controle de concorrência.

O dimensionamento final depende do número de usuários simultâneos, tamanho do histórico e política de retenção. Reavaliar após teste de carga e crescimento medido.
