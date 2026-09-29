# Contas iniciais

O projeto possui o comando `provision_initial_accounts` para criar as contas dos cinco perfis funcionais. Ele é idempotente: contas existentes são ativadas e têm o perfil/departamento atualizado, mas a senha existente não é sobrescrita por padrão.

As senhas não ficam no código, no GitHub, no `.env` versionado ou no frontend. A execução deve acontecer somente contra o banco correto, preferencialmente usando a `DATABASE_URL` de produção em uma sessão segura.

## Contas padrão

| E-mail | Perfil | Departamento |
|---|---|---|
| `admin@gestaobrindes.com` | Administrador | Administração |
| `aprovador@gestaobrindes.com` | Aprovador | Administração |
| `operador@gestaobrindes.com` | Operador de estoque | Operações |
| `solicitante@gestaobrindes.com` | Solicitante | Comercial |
| `industria@gestaobrindes.com` | Indústria | Indústria |

As senhas são geradas aleatoriamente com 24 caracteres quando a conta é criada. Elas só aparecem se a execução usar `--show-passwords` ou `--credentials-file`.

## Execução segura

Primeiro, valide sem alterar:

```powershell
python manage.py provision_initial_accounts
```

Depois, aplique no banco correto e salve o resultado em um arquivo ignorado pelo Git:

```powershell
python manage.py provision_initial_accounts --apply --show-passwords --credentials-file initial.credentials.json
```

Para trocar as senhas das contas existentes:

```powershell
python manage.py provision_initial_accounts --apply --reset-passwords --show-passwords --credentials-file initial.credentials.json
```

O arquivo de credenciais deve ser entregue por canal seguro e removido após o armazenamento no gerenciador de senhas. O padrão `*.credentials.json` já está no `.gitignore`, mas isso não substitui a conferência de `git status`.

## Banco da Vercel

O comando precisa ser executado com `DATABASE_URL` apontando para o PostgreSQL do ambiente publicado. Não execute com SQLite local esperando alterar a Vercel. Após a execução, valide:

1. Login de cada perfil.
2. `GET /api/v1/auth/me/` com o token de cada conta.
3. Visibilidade por departamento e por usuário.
4. Ações permitidas para cada papel.
5. Troca das senhas iniciais, quando aplicável.

Se a plataforma não oferecer shell para executar comandos Django, use um ambiente de administração controlado com a mesma `DATABASE_URL`; não crie um endpoint público de bootstrap de usuários.
