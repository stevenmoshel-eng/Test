import anthropic

import config
import storage

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def summarize_new_posts():
    for post in storage.get_unsummarized_posts():
        summary = _summarize_text(post["text"])
        storage.set_summary(post["id"], summary)


def _summarize_text(text):
    response = _client.messages.create(
        model=config.SUMMARY_MODEL,
        max_tokens=150,
        messages=[
            {
                "role": "user",
                "content": (
                    "Summarize this Telegram news post in 1-2 concise, factual "
                    "sentences. No preamble, just the summary:\n\n" + text
                ),
            }
        ],
    )
    return response.content[0].text.strip()


if __name__ == "__main__":
    summarize_new_posts()
