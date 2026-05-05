import json
import time
import requests
import os

SKOOL_API = "https://www.skool.com/api/coderco/posts"
GITHUB_DISPATCH_URL = "https://api.github.com/repos/moabukar/cv-reviewer/dispatches"
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
POLL_INTERVAL = 10

seen_ids = set()


def check_posts():
    response = requests.get(SKOOL_API)
    response.raise_for_status()
    posts = response.json()

    for item in posts:
        post = item.get("post_tree", {}).get("post", {})
        metadata = post.get("metadata", {})

        post_id = post.get("id")
        first_name = post.get("user", {}).get("first_name")
        title = metadata.get("title", "")

        try:
            attachments = json.loads(metadata.get("attachments_data", "[]"))
            read_url = attachments[0]["metadata"]["read_url"]
        except (IndexError, KeyError, json.JSONDecodeError):
            continue

        if not all([post_id, read_url, first_name]):
            continue

        if "CV Review" not in title or post_id in seen_ids:
            continue

        seen_ids.add(post_id)

        requests.post(
            GITHUB_DISPATCH_URL,
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            json={
                "event_type": "cv-review",
                "client_payload": {
                    "post_id": post_id,
                    "read_url": read_url,
                    "first_name": first_name,
                    "title": title,
                },
            },
        ).raise_for_status()

        print(f"Dispatched CV Review for post {post_id} by {first_name}")


if __name__ == "__main__":
    while True:
        check_posts()
        time.sleep(POLL_INTERVAL)
