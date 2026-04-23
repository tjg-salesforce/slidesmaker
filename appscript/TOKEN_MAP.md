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
| `es_card_1_headline` | Card 1 headline, 2–4 words | 25 |
| `es_card_1_product` | Product name/SKU | 30 |
| `es_card_1_description` | 1–2 sentence adoption state | 200 |
| `es_card_2_headline` | Card 2 headline | 25 |
| `es_card_2_product` | Product name | 30 |
| `es_card_2_description` | Adoption state | 200 |
| `es_card_3_headline` | Card 3 headline | 25 |
| `es_card_3_product` | Product name | 30 |
| `es_card_3_description` | Adoption state | 200 |
| `es_card_4_headline` | Card 4 headline | 25 |
| `es_card_4_product` | Product name | 30 |
| `es_card_4_description` | Adoption state | 200 |
| `es_card_5_headline` | Card 5 headline | 25 |
| `es_card_5_product` | Product name | 30 |
| `es_card_5_description` | Adoption state | 200 |
| `es_card_6_headline` | Card 6 headline | 25 |
| `es_card_6_product` | Product name | 30 |
| `es_card_6_description` | Adoption state | 200 |
| `es_metric_value` | Key metric number (e.g., "85%") | 6 |
| `es_metric_label` | Label under the metric | 30 |
| `es_metric_title` | Headline above metric paragraph, 3–5 words | 30 |
| `es_metric_description` | 2–3 sentence context narrative | 250 |
| `es_metric_progress` | Numeric 0–100 driving the progress arc. Normalize the featured metric to a percentage scale (e.g., "4.89/5.0" → 97.8, "85%" → 85) | 6 |

### Slide 10 — Prioritized Workstreams
| Token | Description | Max chars |
|---|---|---|
| `ws_1_icon` | Icon name from library (see list below) | — |
| `ws_1_name` | Workstream name, short phrase | — |
| `ws_1_summary` | 1–2 sentence objective | — |
| `ws_1_status` | Bullet string, each line starts with "• ", max 3 bullets | — |
| `ws_2_icon` | Icon name for workstream 2 | — |
| `ws_2_name` | Workstream 2 name | — |
| `ws_2_summary` | Summary | — |
| `ws_2_status` | Status bullets | — |
| `ws_3_icon` | Icon name for workstream 3 | — |
| `ws_3_name` | Workstream 3 name | — |
| `ws_3_summary` | Summary | — |
| `ws_3_status` | Status bullets | — |
| `ws_4_icon` | Icon name for workstream 4 | — |
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

## Available icon names (for `ws_N_icon` tokens)

Pick one per workstream. Use different icons for each. Common picks for QBR workstreams:

`brain_ai`, `gear_bolt`, `rocket`, `lightning_bolt`, `shield_check`, `network_nodes`, `bar_chart_up`, `target_bullseye`, `team_meeting`, `handshake`, `lightbulb`, `megaphone`, `globe_web`, `lock_secure`, `funnel_filter`, `code_branch`, `cloud`, `buildings`, `headset`, `puzzle_piece`, `robot_hand`, `workflow_nodes`, `money_bag`, `scales_justice`, `compass_target`, `conveyor_ship`, `chart_laptop`, `phone_tablet`, `calendar_star`, `mountain_flag`, `arrow_right`, `wrench_key`, `magnify_search`, `checklist`, `clipboard_check`, `settings_cog`, `refresh_cycle`

Full library (132 icons): `airplane`, `bell`, `settings_gear`, `search_target`, `bar_chart_up`, `hand_touch`, `computer_monitor`, `puzzle_key`, `trophy`, `chart_down`, `book_open`, `brain`, `clock_gear`, `leaf_head`, `brick_wall`, `hand_cursor`, `server`, `buildings`, `calendar`, `calendar_date`, `truck`, `car`, `cassette`, `printer`, `clipboard_doc`, `timer`, `cloud`, `plant_sprout`, `coffee_mug`, `no_sign`, `monitor_chat`, `chat_bubble`, `target_bullseye`, `team_group`, `org_chart`, `network_nodes`, `molecule`, `cylinder_db`, `flag_send`, `venn_diagram`, `lock_secure`, `document_copy`, `wifi_person`, `sparkle_burst`, `gear_bolt`, `person_badge`, `calendar_star`, `calendar_check`, `fast_forward`, `rocket`, `funnel_filter`, `celebration`, `branch_fork`, `grid_blocks`, `refresh_cycle`, `mountain_flag`, `heart`, `emoji_face`, `hourglass`, `podium`, `lightbulb`, `pen_tool`, `calendar_1`, `globe_gear`, `laptop_devices`, `chart_laptop`, `scales_justice`, `lightbulb_idea`, `checklist`, `compass_target`, `satellite_person`, `magnify_lock`, `circle_person`, `badge_people`, `wrench_key`, `magnify_search`, `gear_inspect`, `medal_ribbon`, `code_branch`, `brain_ai`, `money_bag`, `equalizer_bars`, `team_meeting`, `conveyor_ship`, `inbox_tray`, `vinyl_record`, `phone_tablet`, `clipboard_edit`, `people_network`, `pen_writing`, `phone_sync`, `arrow_right`, `clock_no`, `astronaut`, `rocket_launch`, `star_badge`, `browser_window`, `checklist_gear`, `settings_cog`, `shield_check`, `globe_web`, `cart`, `cart_add`, `megaphone`, `gateway`, `speech_bubble`, `chat_person`, `pie_chart`, `target_rings`, `upload_box`, `puzzle_piece`, `robot_hand`, `headset`, `record_button`, `list_detail`, `stamp_machine`, `lightning_bolt`, `ticket`, `frame_window`, `handshake`, `workflow_nodes`, `cycle_refresh`, `calendar_grid`, `user_settings`, `checkmark`, `clipboard_check`, `agent_support`, `timer_clock`, `warning_triangle`, `monitor_error`, `pen_edit`, `magic_wand`

## Notes for the skill

- **80 tokens total** (76 text + 4 icon). All must be present in the `replacements` object. Missing keys → the `{{token}}` stays visible on the slide. If a field has no data, send an empty string.
- **Bullet fields** (`ws_N_status`, `map_row_N_activities`): newline-separated, each line starts with `• `. Max 3 bullets.
- **Char limits** are hard limits — the slide text boxes are sized for these. Truncate or summarize before sending.
- **The canvas can still be generated** as the human-readable prep artifact. It's just no longer in the data pipeline.
