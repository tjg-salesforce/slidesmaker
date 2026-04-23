# Token Map for Slack Skill → Apps Script

## Endpoint format

POST to the Apps Script Web App URL with:

```json
{
  "title": "Q3 FY27 QBR — Customer Name",
  "user_email": "recipient@salesforce.com",
  "replacements": {
    "customer_name": "value",
    "cover_subtitle": "value",
    ...
  }
}
```

Response: `{"deck_url": "https://docs.google.com/presentation/d/.../edit"}`

Flat JSON object — all tokens at the top level inside `replacements`. No nesting by slide.

## Token map with char limits

Tokens map to `{{token_name}}` placeholders in the Google Slides template. Where no char limit is listed, keep it concise — slide real-estate is limited.

### Slide 1 — Cover
| Token | Description | Max chars |
|---|---|---|
| `customer_name` | Full legal customer name (e.g., "The Procter & Gamble Company") | — |
| `cover_subtitle` | Fiscal quarter + year (e.g., "Q2 FY27 Partnership Review") | — |

### Slide 2 — Thank You for Partnership (metrics)
| Token | Description | Max chars |
|---|---|---|
| `partnership_start_year` | 4-digit year customer became SF customer | 4 |
| `metric_1_value` | Headline stat formatted for slide (e.g., "27K", "4.89/5.0") | — |
| `metric_1_label` | Short label, 1 line | — |
| `metric_2_value` | Second headline stat | — |
| `metric_2_label` | Short label | — |
| `metric_3_value` | Third headline stat | — |
| `metric_3_label` | Short label | — |

### Slide 7 — Successful Partnership Alignment (imperatives + KPIs)
| Token | Description | Max chars |
|---|---|---|
| `imperative_1_name` | Business imperative, short phrase (3–8 words) | — |
| `imperative_1_kpi_1` | First KPI with target if available | — |
| `imperative_1_kpi_2` | Second KPI | — |
| `imperative_2_name` | Second imperative | — |
| `imperative_2_kpi_1` | KPI | — |
| `imperative_2_kpi_2` | KPI | — |
| `imperative_3_name` | Third imperative | — |
| `imperative_3_kpi_1` | KPI | — |
| `imperative_3_kpi_2` | KPI | — |

### Slide 8 — Executive Summary (product cards + metric callout)
| Token | Description | Max chars |
|---|---|---|
| `exec_summary_subtitle` | One-line footprint summary | 80 |
| `es_card_1_headline` | Card 1 headline, 2–4 words | 16 |
| `es_card_1_product` | Product name/SKU | 25 |
| `es_card_1_description` | 1–2 sentence adoption state | 75 |
| `es_card_2_headline` | Card 2 headline | 16 |
| `es_card_2_product` | Product name | 25 |
| `es_card_2_description` | Adoption state | 75 |
| `es_card_3_headline` | Card 3 headline | 16 |
| `es_card_3_product` | Product name | 25 |
| `es_card_3_description` | Adoption state | 75 |
| `es_card_4_headline` | Card 4 headline | 16 |
| `es_card_4_product` | Product name | 25 |
| `es_card_4_description` | Adoption state | 75 |
| `es_card_5_headline` | Card 5 headline | 16 |
| `es_card_5_product` | Product name | 25 |
| `es_card_5_description` | Adoption state | 75 |
| `es_card_6_headline` | Card 6 headline | 16 |
| `es_card_6_product` | Product name | 25 |
| `es_card_6_description` | Adoption state | 75 |
| `es_metric_value` | Key metric number (e.g., "85%") | 6 |
| `es_metric_label` | Label under the metric | 30 |
| `es_metric_title` | Headline above metric paragraph, 3–5 words | 30 |
| `es_metric_description` | 2–3 sentence context narrative | 250 |

### Slide 10 — Prioritized Workstreams
| Token | Description | Max chars |
|---|---|---|
| `ws_1_name` | Workstream name, short phrase | — |
| `ws_1_summary` | 1–2 sentence objective | — |
| `ws_1_status` | Bullet string, each line starts with "• ", max 3 bullets | — |
| `ws_2_name` | Workstream 2 name | — |
| `ws_2_summary` | Summary | — |
| `ws_2_status` | Status bullets | — |
| `ws_3_name` | Workstream 3 name | — |
| `ws_3_summary` | Summary | — |
| `ws_3_status` | Status bullets | — |
| `ws_4_name` | Workstream 4 name | — |
| `ws_4_summary` | Summary | — |
| `ws_4_status` | Status bullets | — |

### Slide 12 — Product Innovation (3 themes)
| Token | Description | Max chars |
|---|---|---|
| `innovation_theme_1_name` | Theme name, short phrase | — |
| `innovation_theme_1_description` | 2–3 sentence "why it matters for this customer" | 325 |
| `innovation_theme_2_name` | Theme 2 name | — |
| `innovation_theme_2_description` | Description | 325 |
| `innovation_theme_3_name` | Theme 3 name | — |
| `innovation_theme_3_description` | Description | 325 |

### Slide 14 — Mutual Action Plan (tactical table)
| Token | Description | Max chars |
|---|---|---|
| `map_row_1_workstream` | Workstream name, short phrase | — |
| `map_row_1_focus_area` | 2–5 words (e.g., "Adoption & License Optimization") | — |
| `map_row_1_activities` | Bullet string, each line starts with "• ", max 3 bullets | — |
| `map_row_1_output` | 1 short sentence — expected output/decision | — |
| `map_row_2_workstream` | Row 2 workstream | — |
| `map_row_2_focus_area` | Focus area | — |
| `map_row_2_activities` | Activity bullets | — |
| `map_row_2_output` | Output | — |
| `map_row_3_workstream` | Row 3 workstream | — |
| `map_row_3_focus_area` | Focus area | — |
| `map_row_3_activities` | Activity bullets | — |
| `map_row_3_output` | Output | — |
| `map_row_4_workstream` | Row 4 workstream | — |
| `map_row_4_focus_area` | Focus area | — |
| `map_row_4_activities` | Activity bullets | — |
| `map_row_4_output` | Output | — |

## Notes for the skill

- **75 tokens total.** All must be present in the `replacements` object. Missing keys → the `{{token}}` stays visible on the slide. If a field has no data, send an empty string.
- **Bullet fields** (`ws_N_status`, `map_row_N_activities`): newline-separated, each line starts with `• `. Max 3 bullets.
- **Char limits** are hard limits — the slide text boxes are sized for these. Truncate or summarize before sending.
- **The canvas can still be generated** as the human-readable prep artifact. It's just no longer in the data pipeline.
