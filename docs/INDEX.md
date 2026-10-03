# Índice da documentação

## Produto, requisitos e paridade

- [PRD](PRD.md) — requisitos e status dos sprints de produto.
- [TRD](TRD.md) — arquitetura, API, dados, segurança e infraestrutura.
- [Paridade funcional com GestaoBrinde](FEATURE-PARITY.md) — comparação por módulo, divergências, critérios de aceite e sprints restantes.

## Operação e implantação

- [Go-live e homologação](GO-LIVE.md) — checklist, evidências locais e bloqueios de ambiente.
- [Arquitetura](architecture.md) — visão geral técnica.

## Estado da paridade

O sistema **ainda não é funcionalmente equivalente** ao original. Há fatias parciais verificadas: QR genérico em duas etapas, estoque por indústria/local, transferências, e TRADE até retirada assinada. Continuam pendentes eventos/cotas, anexo durável da NF, PDF/protocolo baixável, paridade completa de solicitações internas/filas/alçadas, relatórios/administração e homologação PostgreSQL/produção; veja `FEATURE-PARITY.md`.
