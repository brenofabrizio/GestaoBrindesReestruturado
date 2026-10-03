# Paridade funcional com o GestaoBrinde original

**Escopo:** comparação do checkout público `brenofabrizio/GestaoBrinde` (commit `857747a199dc73d2e7ab1f0cd872424a59ca46c0`) com `GestaoBrindesReestruturado` (HEAD `b7f58b91d8e4f4098dd49a8d6b1b23a3c3ff9fa4`). Este inventário não declara que os recursos do original estão homologados ou prontos para produção; ele identifica o contrato funcional a portar e a evidência existente.

## Resultado da comparação

A reestruturação ainda não é cópia funcional equivalente. O frontend reconstruído tem seis áreas principais (Dashboard, Catálogo, Estoque, Solicitações internas, TRADE e Auditoria), enquanto o menu do original descreve mais módulos e subfluxos. Uma seção só deverá mudar para **Concluída** depois de existir fluxo persistido de ponta a ponta, autorização no backend e testes automatizados correspondentes.

## Módulos e aceite de paridade

| Grupo/menu original | Regras/fluxo a preservar | Situação verificada na reestruturação | Critério para concluir |
|---|---|---|---|
| Dashboard | Indicadores operacionais agregados e acesso conforme papel | Parcial: existe painel, mas não foi validada equivalência de indicadores | Comparar cada cartão/filtro e autorização com original; testes de agregação |
| Solicitações TRADE | Solicitação por indústria, aprovação conforme regra, reserva e acompanhamento | Parcial: entidade/tela/API separadas para solicitação, aprovação com chamado, recusa motivada, recebimento por linha e retirada QR; falta roteamento por alçada, evento, anexo durável da NF e aceite completo | Completar regras de aprovador, evento/NF persistente e prova; homologar todos os estados |
| Recebimento no CD | Após aprovação/chamado, conferir NF e quantidades por linha; atualizar saldo, movimento e histórico | Parcial: chamada exige aprovação e NF; recebimento parcial/total por linha cria movimento setorial transacional; anexar arquivo NF em storage durável continua ausente | Integrar upload persistente, local do CD, idempotência e aceitar com dados reais |
| Estoque por indústria | A indústria consulta somente dados vinculados à própria indústria | Parcial: `Industry`, vínculo `UserProfile.industry`, endpoint de agregação, filtros de movimentos/cadastro e bloqueio do saldo global; coberto por teste com duas indústrias e smoke local | Cadastro/vínculo disponível para admin; concluir demais registros por indústria, localização, transferências e homologação com dados reais |
| Matriz de acesso do CD | CD recebe/transfer, confirma saídas/retiradas; não abre solicitações nem acessa fila interna de aprovação/separação | Parcial, corrigido nesta etapa: `operator` e `operations` não têm acesso a solicitações internas nem gestão de catálogo; endpoint/menu mantêm separação de aprovação (`requests.approve`) e operação (`requests.process`) | Fechar matriz para os demais módulos/perfis e validar isolamento real por indústria/local; testar por endpoint/menu |
| Transferência | Transferir CD/evento/local altera posições e registra movimentos `−qty/+qty`, sem saída líquida nem alteração do saldo total | Parcial implementado: locais, posições, API/UI de transferência, backfill de saldo existente e bloqueio de unidades reservadas; também bloqueia transferência se a soma das posições divergir do saldo global; sem integração com eventos/cotas/devolução | Completar ligações com eventos, ajuste/estorno e homologar concorrência por origem no PostgreSQL |
| Brindes | Código sequencial `BRD-00001`, categoria, valor, estoque mínimo, local, foto e desativação sem perda de histórico | Parcial: CRUD, categoria, mínimo e ativo existem; faltam semântica de código/local/valor/foto e estoque inicial pelo fluxo original | Portar os campos e regras de ciclo de vida e validar referências/histórico |
| Retirada / QR Code | Validar solicitação/evento e confirmar retirada sem duplicidade | Parcial: saída genérica usa token QR idempotente e o token só é serializado ao solicitante do pedido pendente; TRADE valida o `public_code`, coleta assinatura PNG, baixa por linha e cria protocolo sequencial; `Idempotency-Key` por retirada devolve o protocolo anterior sem repetir baixa em retry; chave reutilizada com payload diferente é recusada; falta QR de eventos e PDF | Fluxo de retirada ligado a pedido/evento com evidência/PDF e auditoria, validado por papel |
| Eventos / Feirões | Cotas por indústria × brinde; abertura reserva saldo; retirada não ultrapassa cota; fechamento libera excedentes; retirada não depende de sucesso de e-mail | Ausente: sem modelos, endpoints ou tela de eventos no frontend reconstruído | Implementar evento, alocações, reserva, retirada, devolução/fechamento e idempotência; validar cotas simultâneas e liberação do restante |
| Comprovantes | Protocolo ligado à retirada, destinatário, itens/quantidades, saldo posterior, QR e assinatura; PDF preserva assinatura e é consultável | Parcial: `TradeDelivery` guarda recebedor, assinatura PNG em base64, itens, saldos e protocolo; a UI apresenta metadados, mas não há endpoint de imagem nem PDF/exportação/consulta por filtros | PDF baixável e verificável com imagem da assinatura, permissões e busca por data/texto |
| Recebimento no CD | Somente após aprovação/chamado; NF e quantidades por linha; saldo/movimento vinculados à solicitação/indústria | Parcial implementado: status e chamado bloqueiam recebimento prévio; NF numérica, recebimento parcial/total por linha e movimentos TRADE/indústria ficam explicitamente no local CD padrão; upload durável da NF e escolha de outro CD não estão implementados | Integrar storage/anexo, local selecionável por recebimento e aceitar com dados reais |
| Solicitações internas | Fluxo próprio separado de TRADE; formulário inclui finalidade, destinatário, departamento, indústria, data necessária, chamado de compra, observações e itens/quantidades/valor; status rascunho → solicitada → aguardando aprovação → aprovada → em separação → pronta → finalizada, além de compra/recebimento; histórico com ator, data e comentário | Parcial e divergente: o formulário (`RequestsPage.tsx`) envia diretamente, sem ação para salvar rascunho; o detalhe não exibe histórico de transições; dados atuais não comprovam equivalência de campos e estados | Implementar rascunho editável, campos/status do original, detalhe/histórico e critérios de compra; testar todos os estados e papéis |
| Aprovações | Fila própria, alçada configurável por prioridade/critério, decisão com ator, quantidade/justificativa e rejeição motivada | Parcial: a lista interna só exibe ações a quem tem `requests.approve`; nenhuma regra configurável/atribuição por alçada está implementada | Criar fila e motor de regras prioritárias; testar aprovação atribuída, limites, rejeição e permissões |
| Separação e entregas | Fila operacional dedicada; iniciar separação → pronta → registrar entrega, baixa e comprovante | Parcial: o backend interno contém ações `requests.process`, mas perfis CD não podem processar a fila interna e não há tela operacional dedicada; TRADE tem protocolo próprio | Criar fila/telas operacionais e reconciliar papéis, baixa e comprovantes com o original |
| Validação do payload de atendimento | Quantidades por item precisam ser números válidos, item pertencente à solicitação, sem duplicatas e limitadas ao reservado/restante | Risco: endpoint constrói mapa diretamente do payload e duplicatas substituem valores; o tratamento de estrutura inválida não foi comprovado | Serializer estrito + teste para formato inválido, item desconhecido/repetido, quantidade não inteira/negativa e atendimento parcial |
| Brindes | Cadastro de produtos/categorias e disponibilidade aplicável | Parcial: existe Catálogo | Comparar campos, vínculos, filtros, estados e permissões do original |
| Livro de movimentações | Histórico consultável e rastreável de entradas/saídas/transferências/ajustes | Parcial: há backend e auditoria; UI e filtros incompletos/sem paridade comprovada | Movimentos imutáveis, filtros/paginação e reconciliação do saldo testados |
| Registrar entrada | Entrada manual com motivo e atualização consistente de saldo/histórico | Parcial: endpoint existe; fluxo visual não demonstrado | Submissão atualiza saldo, movimento e auditoria uma única vez |
| Registrar saída / confirmar saída | O gestor registra uma ordem de saída; o CD vê apenas saídas pendentes e confirma por QR; o débito do saldo acontece uma única vez na confirmação, não no registro | Implementado nesta etapa para saídas genéricas de estoque: ordem reserva saldo; QR UUID é mostrado ao autorizador; CD confirma enviando o token escaneado, não recebe o token na fila; confirmação idempotente baixa uma vez; cancelamento libera reserva | Homologar a jornada visual com leitor QR; vincular a ordem ao destinatário/solicitação/evento e gerar comprovante do processo original |
| Ajuste / estorno | Ajuste justificado e estorno imutável; nenhum movimento histórico deve ser apagado | Parcial: operações backend existem; UI/política original não comprovadas | Permissões, justificativa, saldo e movimentos reversos cobertos por testes |
| Relatórios | Indicadores e relatórios filtráveis/exportáveis por escopo | Ausente | Relatórios reproduzem filtros e totais do original e respeitam escopo de autorização |
| Importar planilha | Validar dados, prévia, erros, duplicatas e só então aplicar | Parcial: há validação/simulação; integração/aplicação controlada pendente | Prévia sem mutação; confirmação aplica atomicamente e gera evidência auditável |
| Cadastros (categorias, departamentos, indústrias, locais, fornecedores) | CRUD e integridade referencial usados pelos demais fluxos | Parcial: `Industry` tem CRUD API e admin pode vincular perfil; não há tela de manutenção nem os demais cadastros | Concluir telas/API restantes, validação, autorização e proteção de referências |
| Usuários | CRUD, ativação e atribuição de perfil | Parcial: perfil pode ser vinculado à indústria por API restrita a admin; não há UI completa de usuários | Administração por papel, validação e auditoria; sem credenciais padrão |
| Perfis e permissões | Menus e endpoints obedecem às permissões do papel | Parcial: existe matriz interna; equivalência a todos os perfis do original não verificada | Matriz de autorização comparada seção a seção e testada no backend e frontend |
| Regras de aprovação | CRUD de regras/alçadas e aplicação determinística | Ausente como administração correspondente | Alterar regra muda fila/transição; testes de alçada e limites |
| Auditoria | Registro consultável de ações críticas | Parcial: existe página/API de auditoria | Cobrir todas as mutações críticas, autoria, instante e filtros com testes |
| Configurações | Parâmetros operacionais do sistema com acesso restrito | Ausente | Configurações persistentes, validadas e auditadas, com permissão administrativa |

## Divergências críticas encontradas

1. **Saída genérica de estoque:** a baixa imediata foi substituída por ordem pendente → QR/token → confirmação idempotente do CD; o débito é único. O fluxo ainda não está vinculado à solicitação/evento e não substitui o comprovante de entrega original.
2. **TRADE e solicitação interna:** agora têm entidade/rota distintas; TRADE cobre chamado, NF numérica, recebimento parcial, retirada QR e protocolo assinado. Faltam alçadas roteadas, upload durável da NF, evento e PDF; o fluxo interno mantém lacunas de rascunho/fila/histórico.
3. **Eventos / cotas:** posições de estoque e transferência entre locais agora existem; não existe ainda módulo de eventos/feirões, cotas indústria×brinde, reserva no fechamento ou devolução.
4. **PDF/comprovante:** retirada TRADE agora grava protocolo com recebedor, assinatura, linhas e saldos pós-retirada; falta reexibir a imagem da assinatura e exportar PDF/consultar protocolos por filtro.
5. **Escopo de acesso:** indústria consulta só a indústria vinculada; saldo global retorna `403` e leituras de movimentos/cadastro/agregado usam o `industry_id` da sessão. Falta escopo por local e separar seu fluxo TRADE.
6. **Solicitações incompletas:** não há rascunho editável na UI, histórico de transições, inbox/alçada configurável ou fluxo dedicado para separar e entregar.

## Plano de entrega por sprint

### Sprint A — contrato e controle de acesso
- [x] Clonar e identificar o código de referência e o commit comparado.
- [x] Mapear módulos declarados no menu original contra rotas/telas reconstruídas.
- [ ] Validar a matriz oficial completa de papéis/permissões para cada módulo com o original e o negócio; nesta etapa foram corrigidos/testados solicitante, aprovador, CD e escopo de indústria, sem cobrir toda a matriz.
- [x] Restringir fila interna de solicitações no backend, menu e rota para o CD; cobrir autorizações selecionadas com testes de API e helper frontend.

### Sprint B — TRADE e solicitações internas
- [x] Criar entidade/rota/tela TRADE separadas, com indústria, itens, código público e histórico.
- [x] Aprovar com chamado, rejeitar com motivo, receber parcial/total por NF numérica e registrar retirada QR com assinatura/protocolo.
- [ ] Implementar roteamento de aprovação configurável e vínculo com eventos; validar regra com o negócio.
- [ ] Integrar anexo NF durável, PDF/protocolo baixável e completar solicitação interna (rascunho, edição, filas e histórico completo).

### Sprint C — estoque e operação do CD
- [x] Implementar posições por local, backfill do saldo global para o CD padrão e transferência atômica por indústria com ledger `−qty/+qty` sem alterar o total.
- [x] Proteger posições de saídas já reservadas; cobrir saldo insuficiente, saldo global inalterado e reservas preservadas por teste.
- [x] Implementar ordem de saída genérica com reserva, QR/token, confirmação idempotente e cancelamento.
- [ ] Concluir ajuste/estorno na UI, recebimento com arquivo NF persistente, devoluções/eventos e paginação do livro.
- [ ] Testar contenção concorrente no PostgreSQL; SQLite local não prova locks concorrentes.

### Sprint D — eventos e comprovantes
- [ ] Implementar eventos/feirões, cotas por indústria/item, abertura, reserva, retirada e fechamento.
- [x] Criar protocolo TRADE ligado à solicitação/baixa, recebedor, itens, assinatura PNG e saldo após retirada.
- [ ] Gerar PDF baixável/verificável e tela de consulta por data/texto; estender comprovante a outros fluxos.

### Sprint E — cadastros, relatórios e administração
- [x] Criar entidade/API de indústria e atribuição administrativa ao perfil.
- [x] Criar locais/posições e gestão admin básica de locais; transferência aparece na UI.
- [ ] Completar telas/API de categorias/departamentos/fornecedores, usuário/perfis e regras de aprovação.

### Sprint F — homologação de paridade
- [x] Suíte local completa: 50 testes Django, 10 testes Node, build, Django checks e migrations sem drift; browser smoke em SQLite para criação/aprovação/recebimento/retirada TRADE, perfil indústria e transferência CD→evento.
- [ ] Walkthrough dos perfis/jornadas ainda não exercidos e aceite comparativo módulo a módulo.
- [ ] Validar transações em PostgreSQL e smoke no ambiente publicado, quando autorizado/configurado.

## Bloqueios e limites atuais

- O original no GitHub tem uma aplicação PHP e também um backend Laravel experimental. A documentação/código do backend não deve ser confundida com prova de que todos os módulos estão integrados e operacionais na aplicação principal.
- Composer/PHP não estão disponíveis para executar os testes do backend Laravel nesta sessão; por isso os testes do original não foram usados como prova de runtime.
- O `.venv` local e o executável Ruff são bloqueados pelo Controle de Aplicativo; sem contornar a política, a suíte rodou no Python disponível com dependências temporárias: 50 testes Django passaram. Dez testes Node e o build passaram; Ruff sem execução.
- Smoke visual em SQLite temporário cobriu indústria→aprovador→CD (recebimento parcial/total, QR/code, canvas de assinatura, protocolo sequencial), transferências CD→evento e saldo por posição; QR/assinatura foram simulados por automação de browser, sem leitor físico ou caneta real.
- Ainda não há validação PostgreSQL, eventos/cotas, PDF de protocolo, upload durável da NF, todos os perfis/jornadas ou smoke de produção.
- O deploy Vercel e dados de produção não foram acessados. Nenhuma mutação de produção foi executada.
- Este inventário não declara paridade total. Permanecem pendentes a validação PostgreSQL, jornadas completas, módulos ausentes e smoke de produção.

## Referências internas do repositório original

- `app/Support/Menu.php`, `app/pages.php`, `app/routes.php` — menu, páginas, APIs e permissões.
- `docs/Manual-do-Usuario.md`, `docs/Mapa-de-Modulos.md` e `docs/Perfis-e-Permissoes.md` — regras funcionais e papéis.
- `app/Services/RequestWorkflow.php`, `RequestService.php` e `ApprovalEngine.php` — estados, histórico, alçadas e decisões.
- `app/Services/TradeService.php`, `StockService.php`, `EventService.php` e `DeliveryService.php` — TRADE, estoque, eventos e comprovantes.
- `docs/api-contract.md` — contrato detalhado de operações/API.
- `docs/Plano-Sprints-Reestruturacao-Laravel.md` e `docs/TRD-Reestruturacao-Laravel.md` — plano/arquitetura da reestruturação descrita no próprio projeto original.
