# SecureCode AI - Architecture

## 1) High-Level Request Flow

1. User logs in or signs up using Firebase Authentication (frontend).
2. Frontend retrieves Firebase ID token and sends it in `Authorization: Bearer <token>`.
3. FastAPI auth middleware verifies token with Firebase Admin SDK.
4. Authenticated user starts scan:
   - `POST /scan/upload` or `POST /scan/github`
5. Backend applies rate limiting and queues background scan job.
6. Scanner runs static-only analysis (no code execution).
7. Result is persisted in in-memory status + JSON history store (per user).
8. Frontend polls scan status and renders dashboard/results.
9. User exports JSON or generates PDF report.

## 2) Security Architecture

- **Auth middleware**: `backend/security/middleware.py`
- **Token verification**: `backend/security/firebase_auth.py`
- **Protected API access**: all scan/report/history endpoints
- **Rate limiter**: sliding window by user ID for scan submissions
- **Structured error handling**: centralized in `backend/errors.py`
- **ZIP protection**:
  - extension check
  - size limit
  - zip-slip protection
  - bad zip handling
- **GitHub scanning safety**:
  - URL validation
  - structured clone errors
  - static-only parsing
  - temporary clone cleanup

## 3) Analysis Engine Layers

### 3.1 Core static analysis
- Regex rule engine (`rules.py`)
- AST/code structure engine (`ast_parser.py`)
- Complexity + maintainability (`complexity.py`)
- Duplicate block + function similarity (`duplication.py`)
- Dependency risk scanner (`analyzer.py` + offline known-risk list)

### 3.2 Secure architecture and maturity analysis
- Secure architecture validator (`project_health.py`)
- Test coverage analyzer (`project_health.py`)
- Code maturity index (`project_health.py`)

### 3.3 AI reasoning
- Local enrichment (offline) via `ai_engine.py`
- Optional OpenAI advanced enrichment via `openai_engine.py`
- Advanced mode fallback to basic when API key is missing/fails

## 4) Scoring

- Security Score
- Trust Score
- Reliability Score
- Code Quality Score
- Improvement Potential
- Additional computed metrics:
  - Dependency Risk Score
  - Test Coverage Score
  - Code Maturity Index

## 5) Storage and History

- Runtime scan states: in-memory map
- Persistent history: `backend/storage/scan_history.json`
- History and comparisons scoped to authenticated user (`owner_uid`)

## 6) Frontend Architecture

- React + Vite SPA
- Auth context for Firebase session/token refresh
- Axios interceptor injects bearer token for every protected API call
- Protected routes (`/dashboard`, `/scan`, `/results`, `/reports`, `/about`)
- Dashboard modules:
  - score cards
  - severity bar chart
  - radar chart
  - file risk heatmap
  - issue table + AI explanation panel
  - scan history + comparison mode

## 7) Scalability Extensions

- Replace in-memory scan state with Redis
- Use worker queue (Celery/RQ) for scan jobs
- Move history to PostgreSQL for multi-instance consistency
- Add tenant RBAC and audit trail
- Add incremental scans and repository caching
