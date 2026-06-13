# AI Symptom Acquisition Audit™

A founder-operated CLI tool that measures how often gut health brands are recommended by AI models (Gemini), identifies which competitors dominate, and generates a sellable audit report in under 10 minutes.

> **This is not a SaaS product. It is an internal founder tool.**  
> One user. No web UI. No accounts. No server. Run it from your laptop.

---

## What it does

For any Shopify gut health brand, it generates:

| Section | What you learn |
|---|---|
| **Visibility Score** | How often the brand appears across 25 AI queries |
| **Competitor Capture** | Which brands dominate AI recommendations instead |
| **Citation Surface** | Which websites AI cites (Healthline, WebMD, Reddit…) |
| **Evidence Gaps** | Where the brand's authority signals are likely missing |
| **Quick Wins** | 10 prioritized actions to improve AI visibility |

Output: a Markdown report + JSON data file, ready to send to a client.

---

## Setup

**Requirements:** Python 3.11+, a Gemini API key (free tier works)

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd <repo-folder>

# 2. Install dependencies (only 2 packages)
pip install -r requirements.txt

# 3. Set your Gemini API key
export GEMINI_API_KEY="your-key-here"
# Get a free key at: https://aistudio.google.com/app/apikey
```

---

## Usage

### Run an audit

```bash
python main.py --brand "Begin Health" --url "https://beginhealth.com"
```

Output files:
```
reports/begin_health_audit.md    ← send this to the client
reports/begin_health_audit.json  ← raw structured data
```

### Custom prompt file

```bash
python main.py --brand "Seed" --url "seed.com" --prompts prompts.json
```

Edit `prompts.json` to add your own gut health queries.

### Run from a config file

```bash
python main.py config.json
```

`config.json` format:
```json
{
  "brand": "Pendulum",
  "url": "https://pendulum.life",
  "prompts": "prompts.json"
}
```

---

## Managing past reports

```bash
# See all past audits (ID, brand, date, file location)
python main.py --list

# Print any past report to the terminal
python main.py --read 3

# Re-export a past report from the database to reports/ folder
# (useful if you accidentally deleted the .md file)
python main.py --export 3
```

---

## Project structure

```
main.py              ← CLI entry point — the only file you need to run
prompts.json         ← gut health queries (edit freely)
models.py            ← Pydantic schemas: VisibilityResult, CitationResult, EvidenceGap, AuditReport
database.py          ← SQLite read/write helpers
modules/
  visibility.py      ← Module A: 5 prompts × 5 samples via Gemini
  competitors.py     ← Module B: brand frequency counting
  citations.py       ← Module C: URL/domain extraction from responses
  grounding.py       ← Module D: STATIC vs WEB signal classification
  evidence_gap.py    ← Module E: Gemini analysis at temperature=0
  report.py          ← Markdown report generator
reports/             ← generated .md and .json files (gitignored)
audit.db             ← SQLite history of all runs (gitignored)
data/                ← SQLite directory
```

---

## How long does it take?

| Step | Time |
|---|---|
| Module A (25 Gemini calls, 2.5s spacing) | ~65 seconds |
| Modules B–D (local processing) | <1 second |
| Module E (1 Gemini call, temperature=0) | ~5 seconds |
| Report generation | <1 second |
| **Total** | **~2–3 minutes** |
| Human review | ~10 minutes |

---

## Free tier limits

The tool uses `gemini-2.0-flash-lite` for bulk sampling (30 RPM / 1500 RPD free tier).  
Each full audit uses ~26 API calls — well within daily limits.

If you hit a quota error:
- Wait until midnight Pacific for the daily reset, **or**
- Enable billing on [Google AI Studio](https://aistudio.google.com) — cost per audit is under $0.01

---

## Constraints (intentional)

This tool deliberately avoids:

- ❌ Flask / FastAPI / any web framework
- ❌ LangChain / LangGraph / CrewAI / AutoGen
- ❌ Vector databases / embeddings / RAG
- ❌ Redis / Kafka / Celery / any queue
- ❌ Docker / Kubernetes / any cloud deployment
- ❌ Async architecture / multi-agent systems

Every line of code exists to generate a better audit report, faster. Nothing else.

---

## Target customer

- Shopify gut health brands (probiotics, digestive health, prebiotics)
- Founder-led, 5–20 employees
- Examples: Seed, Bioma, BelliWelli, Begin Health, Pendulum

---

## License

Internal founder tool. Not for redistribution.
