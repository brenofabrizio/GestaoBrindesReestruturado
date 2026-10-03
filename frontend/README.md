# Gestão Brindes Web

Frontend React + TypeScript conectado à API Django. O PostgreSQL configurado no backend é a fonte de verdade dos dados operacionais.

## Executar localmente

1. Configure e inicie a API Django em `http://127.0.0.1:8000` conforme o README da raiz.
2. Na pasta `frontend/`:

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

O proxy Vite encaminha `/api/*` para Django. Para apontar a um backend em outro host, defina `VITE_API_BASE_URL` com a URL base terminada em `/api/v1`.

## Deploy

Publique este diretório como projeto frontend separado, com Root Directory `frontend`, e configure `VITE_API_BASE_URL` para a API do ambiente correspondente. Preview e produção devem usar bancos distintos.

## Migração dos dados do modo local legado

Versões anteriores guardavam dados e credenciais de demonstração em `seed.json` e no `localStorage` de cada navegador. O frontend atual não lê nem sincroniza esse armazenamento; os dados locais existentes não são enviados automaticamente ao PostgreSQL. Preserve-os antes de limpar os dados do navegador e faça a migração apenas por um processo de exportação/transformação aprovado. O importador do backend aceita o formato documentado de carga legada, não promete importar diretamente o formato interno do `localStorage`.

Contas para desenvolvimento devem ser provisionadas no backend por canal local seguro. Não há senhas padrão ou credenciais de demonstração publicadas no frontend.
