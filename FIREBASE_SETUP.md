# Firebase Setup for Authentication

## Backend: Firebase Service Account

The backend needs a Firebase service account private key to verify ID tokens from users.

### Get Your Service Account JSON

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **capstone-60578**
3. Navigate to **Project Settings** (gear icon)
4. Click the **Service Accounts** tab
5. Click **"Generate New Private Key"** (Node.js environment)
6. A JSON file will download automatically

### Add Service Account to Backend

**Option A: File-based (recommended for local dev)**

1. Save the downloaded JSON as: `backend/firebase-service-account.json`
2. The backend will automatically load it from `FIREBASE_SERVICE_ACCOUNT_PATH`

**Option B: Environment variable**

1. Open the JSON file and copy all contents
2. In `.env`, uncomment and set:
   ```dotenv
   FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...entire JSON...}
   ```
3. Comment out `FIREBASE_SERVICE_ACCOUNT_PATH`

### Verify

Once added, restart the backend:

```powershell
python -m uvicorn backend.main:app --reload
```

Then try logging in on the frontend. The 401 errors should disappear once you're authenticated.

---

## Frontend: Firebase Web Config ✅

Already configured in `.env` and `frontend/.env`:
- API Key
- Auth Domain  
- Project ID
- Storage Bucket
- etc.

These allow the web app to authenticate users and get ID tokens.
