# Production deployment

The Python backend cannot run inside the Sites Cloudflare Worker. Deploy it on a Python/Docker host and connect it to the published frontend. Supabase credentials are not preconfigured. Never deploy the default development environment publicly.

## 1. Supabase database and authentication

1. Create your own Supabase project. In its SQL Editor, execute `supabase/migrations/001_initial.sql` once, then `supabase/seed.sql`. Do not execute the migration twice; it is a versioned initial migration. The seed is idempotent.
2. Enable email/password sign-in in Supabase Authentication. Configure the Site URL and allowed redirect URLs to the actual frontend origin. Configure email delivery/confirmation for real users.
3. Copy the project URL and public anon/publishable key. Do **not** use the service-role key as SUPABASE_ANON_KEY.
4. Get the PostgreSQL connection string from the project's Connect panel (session pooler is suitable). Convert the driver prefix to `postgresql+psycopg://`. Require TLS, e.g. `?sslmode=require`. Keep the password only in backend secrets. Use the connection format and host supplied by your project; do not guess a region/host.
5. The backend uses a trusted server database connection and enforces per-user ownership/admin checks. Browser database roles have read-only policies for safe tables and no access to answer-bearing question/snapshot tables. All writes pass through the API. Do not expose the backend database credential or grant broader browser table privileges.

## 2. Backend deployment using Docker

Build from the root of the extracted project:

```powershell
docker build -f backend/Dockerfile -t signalprep-api .
```

Create `production.env` outside source control, filling real values:

```dotenv
APP_ENV=production
DEV_AUTH=false
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_PUBLIC_ANON_KEY
CORS_ORIGINS=https://YOUR_FRONTEND_ORIGIN
AI_PROVIDER=
AI_MODEL=
AI_API_KEY=
AI_BASE_URL=https://api.openai.com/v1
```

Run on a Docker-capable server behind HTTPS (or deploy the same Dockerfile on your chosen managed container host):

```powershell
docker run -d --name signalprep-api --restart unless-stopped --env-file production.env -p 127.0.0.1:8000:8000 signalprep-api
```

Point your HTTPS reverse proxy at port 8000, with a generation request timeout sufficient for the configured provider. On managed hosts, configure the service port as 8000 and the health path as `/api/health`, and set the same values in their environment/secrets panel. The image's entry point already binds `0.0.0.0:8000`. Do not set DEV_AUTH=true in production. Startup fails if production lacks Supabase Auth or PostgreSQL configuration.

Do not apply schema creation automatically at production startup. Run reviewed migrations before deployment. Use database backups and verify restores before accepting real user data. Configure ingress request limits, TLS, observability and a secrets manager appropriate to your host. AI rate limits are implemented in the app; deployment-wide request throttling belongs at the ingress layer.

## 3. Connect the hosted frontend

Use either method:

- In **Settings & connection**, enter the HTTPS backend origin, e.g. `https://api.your-domain.example`, and press **Test & connect**. Add the exact frontend origin to backend CORS_ORIGINS. The endpoint setting is a device-local preference, not a database credential.
- For a shared deployment, set the Sites runtime environment variable **BACKEND_URL** to the HTTPS API origin. The included `/api/backend/*` server proxy forwards calls with only the user's Authorization and Content-Type headers. Do not put AI_API_KEY or DATABASE_URL in browser-exposed variables. Leave the browser endpoint blank to use this proxy.

Once health reports a production connection, use **Sign in** or **Create account**. Email confirmation may be required. Tokens are held in memory, so a reload or token expiry requires signing in again. Persistent attempts remain on the server and can be resumed. Automated refresh, password recovery UI and social OAuth are not included in this version.

If deploying the frontend yourself, use the existing Worker-compatible build:

```powershell
npx --yes pnpm@11.25.0 install --frozen-lockfile
npx --yes pnpm@11.25.0 build
```

Sites publication manages the Worker deployment. `Dockerfile.frontend` is a local/container smoke-test option using Wrangler's local runtime, not a recommendation to use Wrangler dev as an internet-facing production server.

## 4. Assign the first administrator

Create your account using the frontend and sign in once, which creates its `profiles` row. Obtain that user's UUID from Supabase Auth. In the SQL Editor, as database owner:

```sql
UPDATE public.profiles SET role = 'admin' WHERE id = 'THE_CONFIRMED_USER_UUID';
```

Use the confirmed UUID of your own account. Never expose this operation in a student-accessible endpoint. Sign in again to load the role.

## 5. Optional AI

Set AI_PROVIDER (`openai`, `openai-compatible`, or `anthropic`), AI_MODEL and AI_API_KEY on the backend. For compatible providers also set AI_BASE_URL. Restart/redeploy the backend and reconnect the frontend so its capability status updates. Run a small generation job, review calculations and explanations, then approve. Keep questionable output pending/rejected.

## 6. Required live commissioning checks

These require your actual services and were not performed with the supplied environment:

1. Confirm migration/seed on PostgreSQL and that anonymous browser access cannot read `questions`, `test_questions` or `question_generation_jobs`.
2. Create two student accounts. Ensure account B receives 404 when requesting A's attempt ID, and students receive 403 for every admin endpoint.
3. Confirm users cannot change `profiles.role` through Supabase's browser API.
4. Generate a 100-question exam; inspect the API response and confirm no answer key, explanation or generation metadata appears before submission.
5. Answer, reload/sign in, resume, submit, and verify history and subject/topic scoring. Confirm timeout submission and duplicate submission behavior.
6. Import a small CSV; verify duplicate/invalid reporting and that a claimed PYQ remains an unverified pattern draft until explicitly verified.
7. Generate 1–2 AI questions with your provider. Confirm they remain pending, and that an unavailable provider produces an explicit error.
8. Check narrow/mobile layouts, screen-reader labels, network failures and real-user load. Perform a security review before broad public release.
