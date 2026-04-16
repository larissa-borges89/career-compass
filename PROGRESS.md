# Career Compass — Progress Tracker

## Projeto
AI-powered job tracker como portfólio para busca de emprego em NYC.
**Dev:** Larissa Borges (Senior Software Engineer)
**Stack:** React + Material UI (frontend) | FastAPI + SQLAlchemy + SQLite (backend)

---

## ✅ Concluído

### Arquitetura geral
- Estrutura de pastas: `frontend/`, `api/`, `src/`, `tests/`
- Ambiente virtual Python (`venv`)
- `.env` com variáveis: `API_KEY`, `MOCK_APIS`, `ANTHROPIC_API_KEY`, `REACT_APP_API_URL`, `REACT_APP_API_KEY`
- `python-dotenv` instalado; `load_dotenv()` no topo do `api_server.py`

### Backend (FastAPI)
- `api_server.py` — servidor principal com:
  - `load_dotenv()` para ler `.env` automaticamente
  - Middleware de autenticação via `X-API-Key` header (pula OPTIONS para CORS)
  - Middleware de logging de requests
  - `Base.metadata.create_all()` no startup
- `api/database.py` — SQLAlchemy 2.0 com `DeclarativeBase`
- `api/models.py` — modelos `Application` e `JobListing`
- `api/routes.py` — todos os endpoints REST:
  - `GET/POST /api/applications`
  - `PATCH /api/applications/{id}`
  - `DELETE /api/applications/{id}`
  - `GET /api/jobs`
  - `POST /api/jobs/search` — com MOCK_MODE + real APIs comentadas
  - `POST /api/jobs/{id}/apply` — com deduplicação por company+role
  - `POST /api/resume/upload`
  - `GET /api/resume/profile`
  - `GET /api/usage`
  - `POST /api/gmail/sync` — com MOCK_MODE
  - `GET /api/stats`
  - `GET /health`

### Fontes externas (src/)
- `src/resume_parser.py` — parse de PDF/DOCX com cache por hash
- `src/job_matcher.py` — match de vagas com Claude AI + `generate_search_keywords`
- `src/job_search.py` — busca via Adzuna e SerpAPI + `filter_ghost_jobs` (48h)
- `src/gmail_api.py` — estrutura criada (OAuth ainda não implementado)
- `src/logger.py` — `get_logger(name)` com formato `timestamp | LEVEL | module | message`
- `src/rate_limiter.py` — limites: Claude 50/dia, Adzuna 250/dia, SerpAPI 100/mês; persistido em `data/api_usage.json`
- `src/mock_data.py` — dados mock para desenvolvimento sem consumir API:
  - `MOCK_JOBS` (5 vagas .NET/Angular/React NYC)
  - `MOCK_MATCH_RESULTS` (scores 74–91)
  - `MOCK_KEYWORDS` (5 keywords)
  - `MOCK_EMAIL_CLASSIFICATIONS` (3 emails: applied, interview, rejected)

### Frontend (React + Material UI)
- `frontend/src/App.js` — ThemeProvider, NotificationProvider, BrowserRouter, Routes
- `frontend/src/components/Navbar.jsx` — navbar responsiva com drawer mobile; botões com `variant="outlined"` para visibilidade
- `frontend/src/pages/Dashboard.jsx` — stats cards, grid de applications com filtro por status, botão "Sync Gmail", botão "Apply Now" com URL
- `frontend/src/pages/Jobs.jsx` — busca com location/maxDays/minScore, `savedIds` como Set para estado persistente entre buscas, deduplicação por company+role
- `frontend/src/pages/Resume.jsx` — upload drag-and-drop, exibição de perfil parseado
- `frontend/src/services/api.js` — Axios com baseURL do `.env`, header `X-API-Key`, timeout 120s, interceptor de erros com `friendlyMessage`, `syncGmail()` exportado
- `frontend/src/context/NotificationContext.jsx` — Context API com `notify/success/error/warning/info`, MUI Snackbar

### Testes (27 passing)
- `tests/conftest.py` — StaticPool in-memory SQLite, override de `get_db()`, cria tabelas por sessão
- `tests/test_api_routes.py` — 10 testes de integração
- `tests/test_auth.py` — 5 testes de autenticação com monkeypatch
- `tests/test_rate_limiter.py` — 8 testes unitários
- `pytest.ini` — `testpaths=tests`, `asyncio_mode=auto`

### Mock Mode
- `MOCK_APIS=true` no `.env` → retorna dados mock, zero chamadas de API
- `MOCK_APIS=false` → retorna erro 503 (real APIs temporariamente desabilitadas)
- Validado end-to-end: Job Search → Add to Tracker → Dashboard → Sync Gmail

### Bugs corrigidos
- Navbar mostrando só 1 botão → `variant="outlined"` nos botões inativos
- ADD TO TRACKER duplicando → deduplicação por company+role no backend
- Status "applied" incorreto ao salvar → corrigido para "saved"
- Scroll para o topo ao clicar ADD TO TRACKER → removido callback `loadJobs()`
- `savedIds` resetando a cada busca → movido para o componente pai como Set
- Testes poluindo banco de produção → `StaticPool` in-memory no `conftest.py`
- `no such table` em produção → `create_all()` no startup do `api_server.py`
- `declarative_base()` deprecated → atualizado para `class Base(DeclarativeBase)`
- `app.dict()` deprecated → atualizado para `app.model_dump()`
- 401 em requisições OPTIONS → middleware agora pula `request.method == "OPTIONS"`
- Mock jobs sem `id` → endpoint retorna jobs do banco (com IDs reais) após upsert
- `load_dotenv()` não chamado → adicionado no topo do `api_server.py`
- SerpAPI rate limit era diário → corrigido para mensal (`%Y-%m`)

---

## 🔄 Em andamento

### 1. Gmail OAuth real
- Google Cloud Console: projeto criado, Gmail API habilitada, `credentials.json` gerado ✅
- Falta: implementar OAuth flow em `src/gmail_api.py`, endpoint de autenticação, leitura + classificação de emails reais

---

## 📋 Backlog

### Próximas 4 tarefas (em ordem)
1. **Gmail OAuth real** — autenticação Google + leitura de emails reais com Claude
2. **Live search status** — progresso em tempo real via Server-Sent Events
3. **Resume tailoring** — Claude sugere adaptações do currículo por vaga
4. **Migrar api_usage.json para SQLite**

### Backlog adicional
- Documentação: atualizar vision doc com decisões arquiteturais
- Persistência de dados de uso de API em SQLite (no lugar de JSON)
- Testes para mock mode e Gmail sync
- Deploy (Heroku / Railway / Render)

---

## 🐛 Known Issues / Tech Debt

### Gmail sync
- **`increment("claude")` é chamado em MOCK mode** (`api/routes.py:411`) — dentro do loop de `/gmail/sync`, `increment("claude")` roda mesmo quando `MOCK_APIS=true`, inflando o contador em `data/api_usage.json`. Fix: mover pra dentro do bloco não-mock (ou pular quando `MOCK_MODE` é True).
- **`STATUS_RANK` trata "rejected" como "applied"** (`api/routes.py:397`) — `{"applied": 1, "rejected": 1}`. Isso impede que uma aplicação já marcada como "applied" seja atualizada pra "rejected" quando chega o email de rejeição. Precisa de lógica separada: rejeição deve sempre sobrescrever (exceto `offer`), independentemente do rank.

### Middleware / Auth
- **Callback OAuth precisava pular auth** — corrigido em `api_server.py:51` via whitelist de `public_paths`. Commitar junto.

---

## 📁 Caminhos importantes
```
/Users/larissaborges/Projects/career-compass/
├── api_server.py
├── .env                          ← API_KEY, MOCK_APIS, ANTHROPIC_API_KEY
├── resume.pdf                    ← currículo atual
├── credentials.json              ← Google Cloud (já existe)
├── token.json                    ← gerado após OAuth (ainda não existe)
├── api/
│   ├── database.py
│   ├── models.py
│   └── routes.py
├── src/
│   ├── resume_parser.py
│   ├── job_matcher.py
│   ├── job_search.py
│   ├── gmail_api.py
│   ├── logger.py
│   ├── rate_limiter.py
│   └── mock_data.py
├── frontend/
│   └── src/
│       ├── App.js
│       ├── components/Navbar.jsx
│       ├── pages/Dashboard.jsx
│       ├── pages/Jobs.jsx
│       ├── pages/Resume.jsx
│       ├── services/api.js
│       └── context/NotificationContext.jsx
├── tests/
│   ├── conftest.py
│   ├── test_api_routes.py
│   ├── test_auth.py
│   └── test_rate_limiter.py
└── data/
    └── api_usage.json
```
