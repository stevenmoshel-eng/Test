import time

import config
import storage
import summarizer
import telegram_collector


def main():
    storage.init_db()
    while True:
        print("Fetching new posts...")
        telegram_collector.fetch_all_channels()

        print("Summarizing new posts...")
        summarizer.summarize_new_posts()

        print(f"Done. Sleeping {config.COLLECTOR_INTERVAL_SECONDS}s...")
        time.sleep(config.COLLECTOR_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
