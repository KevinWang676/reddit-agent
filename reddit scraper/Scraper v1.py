
import os
import csv
import json
import time
import math
import pathlib
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
import praw
from prawcore import RequestException, ResponseException, Forbidden, ServerError
from tqdm import tqdm

# SUBREDDITS = ["malefashionadvice", "femalefashionadvice", "streetwear"]

SUBREDDITS = [
    "malefashionadvice",
    "femalefashionadvice",
    "streetwear",
    "frugalmalefashion",
    "frugalfemalefashion",
    "sneakers",
    "rawdenim",
    "fashion",
    "SustainableFashion",
    "PlusSizeFashion"
]


MONTHS_BACK = 24  # rolling window
MIN_SCORE = 50    # adjust popularity threshold here (e.g., 0, 25, 50, 100...)
MIN_NUM_COMMENTS = 0  # optional comment-count threshold; set >0 if you want

FETCH_ALL_COMMENTS = True         # get full comment tree
INCREMENTAL_RESUME = True         # skip already-saved submissions by id
OUTPUT_DIR = "reddit_fashion_out" # where files go
POSTS_JSONL = "posts.jsonl"       # full data
POSTS_CSV = "posts_summary.csv"   # summary
SEEN_IDS_FILE = "seen_ids.txt"    # for resume (one id per line)
LOG_EVERY = 50                    # print/log every N posts processed

# -----------------------------
# Auth & init
# -----------------------------
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USER_AGENT = os.getenv("USER_AGENT")

if not all([CLIENT_ID, CLIENT_SECRET, USER_AGENT]):
    raise RuntimeError("Missing CLIENT_ID, CLIENT_SECRET, or USER_AGENT in .env")

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
    check_for_async=False
)

# Confirm we’re in read-only mode
print("Logged in as:", reddit.user.me())  # → should print None in read-only

# -----------------------------
# Helpers
# -----------------------------
def ensure_dir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def backoff_sleep(attempt):
    # capped exponential backoff with a little jitter
    delay = min(60, (2 ** attempt)) + 0.25 * attempt
    time.sleep(delay)

def load_seen_ids(path):
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def append_seen_id(path, subm_id):
    with open(path, "a", encoding="utf-8") as f:
        f.write(subm_id + "\n")

def make_paths_for_subreddit(base_dir, sub):
    sub_dir = os.path.join(base_dir, sub)
    ensure_dir(sub_dir)
    return (
        os.path.join(sub_dir, POSTS_JSONL),
        os.path.join(sub_dir, POSTS_CSV),
        os.path.join(sub_dir, SEEN_IDS_FILE),
    )

def write_csv_header_if_needed(csv_path):
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            w = csv.writer(cf)
            w.writerow([
                "id", "created_iso", "subreddit",
                "title", "author",
                "score", "num_comments",
                "link_flair_text", "over_18",
                "is_self"
            ])

def submission_to_post_dict(s):
    return {
        "id": s.id,
        "subreddit": str(s.subreddit),
        "created_utc": int(s.created_utc),
        "created_iso": datetime.fromtimestamp(s.created_utc, tz=timezone.utc).isoformat(),
        "title": s.title,
        "selftext": s.selftext,
        "author": str(s.author) if getattr(s, "author", None) else None,
        "score": int(s.score),
        "upvote_ratio": s.upvote_ratio if hasattr(s, "upvote_ratio") else None,
        "num_comments": int(s.num_comments),
        "link_flair_text": s.link_flair_text,
        "over_18": bool(getattr(s, "over_18", False)),
        "is_self": bool(getattr(s, "is_self", False)),
        # No URLs/media per your request
        # "url": s.url,
        # "permalink": f"https://reddit.com{s.permalink}",
        "removed_by": getattr(s, "removed_by_category", None),
        "edited": bool(getattr(s, "edited", False)),
        "distinguished": getattr(s, "distinguished", None),
        "stickied": bool(getattr(s, "stickied", False)),
        "awards": [
            {
                "name": a["name"],
                "count": a["count"],
            } for a in getattr(s, "all_awardings", [])
        ],
    }

def fetch_all_comments(submission):
    """
    Expand full comment tree (can be heavy).
    Returns a flat list of dicts; you can post-process into a tree if you like.
    """
    # replace_more(limit=None) can be very slow on huge threads; consider limit=0 if you ever need to trim
    submission.comments.replace_more(limit=None)
    out = []
    for c in submission.comments.list():
        out.append({
            "id": c.id,
            "link_id": c.link_id,         # t3_<postid>
            "parent_id": c.parent_id,     # t1_<commentid> or t3_<postid>
            "author": str(c.author) if getattr(c, "author", None) else None,
            "body": c.body,
            "score": int(getattr(c, "score", 0) or 0),
            "created_utc": int(c.created_utc),
            "created_iso": datetime.fromtimestamp(c.created_utc, tz=timezone.utc).isoformat(),
            "is_submitter": bool(getattr(c, "is_submitter", False)),
            "stickied": bool(getattr(c, "stickied", False)),
            "distinguished": getattr(c, "distinguished", None),
        })
    return out

def process_subreddit(subreddit_name, cutoff_utc):
    """
    Iterate subreddit.new() until we either exhaust listings or reach older-than-cutoff posts.
    Save records meeting popularity thresholds; optionally skip IDs we've seen already.
    """
    sub_dir = os.path.join(OUTPUT_DIR, subreddit_name)
    ensure_dir(sub_dir)
    jsonl_path, csv_path, seen_path = make_paths_for_subreddit(OUTPUT_DIR, subreddit_name)
    write_csv_header_if_needed(csv_path)

    seen_ids = load_seen_ids(seen_path) if INCREMENTAL_RESUME else set()

    attempt = 0
    processed = 0
    saved = 0
    too_old_hit = False

    # Open files once for efficiency
    jsonl_f = open(jsonl_path, "a", encoding="utf-8")
    csv_f = open(csv_path, "a", newline="", encoding="utf-8")
    csv_w = csv.writer(csv_f)

    try:
        # PRAW generators handle pagination internally; limit=None asks for as many as API allows.
        submissions = reddit.subreddit(subreddit_name).new(limit=None)

        with tqdm(desc=f"r/{subreddit_name}", unit="post") as pbar:
            for subm in submissions:
                processed += 1
                pbar.update(1)

                # Stop if older than cutoff
                if int(subm.created_utc) < cutoff_utc:
                    too_old_hit = True
                    break

                # Incremental skip
                if INCREMENTAL_RESUME and subm.id in seen_ids:
                    continue

                # Popularity thresholds
                if subm.score < MIN_SCORE:
                    continue
                if MIN_NUM_COMMENTS > 0 and subm.num_comments < MIN_NUM_COMMENTS:
                    continue

                # Hydrate post
                # (If you want 'suppress_warning=True' to avoid PRAW prints, you can pass in reddit=... param)
                post_rec = submission_to_post_dict(subm)

                # Fetch comments if requested
                comments = []
                if FETCH_ALL_COMMENTS:
                    c_attempt = 0
                    while True:
                        try:
                            comments = fetch_all_comments(subm)
                            break
                        except (RequestException, ResponseException, Forbidden, ServerError) as e:
                            c_attempt += 1
                            if c_attempt > 6:
                                print(f"[WARN] Comments failed for {subm.id}: {e}")
                                comments = []
                                break
                            backoff_sleep(c_attempt)

                post_rec["comments"] = comments

                # Write JSONL
                jsonl_f.write(json.dumps(post_rec, ensure_ascii=False) + "\n")

                # Write CSV summary
                csv_w.writerow([
                    post_rec["id"],
                    post_rec["created_iso"],
                    post_rec["subreddit"],
                    post_rec["title"],
                    post_rec["author"],
                    post_rec["score"],
                    post_rec["num_comments"],
                    post_rec["link_flair_text"],
                    post_rec["over_18"],
                    post_rec["is_self"],
                ])

                saved += 1
                if INCREMENTAL_RESUME:
                    append_seen_id(seen_path, subm.id)

                if saved % LOG_EVERY == 0:
                    print(f"[{subreddit_name}] processed={processed} saved={saved}")

    except (RequestException, ResponseException, Forbidden, ServerError) as e:
        attempt += 1
        print(f"[ERROR] API issue on r/{subreddit_name}: {e}")
        backoff_sleep(attempt)
    finally:
        jsonl_f.close()
        csv_f.close()

    return {
        "subreddit": subreddit_name,
        "processed": processed,
        "saved": saved,
        "cutoff_reached": too_old_hit
    }

# -----------------------------
# Main
# -----------------------------
def main():
    ensure_dir(OUTPUT_DIR)
    now = datetime.now(tz=timezone.utc)
    cutoff_dt = now - timedelta(days=30 * MONTHS_BACK)
    # slightly more precise: 730 days for 24 months, but 30*MONTHS works fine for rolling window
    cutoff_utc = int(cutoff_dt.timestamp())

    print(f"Time window: {cutoff_dt.date()} → {now.date()} (UTC)")
    print(f"Filters: MIN_SCORE={MIN_SCORE}, MIN_NUM_COMMENTS={MIN_NUM_COMMENTS}, FETCH_ALL_COMMENTS={FETCH_ALL_COMMENTS}")
    print(f"Incremental resume: {INCREMENTAL_RESUME}")
    print("-" * 60)

    totals = []
    for sub in SUBREDDITS:
        stats = process_subreddit(sub, cutoff_utc)
        totals.append(stats)
        print(f"Done r/{sub}: processed={stats['processed']} saved={stats['saved']} cutoff_reached={stats['cutoff_reached']}")

    print("-" * 60)
    grand_saved = sum(t["saved"] for t in totals)
    print(f"All done. Total posts saved: {grand_saved}")
    print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    main()