from datetime import datetime, timedelta, timezone

from telethon.sync import TelegramClient

import config
import storage


def fetch_all_channels():
    client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)
    client.start()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    try:
        for channel in config.load_channels():
            for message in client.iter_messages(channel):
                if message.date < cutoff:
                    break
                if message.text:
                    storage.insert_post(channel, message.id, message.date.isoformat(), message.text)
    finally:
        client.disconnect()


if __name__ == "__main__":
    storage.init_db()
    fetch_all_channels()
