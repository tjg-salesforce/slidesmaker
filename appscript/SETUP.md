# Apps Script — QBR Deck Builder

## What it does

Receives a JSON POST from the Slack skill with pre-parsed token values, copies the QBR Slides template, replaces all `{{token}}` placeholders, shares the deck, and returns the URL.

No LLM, no Heroku, no external API keys.

## Deployment

1. Go to https://script.google.com → New Project
2. Paste the contents of `Code.gs` into the editor
3. Click Deploy → New deployment
4. Select type: **Web app**
5. Execute as: **Me** (your Workspace account)
6. Who has access: **Anyone** (or "Anyone within [your org]" if you want to restrict)
7. Click Deploy → copy the Web App URL

The URL looks like: `https://script.google.com/macros/s/AKfyc.../exec`

## Testing

### From the script editor
Run `testBuildDeck()` from the editor. Check the Execution log for the deck URL. This verifies the template copy + token replacement works.

### From curl
```bash
curl -L -X POST 'YOUR_WEBAPP_URL' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Q3 FY27 QBR — Acme Corp",
    "user_email": "you@salesforce.com",
    "replacements": {
      "customer_name": "Acme Corp",
      "cover_subtitle": "Q3 FY27 Partnership Review",
      "partnership_start_year": "2018",
      "metric_1_value": "12K",
      "metric_1_label": "Active CRM users",
      "metric_2_value": "98%",
      "metric_2_label": "Platform uptime SLA",
      "metric_3_value": "4.7/5.0",
      "metric_3_label": "CSAT score"
    }
  }'
```

Note: Apps Script redirects on POST — the `-L` flag follows the redirect.

## Expected response

```json
{"deck_url": "https://docs.google.com/presentation/d/abc123/edit"}
```

## Payload schema

```json
{
  "title": "Deck title (appears in Drive)",
  "user_email": "recipient@salesforce.com",
  "template_id": "(optional, overrides default template)",
  "replacements": {
    "customer_name": "...",
    "cover_subtitle": "...",
    ...all 75 token keys...
  }
}
```

## Token keys

See `extraction_configs/qbr.json` for the full list. The `replacements` object should use the same keys — each maps to `{{key}}` in the template.

### Cover
- `customer_name`, `cover_subtitle`

### Thank You (metrics)
- `partnership_start_year`
- `metric_1_value`, `metric_1_label`
- `metric_2_value`, `metric_2_label`
- `metric_3_value`, `metric_3_label`

### Imperatives + KPIs
- `imperative_[1-3]_name`, `imperative_[1-3]_kpi_[1-2]`

### Executive Summary (product cards + metric)
- `exec_summary_subtitle`
- `es_card_[1-6]_headline`, `es_card_[1-6]_product`, `es_card_[1-6]_description`
- `es_metric_value`, `es_metric_label`, `es_metric_title`, `es_metric_description`

### Workstreams
- `ws_[1-4]_name`, `ws_[1-4]_summary`, `ws_[1-4]_status`

### Product Innovation
- `innovation_theme_[1-3]_name`, `innovation_theme_[1-3]_description`

### Mutual Action Plan
- `map_row_[1-4]_workstream`, `map_row_[1-4]_focus_area`, `map_row_[1-4]_activities`, `map_row_[1-4]_output`

## Versioning

When you update `Code.gs`, you must create a **new deployment version** for the changes to take effect on the Web App URL. The "Test deployment" URL always runs the latest saved code — use that during development.
