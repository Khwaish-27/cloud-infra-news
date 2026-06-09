# Cloud & Infra News Digest

A local, **zero-API-key** pipeline that pulls tech news daily, classifies it by keyword
(Cloud Infrastructure, Networks, Cybersecurity, GRC, Data Centres), writes a 3–4 line
summary for each story, and builds a self-contained `index.html` dashboard. A Windows
scheduler can run it automatically every morning.

No keys. No cloud. No database. Just Python + flat files + one HTML page.

---

## Quick start

1. **Install Python 3.11+** (https://python.org) — tick "Add Python to PATH" during install.
2. Open this folder in VS Code, then open a terminal (`Ctrl+` `).
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. (One-time) download the sentence tokenizer that `sumy` needs:
   ```
   python -m nltk.downloader punkt punkt_tab
   ```
5. Run it:
   ```
   python run.py
   ```
6. Open the generated **`index.html`** in your browser. Done.

Re-running `run.py` refreshes the data and rebuilds the page.

---

## How it works

```
sources.yaml ─► fetch.py ─► dedupe + recency ─► classify.py ─► summarize.py ─► render.py ─► index.html
                (RSS +                          (keywords)     (feed text /                 + data/archive/
                Google News)                                    sumy)
```

| File | Role |
|------|------|
| `sources.yaml` | RSS feeds + Google News keyword searches (edit freely, no key) |
| `categories.yaml` | Keyword lists per category |
| `fetch.py` | Pulls & normalizes all feeds, dedupes, filters to last 48h |
| `classify.py` | Assigns categories by keyword match (multi-label) |
| `summarize.py` | 3–4 line summary: feed text, upgraded to `sumy` extractive |
| `render.py` | Jinja2 → `index.html` |
| `run.py` | Runs the whole pipeline; writes `data/articles.json` + archive |
| `templates/index.html` | The dashboard (filters + search, dark theme) |
| `run.bat` | Entry point for Windows Task Scheduler |
| `run.log` | Per-run log (counts, errors) |

---

## Customising

- **Add/remove sources:** edit `sources.yaml`. Add a publisher RSS URL under `rss_feeds`,
  or a new keyword query under `google_news`.
- **Tune categories:** edit the keyword lists in `categories.yaml`.
- **Recency window / summary length:** change `RECENCY_HOURS` and `SUMMARY_SENTENCES`
  at the top of `run.py`.

---

## Schedule it (run daily, hands-free)

Windows Task Scheduler:

1. Open **Task Scheduler** → **Create Basic Task**.
2. Name it "Daily News Digest", trigger **Daily** at your preferred time (e.g. 7:00 AM).
3. Action: **Start a program** → Program/script: browse to **`run.bat`** in this folder.
4. Finish. (Optionally, in the task's properties, tick "Run whether user is logged on or not".)

Or register it from PowerShell (adjust the path):
```powershell
$action  = New-ScheduledTaskAction -Execute "C:\Users\Lenovo\Desktop\Cloud infra news site\run.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 7am
Register-ScheduledTask -TaskName "Daily News Digest" -Action $action -Trigger $trigger
```

---

## Troubleshooting

- **`sumy` / NLTK error about `punkt`:** run `python -m nltk.downloader punkt punkt_tab`.
  If it still fails, the pipeline automatically falls back to feed-text summaries — it
  won't crash.
- **A feed shows 0 items or an error in `run.log`:** that publisher's URL may have changed;
  remove or replace it in `sources.yaml`. The rest keep working.
- **Empty dashboard:** likely the 48h filter on a slow news day — raise `RECENCY_HOURS` in `run.py`.

---

## Roadmap (optional upgrades, all still free)

- Swap `sumy` for a local AI model (HuggingFace `distilbart-cnn` or Ollama `llama3.2`) for
  nicer abstractive summaries.
- Add an email digest of the day's top stories.
- Keep a searchable history page from the `data/archive/` snapshots.
