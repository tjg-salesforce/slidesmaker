# SlidesMaker — Next Steps

## Status
Primary intake is now a **Slack canvas URL → Claude extraction → Google Slides deck**, targeted at QBR prep.

- Admin UI: paste canvas (or URL, once MCP is wired) → Claude extracts fields → review/edit → generate deck
- Template: FY27 PACE QBR (tokenized), ~45 placeholders across 15 slides
- Extraction config: `extraction_configs/qbr.json` — tuned to canvas sections (§ 1 Partnership Stats, § 2 State, § 3 KPIs, § 5 Product Adoption, § 6 Underway, § 7 Innovation, § 8 MAP)
- Legacy PDF intake preserved (`/admin/upload` + `/api/generate` with Bearer auth) but no longer linked from nav
- Heroku deployment with Postgres
- App URL: https://slidesmaker-bded4b9587fb.herokuapp.com

## Env vars
- `ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN`, `SLIDES_TEMPLATE_ID`, `API_KEY`, `DATABASE_URL`, `FLASK_SECRET_KEY` (existing)
- **New:** `SLACK_TOKEN` — user token (`xoxp-…`) used by Slack MCP for canvas reads
- **New (planned):** `SLACK_MCP_URL` — defaults to `https://mcp.slack.com/mcp` (remote MCP)

## Next Steps (in priority order)

### 1. Wire Slack MCP for canvas URL input
- Use Anthropic SDK MCP connector (beta): pass `mcp_servers` to `client.messages.create`
- Admin form: add canvas URL field; prefer URL over pasted text
- New helper: `claude_service.extract_from_canvas_url(url, config)` — passes URL + MCP config to Claude
- Requires `anthropic-beta: mcp-client-2025-04-04` header
- Caveat: canvas must be readable by the user who owns `SLACK_TOKEN` (public, or user is a member)

### 2. First end-to-end QBR run + prompt tuning
- Paste the P&G sample canvas through `/admin/canvas`, check each of the ~45 extracted fields
- Expect to iterate `qbr.json` field descriptions based on misalignments
- Inspect generated deck — confirm tokens land in the right slots, bullet formatting renders correctly

### 3. Review UI improvements for QBR
- 45 fields is a long form; group by slide section with headings (§ 1, § 2, etc.)
- Bullet-list fields (activities, workstream status) need bigger textareas / markdown preview

### 4. Slide capacity overflows
- Canvas sometimes has more rows than template slots (e.g., 7 products vs. 6 exec-summary cards, 6 workstreams vs. 4 rows, 9 MAP actions vs. 4 rows)
- Current approach: Claude prioritizes/groups. Consider: admin UI preview of what got dropped; or template variants with more rows.

### 5. Slack app (longer term)
Submit for approval to create a proper Slack app for the production Salesforce workspace.
- Would enable slash command UX instead of admin paste

### 6. Fix flash messages in admin UI
- Error messages on generation failure aren't always visible; `base.html` flash rendering needs polish
- Low priority since errors log to Heroku

### 7. Add Heroku redirect URI to Google Cloud Console
Required if the refresh token ever expires.
- Add: `https://slidesmaker-bded4b9587fb.herokuapp.com/oauth/callback`
- Google Cloud Console → APIs & Services → Credentials → OAuth client

## Key Info
- Heroku app: `slidesmaker`
- GitHub repo: `https://github.com/tjg-salesforce/slidesmaker`
- Local project path: `/Users/tgrossman/Documents/Claude Code/SlidesMaker`
- Extraction configs: `extraction_configs/qbr.json` (primary), `extraction_configs/default.json` (legacy PDF path)
- To run locally: `cd` to project, `OAUTHLIB_INSECURE_TRANSPORT=1 venv/bin/flask --app wsgi run`
