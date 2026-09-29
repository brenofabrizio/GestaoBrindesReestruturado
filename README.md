# Gestão Brindes — API

Fundação do backend do sistema Gestão Brindes, organizada como um monólito modular Django.

## Requisitos

- Python 3.13+ no runtime de deploy
- PostgreSQL 16+ para ambientes persistentes

No deploy Vercel, configure `DATABASE_URL` com o PostgreSQL provisionado pela Vercel/Neon.
Sem `DATABASE_URL` ou `POSTGRES_HOST`, o projeto usa SQLite apenas como fallback local.

## Deploy na Vercel

O projeto contém `manage.py` e é reconhecido pela integração Django da Vercel. O runtime
Python é provisionado pela própria Vercel; não é necessário instalar Python ou Docker na
máquina para publicar via Git. Configure pelo menos `DJANGO_SECRET_KEY`, `DATABASE_URL` e
`DJANGO_ALLOWED_HOSTS`. As migrações são executadas no build por meio de
`[tool.vercel.scripts]`.

O banco precisa ser externo e persistente. Não use SQLite em produção, pois o filesystem
do ambiente serverless não deve ser tratado como armazenamento permanente.

Para deploys de preview, use uma branch/banco separado no provedor PostgreSQL. Como o build
executa migrações, apontar previews diretamente para o banco de produção pode aplicar uma
migração antes da publicação oficial.

Em produção, a aplicação falha ao iniciar se faltar segredo forte, PostgreSQL persistente,
hosts concretos ou origens CORS/CSRF explícitas. Confira as variáveis, smoke tests, migração
e dependências externas em [`docs/GO-LIVE.md`](docs/GO-LIVE.md) antes de publicar.

## Desenvolvimento local

```powershell
py -3.13 -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Endpoints iniciais:

- `GET /api/v1/health/`
- `POST /api/v1/auth/token/`
- `POST /api/v1/auth/token/refresh/`
- `GET /api/v1/auth/me/`
- `GET|POST /api/v1/catalog/categories/`
- `GET|POST /api/v1/catalog/products/`
- `GET /api/v1/inventory/balances/`
- `GET|POST /api/v1/inventory/movements/`
- `GET|POST /api/v1/orders/requests/`
- `POST /api/v1/orders/requests/{id}/submit/`
- `POST /api/v1/orders/requests/{id}/approve/`
- `POST /api/v1/orders/requests/{id}/reserve/`
- `POST /api/v1/orders/requests/{id}/fulfill/`
- `GET /api/v1/audit/events/` (operadores)

O frontend está em `frontend/` e pode ser publicado como um projeto Vercel separado
com Root Directory `frontend`. Ele usa `VITE_API_BASE_URL` para apontar para esta API.
- `GET /api/docs/`
- `GET /api/schema/`

## Organização

- `config/`: configuração do projeto Django.
- `apps/core/`: recursos transversais e health check.
- `apps/accounts/`: usuários, autenticação e perfis.
- `docs/`: decisões e arquitetura.

Os próximos módulos serão adicionados sem transformar o projeto em microserviços: catálogo, estoque, solicitações e auditoria permanecem dentro do mesmo deploy e banco transacional.
