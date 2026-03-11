# Viva Script - SecureCode AI

## 1) Opening

"SecureCode AI is an enterprise-grade code risk platform with authenticated scanning, offline static analysis, and optional advanced AI reasoning."

## 2) Problem Statement

"Most teams need secure, local, and explainable code scanning. This project provides that with strong backend security, structured issue intelligence, and actionable remediation output."

## 3) Security and Authentication

"Frontend uses Firebase Authentication (email/password).  
Backend verifies Firebase ID tokens on protected endpoints through middleware.  
Invalid or expired tokens are rejected with structured `401` responses.  
Scan submission routes are rate-limited to prevent abuse."

## 4) Scan Inputs

"Users can scan:
- GitHub repository URL
- ZIP upload

GitHub repositories are cloned to temporary folders, scanned statically, and deleted.  
ZIP files are validated, safely extracted (zip-slip prevention), scanned, and cleaned up."

## 5) Analysis Engine

"The scanner combines:
- Regex vulnerability rules
- Python AST analysis
- JavaScript heuristic AST-like analysis
- Duplicate block and duplicate function similarity detection
- Dependency risk scanning
- Secure architecture validation
- Test coverage and code maturity scoring"

## 6) AI Modes

"There are two AI modes:
- Basic Mode: fully offline rule/AST/heuristic reasoning
- Advanced AI Mode: backend calls OpenAI for deep issue reasoning and secure refactor suggestions

If OpenAI fails, the system automatically falls back to Basic mode."

## 7) Issue Output Quality

"Each issue includes:
- technical risk explanation
- real-world attack scenario
- why it is dangerous
- secure fix explanation
- refactored code
- best-practice reference
- performance impact
- confidence score"

## 8) Scoring

"Primary scores:
- Security
- Trust
- Reliability
- Code Quality
- Improvement Potential

Additional metrics:
- Dependency Risk Score
- Test Coverage Score
- Code Maturity Index"

## 9) Frontend

"React + Vite dashboard includes:
- Login/Signup
- Protected routes
- Scan page with AI mode toggle
- Results page with charts and AI explanation panel
- History and scan comparison
- JSON and PDF export"

## 10) Closing

"This solution is production-oriented: authenticated, modular, error-handled, statically safe, and extendable for multi-tenant enterprise deployments."
