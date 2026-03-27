# SlidesMaker Implementation Plan

## Context
Build a Heroku Flask app that ingests a PDF (customer POV), uses Claude API to extract structured content, copies a Google Slides template, fills in placeholders, sets sharing permissions, and returns a link. Primary consumer is a Slack workflow; admin web UI for human-in-the-loop review.

## Architecture

**Stack**: Python/Flask on Heroku with Postgres
**PDF Extraction**: Claude API (native PDF support, no pdfplumber needed)
**Google Integration**: OAuth 2.0 with owner's personal account (one-time auth, refresh token stored as env var)
**Template mechanism**: `{{placeholder}}` tokens in Google Slides, replaced via `replaceAllText` batch API
**Flexibility**: Extraction config is a JSON file mapping field names to descriptions — change PDF/template combos without code changes

## Project Structure
```
SlidesMaker/
  app/
    __init__.py              # Flask app factory
    config.py                # Env var config
    routes/
      __init__.py
      api.py                 # POST /api/generate
      admin.py               # Admin UI (upload, review, history)
      auth.py                # Google OAuth (/authorize, /oauth/callback)
    services/
      __init__.py
      claude_service.py      # PDF → Claude → structured JSON
      google_service.py      # Drive copy, Slides replaceAllText, permissions
      pipeline.py            # Orchestrates extract → generate → share
    models.py                # Generation tracking (SQLAlchemy)
    templates/
      base.html
      admin/upload.html
      admin/review.html
      admin/history.html
    static/css/style.css
  extraction_configs/
    default.json             # Configurable field schema + prompts
  requirements.txt
  Procfile
  runtime.txt
  wsgi.py
  .env.example
```

## Implementation Phases

### Phase 1: Skeleton + Config
- `requirements.txt` (Flask, gunicorn, anthropic, google-api-python-client, google-auth-oauthlib, Flask-SQLAlchemy, Flask-Migrate, psycopg2-binary, python-dotenv)
- `Procfile` (`web: gunicorn wsgi:app`)
- `runtime.txt` (python-3.12.9)
- `.env.example` with all required vars
- `app/config.py` — load env vars
- `app/__init__.py` — app factory, register blueprints, init db
- `wsgi.py` — entry point

### Phase 2: Google OAuth
- `app/routes/auth.py` — `/authorize` initiates OAuth (scopes: drive + presentations, access_type=offline, prompt=consent), `/oauth/callback` displays refresh token for user to copy to Heroku config

### Phase 3: Google Service
- `app/services/google_service.py`:
  - `get_credentials()` — build from refresh token + client ID/secret
  - `copy_template(title)` — Drive `files().copy()`
  - `replace_placeholders(presentation_id, replacements)` — Slides `batchUpdate` with `replaceAllText` per field
  - `set_permissions(presentation_id, user_email)` — editor to user, viewer to @salesforce.com domain

### Phase 4: Claude Service
- `extraction_configs/default.json` — model, prompts, field definitions (dummy fields for PoC)
- `app/services/claude_service.py`:
  - `extract_from_pdf(pdf_bytes, config)` — base64-encode PDF, send to Claude with extraction prompt built from field schema, parse JSON response

### Phase 5: Pipeline
- `app/services/pipeline.py`:
  - `generate_deck(pdf_bytes, user_email, title, config)` — orchestrates extract → copy → replace → share → save to db
  - `generate_deck_from_data(data, user_email, title)` — same but skips extraction (for admin review flow)

### Phase 6: Database
- `app/models.py` — `Generation` model (id, created_at, user_email, pdf_filename, extracted_data JSON, deck_url, presentation_id, status)

### Phase 7: API Endpoint
- `app/routes/api.py` — `POST /api/generate` accepts multipart PDF + user_email, authenticates via Bearer API_KEY header, returns JSON with deck_url

### Phase 8: Admin UI
- `app/routes/admin.py`:
  - `GET /admin/upload` — upload form
  - `POST /admin/upload` — extract fields, redirect to review
  - `GET/POST /admin/review/<id>` — editable fields, generate on submit
  - `GET /admin/history` — table of past generations
- Templates with Pico CSS (CDN) for clean minimal styling

### Phase 9: Heroku Deployment
- `heroku create`, add postgres, set config vars, push, run migrations
- One-time OAuth: visit `/authorize`, copy refresh token to config

## Key Design Decisions
- **Direct PDF to Claude** (no text extraction lib) — handles tables, charts, complex layouts natively
- **`replaceAllText`** — Google's recommended approach, resilient to template layout changes
- **JSON extraction config** — swap PDF/template combos without code changes
- **Postgres from day one** — Heroku's ephemeral filesystem rules out SQLite
- **Sonnet for extraction** — fast, cheap, comparable quality for structured output tasks

## Env Vars Required
- `FLASK_SECRET_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `SLIDES_TEMPLATE_ID`, `API_KEY`, `DATABASE_URL`

## Verification (PoC)
1. Create a test Google Slides template with `{{company_name}}`, `{{executive_summary}}`, etc.
2. Use any sample PDF
3. Test via curl: `curl -X POST /api/generate -H "Authorization: Bearer KEY" -F "pdf=@sample.pdf" -F "user_email=you@example.com"`
4. Verify: deck is copied, placeholders replaced, permissions set, link returned
5. Test admin UI: upload PDF, review extracted fields, edit, generate

## Risks
- **OAuth refresh token expiry**: If Google Cloud project is in "Testing" mode, tokens expire in 7 days. Must publish consent screen.
- **Malformed Claude JSON**: Strip markdown fences, try/except on parsing. Future: use Claude tool-use for guaranteed structured output.
- **Heroku costs**: No free tier. Eco dynos + essential-0 Postgres are cheapest options.
