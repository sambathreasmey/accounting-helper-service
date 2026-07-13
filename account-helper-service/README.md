# Accounting Helper Service

A Telegram bot that parses purchase-order messages, dispatches document
generation to a GitHub Actions workflow (`po-generate-automation`), keeps a
history of every PO in Postgres (Neon), and ships a Telegram **Mini App**
(dashboard, history, editable regenerate) served straight from FastAPI.

## Architecture

```
Telegram message ──▶ /telegram/webhook ──▶ router ──▶ po_handler
                                                          │
                                              parse + save to DB (status=pending)
                                                          │
                                          repository_dispatch to GitHub ──▶ status=dispatched
                                                          │
                        po-generate-automation workflow runs, generates the doc
                                                          │
                        POST /api/po/callback (X-Callback-Secret) ──▶ status=completed|failed
                                                          │
                                         Telegram message with the file link
```

The Mini App (`/app`) talks to `/api/webapp/*`, authenticated via Telegram's
`initData` (sent as `X-Telegram-Init-Data`), scoped per user via their
Telegram `chat_id`.

## Local setup

```bash
cp .env.example .env   # fill in real values
pip install -r requirements.txt
fastapi dev app/main.py
```

Tables are created automatically on startup (`init_models()` in
`app/db/database.py`). For anything beyond this project's current scale,
switch to Alembic migrations instead of relying on `create_all`.

## New environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Neon Postgres connection string (pooled). Normalized to the `asyncpg` driver automatically. |
| `PO_CALLBACK_SECRET` | Shared secret the generation workflow must send back when reporting completion. |
| `MINI_APP_URL` | Public URL of the Mini App (`{PUBLIC_BASE_URL}/app`). Adds the "Open Dashboard" button to bot messages. |

## Wiring up `po-generate-automation`

Each `repository_dispatch` now includes a `callback` block:

```json
{
  "event_type": "po-generate-trigger",
  "client_payload": {
    "chat_id": 123456789,
    "invitation_data": { "data": [ /* ... */ ], "references": [] },
    "callback": {
      "po_db_id": "b3f1...uuid",
      "url": "https://your-app.fastapicloud.dev/api/po/callback",
      "secret": "<PO_CALLBACK_SECRET>"
    }
  }
}
```

At the end of the workflow, `POST` back:

```bash
curl -X POST "$CALLBACK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Callback-Secret: $CALLBACK_SECRET" \
  -d '{
        "po_db_id": "b3f1...uuid",
        "status": "completed",
        "file_url": "https://.../generated-po.pdf",
        "github_run_id": "'"$GITHUB_RUN_ID"'"
      }'
```

Use `"status": "failed"` with an `"error_message"` if generation fails —
this is what unlocks the "edit & regenerate" flow in the Mini App (only
`completed`/`failed` orders are editable; `pending`/`dispatched` are still
in flight).

## Mini App

Static, dependency-free HTML/JS at `app/static/webapp/`, served at `/app`.
Three views: dashboard stats, filterable/paginated history, and a detail
sheet that lets you edit line items and re-trigger generation for any
`completed` or `failed` order.

## Project layout

```
app/
  api/            FastAPI routers (telegram webhook, PO callback, mini app API)
  bot/            Telegram update routing + message handlers + PO text parser
  core/           settings, Telegram initData auth
  db/             SQLAlchemy models, session, CRUD
  schemas/        Pydantic request/response models
  services/       Telegram/GitHub HTTP clients, Redis dedupe
  static/webapp/  Mini App frontend
```
