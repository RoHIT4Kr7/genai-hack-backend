# Google Sign‑In (OIDC) Integration Setup

Follow these steps to configure Google Sign‑In end to end (GCP + local env) for the FastAPI backend and React (Vite) frontend in this workspace.

## What’s already implemented

- Backend (FastAPI)
  - POST `/api/v1/auth/google`: verifies a Google ID token (from the browser) using your Google OAuth Client ID, upserts a user in the DB, and returns an application JWT.
  - GET `/api/v1/auth/me`: returns the current user from the Authorization: Bearer <JWT> header.
  - SQLAlchemy DB (`sqlite:///./app.db` by default) with a `User` model.
  - CORS allows localhost ports 8080 and 5173 out of the box.
- Frontend (React + Vite + TypeScript)
  - Uses `@react-oauth/google` to obtain the Google ID token in the browser.
  - AuthContext persists the returned app JWT + user in localStorage and exposes login/logout.
  - `/login` page with Google button, and ProtectedRoute for `/dashboard` and `/profile`.

You only need to configure GCP and environment variables, then run both apps.

---

## 1) Google Cloud Console (GCP) configuration

1. Create a project (or reuse one).
2. OAuth consent screen:
   - User type: External (unless you only need internal users).
   - App name, support email, developer email, etc.
   - Scopes: the default openid/email/profile is enough (no sensitive scopes are required).
   - Test users: add your Google account (until the app is published).
3. Create OAuth 2.0 Client ID:
   - Application type: Web application.
   - Name: e.g., "Local Dev Web Client".
   - Authorized JavaScript origins (add both for dev):
     - http://localhost:8080
     - http://127.0.0.1:8080
     - http://localhost:5173 (optional; if you use the Vite default port)
     - http://127.0.0.1:5173 (optional)
   - Redirect URIs: Not required for Google Identity Services popup/One Tap.
4. Copy the generated Client ID. You’ll use it in both backend and frontend env files.

Note: For production, add your real domain (https) to Authorized JavaScript origins and to the OAuth consent screen’s Authorized domains.

---

## 2) Backend configuration (FastAPI)

Create a `.env` file at `backned-hck/.env` with at least:

```
GOOGLE_CLIENT_ID=YOUR_GOOGLE_OAUTH_CLIENT_ID
JWT_SECRET_KEY=change-this-to-a-long-random-secret
# Optional overrides
# JWT_ALGORITHM=HS256
# JWT_EXPIRES_MIN=60
# DATABASE_URL=sqlite:///./app.db
# CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173
```

Install and run (Windows PowerShell examples):

```
# Using your existing virtualenv (already present as .venv)
& d:/calmira/backned-hck/.venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

If you prefer `uv` (already used in this repo), you can instead do:

```
uv add -r requirements.txt
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend exposes:

- POST http://localhost:8000/api/v1/auth/google
- GET http://localhost:8000/api/v1/auth/me

Quick check (PowerShell):

```
# Expect 401 (unauthorized) when called without a token
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/api/v1/auth/me"
```

---

## 3) Frontend configuration (Vite React)

Create a `.env` file at `calmira-mind-haven/.env`:

```
VITE_GOOGLE_CLIENT_ID=YOUR_GOOGLE_OAUTH_CLIENT_ID
```

Install and run:

```
cd d:/calmira/calmira-mind-haven
npm install
npm run dev
# Open http://localhost:8080
```

Notes:

- The frontend calls the backend at `http://localhost:8000/api/v1` (see `src/context/AuthContext.tsx`).
- Vite’s proxy for `/api` is configured, but not required since we call the absolute backend URL.

---

## 4) End‑to‑end test

1. Visit http://localhost:8080/login
2. Click the Google Sign‑In button and choose the account you added as a Test user.
3. On success, the frontend posts the Google ID token to the backend `/auth/google`, which verifies it against `GOOGLE_CLIENT_ID`, upserts a user, and returns an app JWT.
4. The frontend stores the JWT and user in localStorage; Protected routes like `/dashboard` and `/profile` become accessible.
5. You can also verify the session via:

```
# In PowerShell, replace <TOKEN> with the stored JWT
$headers = @{ Authorization = "Bearer <TOKEN>" }
Invoke-RestMethod -Method GET -Headers $headers -Uri "http://localhost:8000/api/v1/auth/me"
```

If you get 401, ensure both frontend and backend are using the SAME Google Client ID and the backend JWT secret is set.

---

## 5) Production checklist

- Create a separate OAuth Client ID for your production domain.
- Update `CORS_ORIGINS` in backend `.env` to include your site’s HTTPS origin.
- Serve the frontend over HTTPS; add that domain to GCP Authorized JavaScript origins.
- Use a strong `JWT_SECRET_KEY` and consider shorter JWT lifetimes.
- Optional: Move from local SQLite to a managed DB (and set `DATABASE_URL`).
- Optional: Add refresh token / silent re-auth logic if desired.

---

## 6) Troubleshooting

- Vite dev server starts but page errors: Check that `.env` has `VITE_GOOGLE_CLIENT_ID` and that the value matches backend `GOOGLE_CLIENT_ID` exactly.
- 401 on `/auth/google`: Ensure your GCP OAuth Client ID is a Web application type and the JavaScript origin matches `http://localhost:8080`.
- 401 on `/auth/me`: Ensure you’re sending the app JWT (not Google’s ID token) as `Authorization: Bearer <token>`.
- CORS errors: Add your origin to `CORS_ORIGINS` in backend `.env`.
- Backend fails due to optional audio deps (e.g., `pyaudio`): Voice features are optional; auth endpoints work without them.
