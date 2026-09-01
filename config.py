import os

from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

SESSION_NAME = os.environ.get("TELEGRAM_SESSION_NAME", "israel_news_session")
SUMMARY_MODEL = os.environ.get("SUMMARY_MODEL", "claude-haiku-4-5-20251001")
COLLECTOR_INTERVAL_SECONDS = int(os.environ.get("COLLECTOR_INTERVAL_SECONDS", 15 * 60))

CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "channels.txt")
DB_PATH = os.path.join(os.path.dirname(__file__), "posts.db")


def load_channels():
    with open(CHANNELS_FILE) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]
