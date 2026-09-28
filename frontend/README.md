# Gestão Brindes Web

Frontend React + TypeScript para o backend Django do projeto.

## Executar

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Por padrão, a aplicação usa `/api/v1` no mesmo domínio. Para desenvolvimento
separado, defina `VITE_API_BASE_URL` apontando para a API publicada.

## Deploy

O diretório pode ser criado como um projeto separado na Vercel com Root Directory
`frontend`. O backend Django deve permanecer em um projeto Vercel próprio ou ser
exposto pelo mesmo domínio conforme a configuração de roteamento escolhida.

