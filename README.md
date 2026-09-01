# News Feed Dashboard

Monitors a set of Telegram channels and shows a rolling 24-hour feed of
AI-summarized posts on a local webpage.

**How it works:** a collector logs into your Telegram account (via Telethon)
and pulls the last 24 hours of posts from each channel in `channels.txt`,
summarizes new posts with Claude, and stores everything in a local SQLite
database (`posts.db`). A small Flask app reads that database and displays
the feed at `http://localhost:5001`.

Two processes, run in two terminal tabs:
- `run_collector_loop.py` — fetches + summarizes on a timer, keep it running.
- `app.py` — serves the dashboard webpage.

## Setup

1. **Install dependencies** (in the same virtual environment you already
   created for `feed.py`, e.g. `israel-news-env`):
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure credentials.** Copy the example env file and fill in your
   own values — never commit this file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set:
   - `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` — from https://my.telegram.org
   - `ANTHROPIC_API_KEY` — from https://console.anthropic.com

   If you already have an authenticated Telethon session file from `feed.py`
   (`israel_news_session.session`), copy it into this project folder and it
   will be reused — no need to log in again. Otherwise the first run will
   prompt you for your phone's login code, same as before.

3. **Add your channels.** Edit `channels.txt` — one channel username per
   line (the part after `t.me/`, no `@`). You can add or remove channels at
   any time; the collector picks up changes on its next cycle.

4. **Run the collector** (leave this running):
   ```bash
   python3 run_collector_loop.py
   ```

5. **Run the dashboard** (in a second terminal tab):
   ```bash
   python3 app.py
   ```
   Then open http://localhost:5001 in your browser.

## Notes

- `posts.db` and your `.session` file are gitignored — they contain your
  data and an authenticated Telegram login, and must never be committed or
  shared.
- The dashboard auto-refreshes every 60 seconds.
- Summaries are generated once per post and cached in the database, so
  re-running the collector doesn't re-summarize old posts.
- To adjust how often the collector checks Telegram, set
  `COLLECTOR_INTERVAL_SECONDS` in `.env` (default: 900 = 15 minutes).
