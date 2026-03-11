# ensure environment is up‑to‑date
pip install -r requirements.txt  # done once

# IMPORTANT: Firebase Service Account Setup
# 1. Read FIREBASE_SETUP.md for detailed instructions
# 2. Get service account JSON from Firebase Console > Project Settings > Service Accounts
# 3. Save it as: backend/firebase-service-account.json
# 4. Then restart backend below

# start as a package (relative imports work)
python -m backend.main

# or with uvicorn for auto‑reload
python -m uvicorn backend.main:app --reload