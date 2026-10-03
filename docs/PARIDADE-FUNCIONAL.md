# Paridade funcional

A matriz canônica de funcionalidades, evidências, lacunas e sprints está em [FEATURE-PARITY.md](FEATURE-PARITY.md). Este arquivo é mantido apenas como atalho para referências que ainda usam o nome antigo.

A aplicação ativa usa o frontend React conectado à API Django; PostgreSQL é a fonte de verdade pretendida para ambientes persistentes. O antigo modo `seed.json`/`localStorage` não é carregado pelo frontend atual e seus dados não são enviados automaticamente ao banco. Preserve/exporte dados locais antes de qualquer limpeza e valide a transformação antes de importar.

Paridade total e go-live não estão concluídos. PostgreSQL concorrente, homologação integral, módulos pendentes e smoke do ambiente publicado continuam em aberto.
