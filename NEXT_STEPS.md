# SlidesMaker — Next Steps

## Status
Core flow is working end-to-end:
- Admin UI: upload PDF → Claude extracts fields → review/edit → generate Google Slides deck
- API endpoint: POST /api/generate (Bearer auth)
- Heroku deployment with Postgres
- App URL: https://slidesmaker-bded4b9587fb.herokuapp.com

## Next Steps (in priority order)

### 1. Slack workflow integration
Build a Slack workflow that POSTs to `POST /api/generate` with a PDF attachment and user email.
- Endpoint already built and auth-protected with Bearer API_KEY
- Test with: `curl -X POST https://slidesmaker-bded4b9587fb.herokuapp.com/api/generate -H "Authorization: Bearer <API_KEY>" -F "pdf=@sample.pdf" -F "user_email=user@example.com"`

### 2. Google Slides template polish
Design the actual slides layout so placeholder text renders well.
- Current template has all placeholders on one slide
- Consider multiple slides per section, proper fonts/positioning
- Template lives in the dev Google account used for OAuth

### 3. Fix flash messages in admin UI
Error messages on generation failure aren't visible to the user.
- `flash()` calls are working but base.html flash rendering needs fixing
- Low priority since errors now log to Heroku logs

### 4. Add Heroku redirect URI to Google Cloud Console
Required if the refresh token ever expires and needs to be re-generated.
- Add: `https://slidesmaker-bded4b9587fb.herokuapp.com/oauth/callback`
- Google Cloud Console → APIs & Services → Credentials → OAuth client

## Key Info
- Heroku app: `slidesmaker`
- GitHub repo: `https://github.com/tjg-salesforce/slidesmaker`
- Local project path: `/Users/tgrossman/Documents/Claude Code/SlidesMaker`
- Extraction config: `extraction_configs/default.json` — edit to change fields/prompts without code changes
- To run locally: `cd` to project, `OAUTHLIB_INSECURE_TRANSPORT=1 venv/bin/flask --app wsgi run`
