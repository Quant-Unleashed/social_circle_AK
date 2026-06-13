# Social Hub

Private social coordination hub for friends and family. The app is built around:

- invite-only login
- profiles
- groups
- module access by invite code
- activity feed
- tennis scoring
- badminton ladder
- events and hosting tools
- Life Map entries with visibility
- an external FIFA Sweepstake link

The FIFA Sweepstake is intentionally **not** imported as a module. The hub links out to:

<https://aman-fifa-sweepstake.onrender.com>

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/login>.

Local invite codes:

- `SOCIALHUB`
- `TENNIS2026`
- `BADMINTON2026`
- `BBQCREW`
- `FAMILY`

Local state is stored in `data/social_hub_state.json`, which is ignored by git.

## Free hosting plan

Use Render free web service for the FastAPI app and Supabase free tier for Auth/Postgres.

Render uses `render.yaml`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set these environment variables in Render:

- `SESSION_SECRET`
- `APP_INVITE_CODE`
- `ADMIN_EMAILS`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

Create the Supabase tables with `db/schema.sql`. The current app has a local JSON store for development and a schema ready for the hosted Postgres data model.

## Tests

```bash
pytest
```
