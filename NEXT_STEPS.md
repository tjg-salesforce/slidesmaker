# SlidesMaker — Next Steps

## Status

**Primary intake: Slack canvas → Claude (via Slack MCP) → Google Slides deck.** Targeted at FY27 QBRs.

Working end-to-end except for one sharing blocker (DLP label, see Known Issues §1):

- Admin pastes canvas URL (or canvas markdown) + recipient email on `/admin/canvas`
- Request returns immediately; extraction runs in a background thread to avoid Heroku's 30s H12 timeout
- Status page (`/admin/status/<id>`) polls every 3s; redirects to review page when extraction completes
- Admin reviews/edits ~75 extracted fields, clicks Generate
- Deck is copied from the tokenized FY27 QBR template, tokens replaced, shared with recipient

Legacy PDF intake preserved at `/admin/upload` and `/api/generate` (Bearer auth) but no longer linked in nav.

- App URL: https://slidesmaker-bded4b9587fb.herokuapp.com

## Architecture

```
POST /admin/canvas
  │
  ├─ Create Generation record (status=queued)
  ├─ Spawn daemon thread (app context pushed inside)
  └─ Redirect to /admin/status/<id>

Thread
  ├─ status = extracting
  ├─ claude_service.extract_from_canvas_url(url, config)
  │     └─ Anthropic Messages API with mcp_servers + mcp_toolset
  │           └─ Claude calls Slack MCP tools → fetches canvas → returns JSON
  ├─ record.extracted_data = parsed JSON
  └─ status = pending_review

POST /admin/review/<id>  (user edits + submits)
  ├─ pipeline.generate_deck_from_data
  │     ├─ google_service.copy_template  (Drive files.copy)
  │     ├─ google_service.replace_placeholders  (Slides batchUpdate replaceAllText)
  │     └─ google_service.set_permissions  (Drive permissions.create: user writer + domain reader)
  └─ status = done; redirect to /admin/history
```

## Env vars

Existing:
- `ANTHROPIC_API_KEY`, `FLASK_SECRET_KEY`, `API_KEY`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
- `SLIDES_TEMPLATE_ID` — tokenized FY27 QBR template
- `DATABASE_URL`

Added for canvas flow:
- `SLACK_TOKEN` — `xoxp-…` user token used by Slack MCP
- `SLACK_MCP_URL` — defaults to `https://mcp.slack.com/mcp`

Known needed but **not yet wired**:
- `DRIVE_LABEL_ID`, `DRIVE_LABEL_FIELD_ID`, `DRIVE_LABEL_EXTERNAL_CHOICE_ID` — for automating the DLP label flip (see Known Issues §1)

## Key files

- `extraction_configs/qbr.json` — field map, system prompt, user prompt for QBR canvases (primary)
- `extraction_configs/default.json` — legacy config for PDF path (kept for fallback)
- `app/services/claude_service.py` — `extract_from_pdf`, `extract_from_canvas`, `extract_from_canvas_url` (MCP)
- `app/services/pipeline.py` — `_extract_into` (thread-safe), `extract_canvas_*_into`, `generate_deck_from_data`, `_build_deck`
- `app/services/google_service.py` — Drive/Slides wrappers (`copy_template`, `replace_placeholders`, `set_permissions`)
- `app/routes/admin.py` — `/canvas`, `/status/<id>`, `/review/<id>`, `/history`, (hidden) `/upload`
- `app/templates/admin/canvas.html`, `status.html`, `review.html`, `history.html`
- `app/config.py`, `app/models.py`

Anthropic MCP connector details:
- Current beta: `anthropic-beta: mcp-client-2025-11-20`
- Passed via `extra_body={"mcp_servers": [...], "tools": [{"type":"mcp_toolset","mcp_server_name":"slack"}]}` because the installed SDK (`anthropic==0.49.0`) doesn't accept `mcp_servers` as a native kwarg
- `authorization_token` is the raw `xoxp-…` token (no `Bearer` prefix)
- `max_tokens=8192` for canvas extraction (45+ fields + tool-use overhead)

## V1 slide subset (what IS in the MVP)

15 slides. Page numbers reference the original `QBR-Examples/FY27 PACE QBR Template.pdf`.

| # | Template pg | Slide | Tokens on slide |
|---|---|---|---|
| 1 | 3 | Cover | `customer_name`, `cover_subtitle` |
| 2 | 5 | Thank You for Partnership — **Option 2 (metrics)** | `partnership_start_year`, `customer_name`, `metric_1_value`, `metric_1_label`, `metric_2_value`, `metric_2_label`, `metric_3_value`, `metric_3_label` |
| 3 | 6 | Agenda | *(static)* |
| 4 | 7 | § State of the Partnership (divider) | *(static)* |
| 5 | 9 | Let's Ensure We're Aligned — **Option 2** | *(static — discussion prompts kept as-is)* |
| 6 | 11 | § Value Realization (divider) | *(static)* |
| 7 | 12 | Successful Partnership Alignment (imperatives + KPIs) | `imperative_1_name`, `imperative_1_kpi_1`, `imperative_1_kpi_2`, `imperative_2_name`, `imperative_2_kpi_1`, `imperative_2_kpi_2`, `imperative_3_name`, `imperative_3_kpi_1`, `imperative_3_kpi_2` |
| 8 | 16 | Executive Summary — **Option 2** (product cards) | `exec_summary_subtitle`, `es_card_1_headline`, `es_card_1_product`, `es_card_1_description` (×6 cards), `es_metric_value`, `es_metric_label`, `es_metric_title`, `es_metric_description` |
| 9 | 19 | § What's Underway (divider) | *(static)* |
| 10 | 20 | Prioritized Workstreams — **Option 1** | `ws_N_name`, `ws_N_summary`, `ws_N_status` for N=1..4 |
| 11 | 21 | § Salesforce Innovation (divider) | *(static)* |
| 12 | 23 | Product Innovation (3-theme layout) | `innovation_theme_N_name`, `innovation_theme_N_description` for N=1..3 |
| 13 | 25 | § Mutual Action Plan (divider) | *(static)* |
| 14 | 27 | Proposed Plan — **Option 2** (tactical table) | `map_row_N_workstream`, `map_row_N_focus_area`, `map_row_N_activities`, `map_row_N_output` for N=1..4 |
| 15 | 28 | Thank You | *(static)* |

### Complete token inventory (75 tokens)

All keys in `extraction_configs/qbr.json`:

**Cover / header**
- `customer_name`
- `cover_subtitle`

**Thank You Option 2 (metrics)**
- `partnership_start_year`
- `metric_1_value`, `metric_1_label`
- `metric_2_value`, `metric_2_label`
- `metric_3_value`, `metric_3_label`

**Imperatives + KPIs**
- `imperative_1_name`, `imperative_1_kpi_1`, `imperative_1_kpi_2`
- `imperative_2_name`, `imperative_2_kpi_1`, `imperative_2_kpi_2`
- `imperative_3_name`, `imperative_3_kpi_1`, `imperative_3_kpi_2`

**Exec Summary (product health cards + metric callout)**
- `exec_summary_subtitle`
- `es_card_1_headline`, `es_card_1_product`, `es_card_1_description`
- `es_card_2_headline`, `es_card_2_product`, `es_card_2_description`
- `es_card_3_headline`, `es_card_3_product`, `es_card_3_description`
- `es_card_4_headline`, `es_card_4_product`, `es_card_4_description`
- `es_card_5_headline`, `es_card_5_product`, `es_card_5_description`
- `es_card_6_headline`, `es_card_6_product`, `es_card_6_description`
- `es_metric_value`, `es_metric_label`, `es_metric_title`, `es_metric_description`

**Workstreams table (4 rows × 3 cols)**
- `ws_1_name`, `ws_1_summary`, `ws_1_status` *(status = bullet string)*
- `ws_2_name`, `ws_2_summary`, `ws_2_status`
- `ws_3_name`, `ws_3_summary`, `ws_3_status`
- `ws_4_name`, `ws_4_summary`, `ws_4_status`

**Product Innovation (3 themes)**
- `innovation_theme_1_name`, `innovation_theme_1_description`
- `innovation_theme_2_name`, `innovation_theme_2_description`
- `innovation_theme_3_name`, `innovation_theme_3_description`

**Mutual Action Plan table (4 rows × 4 cols)**
- `map_row_1_workstream`, `map_row_1_focus_area`, `map_row_1_activities`, `map_row_1_output` *(activities = bullet string)*
- `map_row_2_workstream`, `map_row_2_focus_area`, `map_row_2_activities`, `map_row_2_output`
- `map_row_3_workstream`, `map_row_3_focus_area`, `map_row_3_activities`, `map_row_3_output`
- `map_row_4_workstream`, `map_row_4_focus_area`, `map_row_4_activities`, `map_row_4_output`

Bullet-list convention: newline-separated string with each line starting with `• `.

## Slides NOT in the MVP (deferred)

Template has ~35 slides total. These are explicitly skipped in v1:

| Template pg | Slide | Why deferred |
|---|---|---|
| 1–2 | Instructions / meta | Not real slides — delete from deck |
| 4 | Thank You — Option 1 (narrative) | Chose Option 2 (metrics) instead |
| 8 | State Option 1 (gaps/flags/superpowers) | Chose Option 2 (alignment prompts) |
| 10 | State Option 3 (partnership check-in) | Chose Option 2 |
| 13 | Alignment pre-filled example | Canvas instructs to delete |
| 14 | Product Adoption Dashboard | Internal only — not for customer deck |
| 15 | Building on Strong Foundation — Option 1 | Chose Option 2 (exec summary cards) |
| 17 | Customer Success Score — Option 3 | Chose Option 2 |
| 18 | $20M Value Realized | Needs real Salesforce-integrated metrics; punted |
| 22 | Industry content links | Static link collection; not customer-facing |
| 24 | Product Innovation 4-capability cards | Chose 3-theme layout (pg 23) |
| 26 | Proposed Plan — Option 1 (narrative) | Chose Option 2 (tactical table) |
| 29 | Industry Examples | Static links |
| 30 | Optional add-ons | Reference material |
| 31 | What We Heard (alternative state slide) | Chose alignment format |
| 32–33 | Capability Analysis (alternative exec summary) | Chose product cards |
| 34 | Signature Success Path timeline | Only for Signature customers |
| 35 | Value Drift graph | Optional analytical aid |

## Next Steps (in priority order)

### 1. Unblock deck sharing across DLP labels
Currently blocks customers on `salesforce.com` from accessing decks generated by the dev Google account. See Known Issues §1. Short-term: manually change label in Drive UI. Medium: automate via `files.modifyLabels` (needs scope + label IDs). Long: move deck ownership to a Salesforce Workspace project once security review clears.

### 2. First clean end-to-end QBR run + prompt tuning
Run the P&G sample canvas through the flow on Heroku. Inspect each of the 75 extracted fields vs. canvas content. Iterate `qbr.json` field descriptions where Claude is returning the wrong shape (most likely: bullet-string formatting, over-long fields for small boxes, imperatives vs. KPI assignment).

### 3. Review UI improvements
75 fields is a long flat form. Group by slide section with headings (Cover, Thank You, Imperatives, Exec Summary, Workstreams, Innovation, MAP). Bullet-list fields (`ws_N_status`, `map_row_N_activities`) need taller textareas.

### 4. Slack auto-DM on deck completion
Currently admin has to copy the deck URL from `/admin/history` and share manually. Add a `chat.postMessage` call with the deck URL to the recipient once status=done. Uses existing `SLACK_TOKEN`.

### 5. Overflow handling for slide capacity
Canvas often has more rows than template slots (7 products vs. 6 exec-summary cards, 6 workstreams vs. 4 rows, 9 MAP actions vs. 4 rows). Today Claude prioritizes/groups silently. Consider surfacing "we dropped these rows" in the review UI.

### 6. Proper Slack app (longer term)
Submit for approval to create a production Slack app. Would enable slash-command UX instead of admin paste. Blocked on workspace approval.

### 7. Flash messages polish + error surfacing
Error flash rendering in base.html is minimal. Extraction errors now hit the status page cleanly, but deck-build errors still require checking Heroku logs.

### 8. Heroku OAuth redirect URI
Required if `GOOGLE_REFRESH_TOKEN` ever expires or needs scope expansion.
- Add: `https://slidesmaker-bded4b9587fb.herokuapp.com/oauth/callback`
- Google Cloud Console → APIs & Services → Credentials → OAuth client

## Known Issues

### 1. DLP label blocks external sharing
New decks in the dev Google account get an "internal only" classification label by default. Even after `drive.permissions().create` succeeds for a `salesforce.com` recipient, the recipient gets "Can't access item — Switch to an account with access." Workaround: manually flip the label to "external allowed" in Drive UI after each generation. Fix requires `drive.labels` scope + label IDs (user is non-admin; IDs must be obtained via API call rather than admin console).

### 2. Single-dyno thread assumption
Background extraction runs as a daemon thread in the same web dyno. If we scale to multiple web dynos, threads won't share state. If the dyno restarts mid-extraction, records are stuck in `queued`/`extracting`. Real fix: add a worker dyno + RQ/Celery.

### 3. `anthropic==0.49.0` SDK predates native MCP kwargs
We pass `mcp_servers` and `tools` via `extra_body` to bypass SDK kwarg validation. Upgrading the SDK would let us use native kwargs; no functional change needed.

### 4. Canvas must be readable by `SLACK_TOKEN`'s user
Either public or user is a channel/DM member. The Slack MCP uses the provided token as-is; no workspace-wide impersonation.

## Key Info
- Heroku app: `slidesmaker` (pass `-a slidesmaker` to heroku CLI commands)
- GitHub repo: `https://github.com/tjg-salesforce/slidesmaker`
- Local project path: `/Users/tgrossman/Documents/Claude Code/SlidesMaker`
- To run locally: `cd` to project, `OAUTHLIB_INSECURE_TRANSPORT=1 venv/bin/flask --app wsgi run`
- Heroku logs: `heroku logs --tail -a slidesmaker`
- Slack MCP probe (verifies token works): `curl -sv -X POST https://mcp.slack.com/mcp -H "Authorization: Bearer $SLACK_TOKEN" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d @/tmp/mcp_init.json` (init JSON payload in `/tmp/mcp_init.json`)
