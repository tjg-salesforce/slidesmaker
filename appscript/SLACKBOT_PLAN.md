# Deck Generation Plan — Skill → Canvas → Deck

## Overview

The skill already has all 75 token values structured in memory before it writes the canvas. Instead of throwing that data away and re-extracting it later, the skill embeds the pre-parsed JSON payload directly into the canvas as a hidden section. Heroku retrieves it mechanically — no LLM, no MCP, no extraction.

## End-to-end flow

### Step 1 — Skill creates canvas (already works)
- Skill runs Phases 1–3 (gather inputs, research Slack, research innovation)
- Skill creates the human-readable QBR canvas (Phase 4)
- **New**: skill appends a hidden/collapsed section at the bottom of the canvas containing the full 75-token JSON payload wrapped in delimiters:

```
───────────────────
[collapsed or visually separated section]

<!-- DECK_PAYLOAD
{"customer_name":"The Procter & Gamble Company","cover_subtitle":"Q3 FY27 Partnership Review","partnership_start_year":"2015","metric_1_value":"27K",...all 75 tokens...,"user_email":"ae@salesforce.com","title":"Q3 FY27 QBR — P&G"}
DECK_PAYLOAD -->
```

The AE doesn't need to interact with this section. It's just data storage riding along with the canvas.

### Step 2 — Skill adds a "Generate Deck" workflow button to the canvas
- The button triggers a Slack workflow (built in Workflow Builder)
- The workflow does two things:
  1. Adds TJ to the canvas (so TJ's Slack token can read it)
  2. Writes a row to a Google Sheet with: `canvas_url`, `ae_email`, `status=pending`
- The workflow tells the AE: "Your deck is being generated — you'll be notified on this canvas when it's ready."

### Step 3 — Apps Script picks up the new row
- An Apps Script time-driven trigger checks the Sheet every 30–60 seconds for rows with `status=pending`
- When it finds one, it calls a Heroku endpoint with the `canvas_url` and `ae_email`

### Step 4 — Heroku reads the canvas and forwards to Apps Script
- Heroku calls the Slack API using TJ's `SLACK_TOKEN`:
  - Fetches canvas content (one API call)
- Heroku parses the payload — no LLM, just:
  ```python
  payload_text = canvas_text.split("DECK_PAYLOAD")[1]
  data = json.loads(payload_text.strip())
  ```
- Heroku forwards the parsed JSON to the Apps Script deck builder endpoint

### Step 5 — Apps Script builds the deck
- Copies the Slides template
- Replaces all 75 `{{token}}` placeholders
- Sets permissions (AE gets editor, salesforce.com domain gets viewer)
- Returns the `deck_url`

### Step 6 — Result delivered back to the AE
- Apps Script writes `deck_url` back to the Sheet row, sets `status=done`
- A webhook-triggered workflow fires:
  - Adds the deck link to the canvas (at the top or in the header)
  - @mentions the AE so they get a Slack notification
- AE opens the canvas notification, sees their deck link, clicks through

## What the skill needs to do (changes from current)

1. **Embed the JSON payload** in the canvas when creating it. Append after all human-readable content, wrapped in `<!-- DECK_PAYLOAD ... DECK_PAYLOAD -->` delimiters. Include `user_email` and `title` in the payload so downstream steps have everything they need.

2. **Add a "Generate Deck" workflow button** to the canvas. The workflow is pre-built in Workflow Builder — the skill just needs to embed the trigger.

3. **No HTTP calls needed from the skill.** The skill's job ends after writing the canvas. Everything downstream is triggered by the AE clicking the button.

## What needs to be built

| Component | Owner | Status |
|---|---|---|
| Skill: embed JSON payload in canvas | Slackbot skill update | To do |
| Skill: add workflow button to canvas | Slackbot skill update | To do |
| Workflow: add TJ to canvas + write Sheet row | Workflow Builder | To do |
| Google Sheet: queue table | Google Sheets | To do |
| Apps Script: Sheet trigger → call Heroku | Apps Script | To do |
| Heroku: read canvas via Slack API + forward | Flask route | To do |
| Apps Script: deck builder (copy/replace/share) | Apps Script | Done (`Code.gs`) |
| Webhook workflow: add deck link to canvas + notify AE | Workflow Builder | To do |

## Why this works

- **No LLM extraction** — the skill parsed the data, Heroku just retrieves it
- **No MCP** — plain Slack API call to read canvas text
- **No Anthropic API key** — removed from the pipeline entirely
- **No DLP label issues** — Apps Script runs inside the Workspace
- **Clean AE experience** — they see a canvas, click a button, get notified with a deck link
- **TJ's Slack token is only used server-side** (Heroku) to read canvases after the workflow grants access
