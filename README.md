# Job Agent

Discover matching AI/backend roles, tailor your resume with JD keywords (without inventing experience), and queue every application for one-click approval before any portal submit.

**Nothing applies until you approve it in the queue UI.**

## Features

- Resume parser (PDF/DOCX → structured profile)
- Portal discovery adapters: **Naukri**, **Instahyre**, **LinkedIn**, **Workday**
- Heuristic matcher (+ optional OpenAI embeddings boost)
- Resume tailor with **PDF + unified diff**
- FastAPI **approval queue** (Approve / Skip)
- Playwright apply automation with account creation (**Naukri** / **Instahyre** live; **LinkedIn** / **Workday** stubbed with the same interface)
- Gmail OAuth helpers for OTP + reply tracking
- Daily scheduler + SQLite tracking

## Requirements

- Python 3.11+
- (Optional) Playwright browsers for live apply
- (Optional) OpenAI API key for embedding boost
- (Optional) Gmail OAuth client secrets for OTP/replies

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
playwright install chromium   # only needed for live browser apply

cp .env.example .env
# edit .env — never commit real secrets

# Upload your resume (PDF or DOCX). Contents of resume/ are gitignored.
cp /path/to/your-resume.pdf resume/

job-agent init-db
job-agent run-once          # discover → score → tailor → enqueue
job-agent queue             # open http://127.0.0.1:8080
```

Daily scheduler (blocking):

```bash
job-agent scheduler
```

## Configuration

Copy `.env.example` to `.env`. Important knobs:

| Variable | Purpose |
|---|---|
| `ROLE_KEYWORDS` | Target roles/skills |
| `LOCATIONS` / `REMOTE_OK` | Location filter |
| `MATCH_SCORE_THRESHOLD` | Minimum score to tailor/enqueue |
| `MATCH_KEYWORD_STUFF_CAP` | Cap on JD keyword emphasis |
| `OPENAI_API_KEY` | Optional embedding boost |
| `NAUKRI_*` / `INSTAHYRE_*` | Portal credentials for live apply |
| `LINKEDIN_*` / `WORKDAY_*` | Reserved for later live apply |
| `GMAIL_CREDENTIALS_PATH` | OAuth client secrets JSON |
| `MAX_DAILY_APPLIES` | Safety cap |

## Portal notes

### Discovery

Adapters try a live HTML/API fetch first. If the portal blocks the request or markup does not match selectors, they fall back to **deterministic fixtures** so matcher/tailor/queue still work offline.

### Apply

| Portal | Account creation | Apply |
|---|---|---|
| Naukri | Implemented (Playwright) | Implemented; pauses on CAPTCHA/2FA |
| Instahyre | Implemented (Playwright) | Implemented; pauses on CAPTCHA/2FA |
| LinkedIn | Stubbed (same interface) | Stubbed — manual after approval |
| Workday | Stubbed (same interface) | Stubbed — manual after approval |

Login URLs and selectors live under `src/job_agent/constants/portals.py` and the apply adapters. Persistent browser sessions are stored in `sessions/` (gitignored).

### Gmail

1. Create an OAuth desktop client in Google Cloud Console.
2. Save the client JSON to the path in `GMAIL_CREDENTIALS_PATH`.
3. First use of OTP/send opens a local consent flow and writes `GMAIL_TOKEN_PATH`.

## Project layout

```
src/job_agent/
  resume/       # PDF/DOCX parser
  sources/      # portal discovery adapters
  matcher/      # scoring
  tailor/       # rewrite + PDF + diff
  apply/        # Playwright apply adapters
  gmail/        # OAuth send / OTP / replies
  queue/        # FastAPI approval UI
  scheduler/    # daily pipeline
  db/ models/ constants/ config
resume/         # upload your resume here (gitignored)
tailored/       # generated PDFs/diffs (gitignored)
data/           # SQLite (gitignored)
sessions/       # Playwright profiles (gitignored)
```

## Development

```bash
ruff check src tests
ruff format src tests
pytest -q
```

CI runs lint + unit tests on PRs (see `.github/workflows/ci.yml`).

## Safety

- Credentials only via env / local OAuth files — never commit them
- Resume uploads are gitignored
- Human-like `slow_mo`, persistent sessions, and daily apply caps
- CAPTCHA / 2FA → apply pauses and the queue shows the reason
- Tailoring only reorders/rephrases evidenced experience; keyword stuffing is capped and shown in the diff
