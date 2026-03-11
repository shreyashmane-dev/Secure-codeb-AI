# SecureCode AI - Enterprise Code Security and Reliability Analyzer

SecureCode AI is a production-ready full-stack platform that performs authenticated static code scanning with:

- Offline analysis engine (regex + AST + heuristics + scoring)
- Optional Advanced AI Mode (OpenAI) for deep risk reasoning and refactoring guidance
- Firebase Authentication (frontend + backend token verification)
- SaaS dashboard with charts, history, comparison, and report export

## Core Capabilities

- Scan by ZIP upload (safe extract, size limits, cleanup)
- Scan by GitHub URL (clone locally, static-only scan, cleanup)
- Detect:
  - Vulnerabilities
  - Secrets
  - Insecure auth and file handling patterns
  - Dependency risks (requirements.txt, package.json)
  - Duplicate code blocks and duplicate function similarity
  - Dead code
  - Missing exception handling
  - Code smells (long functions, too many params, deep nesting, magic numbers, naming issues, unused imports)
- Validate architecture:
  - Missing input validation
  - Missing auth layer
  - Insecure CORS wildcard usage
  - Debug mode enabled
- Test coverage analyzer (basic)
- Code maturity index
- Historical scan comparison mode
- PDF and JSON report generation

## Authentication and Security

- Firebase email/password signup/login/logout on frontend
- ID token sent as:
  - `Authorization: Bearer <token>`
- Backend verifies token via Firebase Admin SDK on protected routes
- Invalid/expired/revoked token -> `401 Unauthorized`
- Scan endpoints protected by auth middleware
- Rate limiting on scan submission endpoints
- Structured error responses

## AI Modes

- Basic Mode:
  - Offline engine only
  - No external AI API call
- Advanced AI Mode:
  - Backend calls OpenAI (never from frontend)
  - Strict structured AI response fields per issue:
    - `issue_type`
    - `severity`
    - `risk_explanation`
    - `real_world_attack_scenario`
    - `why_this_is_dangerous`
    - `secure_fix_explanation`
    - `refactored_code`
    - `best_practice_reference`
    - `performance_impact`
    - `confidence_score`
- OpenAI failures automatically fall back to Basic Mode.

## Scoring

- Security Score
- Trust Score
- Reliability Score
- Code Quality Score
- Improvement Potential %
- Additional metadata:
  - Dependency Risk Score
  - Test Coverage Score
  - Code Maturity Index

## API Endpoints

Public:
- `GET /health`

Protected (Firebase token required):
- `GET /auth/me`
- `POST /scan/github`
- `POST /scan/upload`
- `GET /scan/status?scan_id=<id>`
- `GET /scan/history`
- `GET /scan/analytics`
- `GET /scan/export/{scan_id}`
- `GET /scan/compare?scan_id_a=<id>&scan_id_b=<id>`
- `POST /generate/report`

## Frontend Pages

- `/login`
- `/signup`
- `/dashboard`
- `/scan`
- `/results/:scanId`
- `/reports`
- `/about`

## Project Structure

```text
SecureCode-AI/
  backend/
    api/
      auth.py
      scan.py
      upload.py
      report.py
    engine/
      analyzer.py
      ai_engine.py
      openai_engine.py
      rules.py
      ast_parser.py
      complexity.py
      duplication.py
      project_health.py
      scoring.py
      trust_engine.py
      reliability_engine.py
      quality_engine.py
    security/
      firebase_auth.py
      middleware.py
      dependencies.py
      rate_limiter.py
    services/
      scan_jobs.py
    storage/
      scan_store.py
    utils/
      file_handler.py
      git_handler.py
      report_generator.py
    main.py
    config.py
    models.py
    runtime.py
    errors.py
  frontend/
    src/
      api/client.js
      auth/firebase.js
      context/AuthContext.jsx
      context/ThemeContext.jsx
      components/
      pages/
      App.jsx
      main.jsx
  requirements.txt
  docker-compose.yml
  Dockerfile
```

## Setup Instructions

### 1) Clone and backend setup

```bash
cd C:\Users\OMPRASAD\SecureCode-AI
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy backend\.env.example backend\.env
```

### 2) Firebase setup (required)

1. Create Firebase project.
2. Enable Authentication -> Email/Password provider.
3. Create Firebase Web App and copy frontend keys.
4. Generate service account key JSON from Firebase Console.
5. Place JSON at:
   - `backend/firebase-service-account.json`
6. Set backend env:
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_SERVICE_ACCOUNT_PATH=backend/firebase-service-account.json`
7. Set frontend env in `frontend/.env`:
   - `VITE_FIREBASE_API_KEY`
   - `VITE_FIREBASE_AUTH_DOMAIN`
   - `VITE_FIREBASE_PROJECT_ID`
   - `VITE_FIREBASE_STORAGE_BUCKET`
   - `VITE_FIREBASE_MESSAGING_SENDER_ID`
   - `VITE_FIREBASE_APP_ID`

### 3) OpenAI setup (optional for Advanced AI Mode)

In `backend/.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SEC=45
ADVANCED_AI_MAX_ISSUES=20
```

If not configured, Advanced mode requests fall back to Basic mode.

### 4) Run backend

```bash
cd C:\Users\OMPRASAD\SecureCode-AI
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5) Run frontend

```bash
cd C:\Users\OMPRASAD\SecureCode-AI\frontend
npm install
copy .env.example .env
npm run dev
```

Open:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

## Docker

```bash
cd C:\Users\OMPRASAD\SecureCode-AI
docker compose up --build
```

## Backend Verification Checklist

- Protected endpoints reject missing token with 401
- Invalid GitHub URL returns structured 400
- Corrupted ZIP fails with structured scan error
- Valid ZIP scan completes and returns scores/issues
- PDF generation works for completed scan IDs

## Notes

- The scanner never executes uploaded/cloned source code.
- GitHub and ZIP content is only parsed statically.
- Temporary workspaces are cleaned after scan completion/failure.
