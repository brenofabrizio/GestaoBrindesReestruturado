# Gestão Brindes Web

Frontend React + TypeScript com modo local funcional para uso sem banco de dados.

## Modo atual: JSON + localStorage

Por enquanto, o sistema roda sem PostgreSQL e sem API Django:

- `src/data/seed.json` contém os dados iniciais de usuários, catálogo, estoque e solicitações.
- `localStorage` mantém sessão, novos produtos, movimentações, solicitações e auditoria no navegador.
- As regras de aprovação, reserva, atendimento parcial e cancelamento são executadas no frontend.
- Cada navegador possui sua própria cópia dos dados; isso não substitui um banco compartilhado.

Contas temporárias de demonstração:

| Perfil | E-mail | Senha |
|---|---|---|
| Administrador | `admin@gestaobrindes.com` | `GBr!29vQ#x7Lm2ZaP` |
| Solicitante | `solicitante@gestaobrindes.com` | `Solicitante#2026` |
| Operador | `operador@gestaobrindes.com` | `Operador#2026` |

Essas credenciais são apenas para o modo local/demonstração. Não devem ser usadas como autenticação de produção.

## Executar

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Por padrão, a aplicação usa `/api/v1` no mesmo domínio. Para desenvolvimento
separado, defina `VITE_API_BASE_URL` apontando para a API publicada.

## Deploy

O diretório pode ser publicado como um projeto Vercel com Root Directory `frontend`.
No estado atual, não é necessário configurar `VITE_API_BASE_URL`: o build usa os dados
locais. Quando o backend voltar a ser usado, será necessário trocar o adaptador de dados
em `src/lib/api.ts` e configurar a URL da API, além de migrar o conteúdo do localStorage.

## Limpar a base local

Para começar novamente com o `seed.json`, abra o console do navegador e execute:

```js
localStorage.removeItem("gestao_brindes_json_database_v1");
localStorage.removeItem("gestao_brindes_local_access");
location.reload();
```
