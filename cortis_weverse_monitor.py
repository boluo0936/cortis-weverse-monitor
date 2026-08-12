"""
Cortis Weverse monitor (cloud edition) - runs on GitHub Actions.
Detects new artist posts / lives on CORTIS's Weverse community and
pushes notifications to WeChat via PushPlus.

- Runs every 15 min via GitHub Actions cron.
- State (seen post/live IDs) is persisted in seen.json and committed
  back to the repo by the workflow, so the next run only reports NEW items.
- Requires repo secret: PUSHPLUS_TOKEN (from https://www.pushplus.plus/)
"""
import json
import os
import re
import sys
import time
import urllib.request

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen.json")
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
UA = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
BASE = "https://weverse.io/cortis"


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"posts": [], "lives": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def extract_posts(html):
    items = []
    for m in re.finditer(r'href="(https://weverse\.io/cortis/artist/(\d+)-(\d+))"[^>]*>\s*([^<]{1,200})', html):
        url, member_id, post_id, text = m.groups()
        text = re.sub(r"&[a-z]+;", " ", text).strip()
        items.append({"member_id": member_id, "post_id": post_id, "url": url, "preview": text})
    seen = set()
    out = []
    for it in items:
        if it["post_id"] not in seen:
            seen.add(it["post_id"])
            out.append(it)
    return out


def extract_lives(html):
    items = []
    for m in re.finditer(r'href="(https://weverse\.io/cortis/live/(\d+)-(\d+))"', html):
        url, artist_id, live_id = m.groups()
        items.append({"url": url, "live_id": live_id})
    seen = set()
    out = []
    for it in items:
        if it["live_id"] not in seen:
            seen.add(it["live_id"])
            out.append(it)
    return out


def post_author(html):
    m = re.search(r'"@type":"Article".{0,3000}?"author":\[\{"@type":"Person","name":"([^"]+)"', html, re.S)
    name = m.group(1) if m else None
    m2 = re.search(r'"headline":"([^"]+)"', html)
    headline = m2.group(1) if m2 else None
    m3 = re.search(r'"datePublished":"([^"]+)"', html)
    date = m3.group(1) if m3 else None
    return name, headline, date


def pushplus(title, content):
    """Send WeChat push via PushPlus. Returns True on success."""
    if not PUSHPLUS_TOKEN:
        print(f"[pushplus] no token, skipped: {title}", file=sys.stderr)
        return False
    body = json.dumps({"token": PUSHPLUS_TOKEN, "title": title, "content": content, "template": "markdown"})
    req = urllib.request.Request(
        "https://www.pushplus.plus/send",
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read().decode("utf-8"))
        ok = resp.get("code") == 200
        print(f"[pushplus] {'OK' if ok else 'FAILED'}: {resp.get('msg')}")
        return ok
    except Exception as e:
        print(f"[pushplus] error: {e}", file=sys.stderr)
        return False


def main():
    state = load_state()
    seen_posts = set(state.get("posts", []))
    seen_lives = set(state.get("lives", []))
    new_posts = []
    new_lives = []

    # --- Artist posts ---
    try:
        html = fetch(f"{BASE}/artist")
    except Exception as e:
        sys.stderr.write(f"artist page error: {e}\n")
        html = None

    if html:
        for it in extract_posts(html):
            if it["post_id"] not in seen_posts:
                new_posts.append(it)

        for it in new_posts:
            try:
                detail = fetch(it["url"])
                author, headline, date = post_author(detail)
                it["author"] = author or "未知成员"
                it["headline"] = headline or it["preview"]
                it["date"] = (date or "")[:16].replace("T", " ")
            except Exception as e:
                it["author"] = "未知成员"
                it["headline"] = it["preview"]
                it["date"] = ""

    # --- Lives ---
    try:
        lhtml = fetch(f"{BASE}/live")
    except Exception as e:
        sys.stderr.write(f"live page error: {e}\n")
        lhtml = None

    if lhtml:
        for it in extract_lives(lhtml):
            if it["live_id"] not in seen_lives:
                new_lives.append(it)

    # --- Persist state (workflow commits it back) ---
    for it in new_posts:
        seen_posts.add(it["post_id"])
    for it in new_lives:
        seen_lives.add(it["live_id"])
    state["posts"] = list(seen_posts)
    state["lives"] = list(seen_lives)
    save_state(state)

    # --- Notify for each new item ---
    for it in new_posts:
        title = f"Cortis Weverse 新帖 - {it['author']}"
        content = (
            f"**发帖人：{it['author']}**\n\n"
            f"{it['headline'][:200]}\n\n"
            f"时间: {it['date']}\n\n"
            f"[查看原帖]({it['url']})"
        )
        print(f"NEW POST by {it['author']}: {it['headline'][:80]}")
        pushplus(title, content)

    for it in new_lives:
        title = "Cortis Weverse 直播提醒"
        content = f"**Cortis 开直播了！**\n\n[点击进入直播间]({it['url']})"
        print(f"NEW LIVE: {it['url']}")
        pushplus(title, content)

    if not new_posts and not new_lives:
        print("no new items")


if __name__ == "__main__":
    main()
