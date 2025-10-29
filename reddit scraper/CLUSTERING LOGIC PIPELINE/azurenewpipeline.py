
"""
Reddit Insight Evolution Pipeline (Azure OpenAI)
------------------------------------------------
Workflow:
1. Scrape new posts
2. Summarize posts
3. Categorize summaries into fixed categories
4. Dynamically cluster summaries (threshold-based)
5. Generate one insight per cluster
6. Save all results and Markdown report
"""

import os
import re
import json
import time
import praw
import numpy as np
from numpy.linalg import norm
from tqdm import tqdm
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from sklearn.cluster import AgglomerativeClustering
from openai import AzureOpenAI

# ==============================================================
# CONFIGURATION
# ==============================================================

load_dotenv()

# Reddit credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USER_AGENT = os.getenv("USER_AGENT", "python:RedditPipeline:v4.0")

# Azure OpenAI credentials
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "embedding-small-v1")

# Initialize client
openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2025-01-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)
print(f"✓ Azure OpenAI initialized with deployments: {AZURE_DEPLOYMENT} / {AZURE_EMBEDDING_DEPLOYMENT}")

# Global defaults
OUTPUT_DIR = "pipeline_output"
MONTHS_BACK = 12
MIN_SCORE = 50

FIXED_CATEGORIES = [
    "Product Efficacy & Usage",
    "Purchase Drivers & Intent",
    "Customer Journey Stage",
    "Experience Friction"
]

# ==============================================================
# UTILITIES
# ==============================================================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def safe_llm_call(fn, retries=3, delay=3):
    """Retry wrapper for LLM calls."""
    for i in range(retries):
        try:
            return fn()
        except Exception as e:
            print(f"⚠️ LLM call failed ({i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise

# ==============================================================
# STEP 1 — SCRAPE SUBREDDIT
# ==============================================================

def scrape_subreddit(subreddit, cutoff_utc, max_posts=None):
    print(f"\n{'='*60}\nSTEP 1: Scraping r/{subreddit}\n{'='*60}")
    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT
    )

    posts = []
    for subm in tqdm(reddit.subreddit(subreddit).new(limit=None), desc="Scraping posts"):
        if subm.score < MIN_SCORE:
            continue
        if int(subm.created_utc) < cutoff_utc:
            continue
        post = {
            "id": subm.id,
            "title": subm.title,
            "selftext": subm.selftext or "",
            "score": subm.score,
            "num_comments": subm.num_comments,
            "created_utc": subm.created_utc,
            "created_iso": datetime.fromtimestamp(subm.created_utc).isoformat(),
            "permalink": f"https://reddit.com{subm.permalink}",
        }
        posts.append(post)
        if max_posts and len(posts) >= max_posts:
            break

    print(f"✓ Scraped {len(posts)} posts from r/{subreddit}")
    return posts

# ==============================================================
# STEP 2 — SUMMARIZE POSTS
# ==============================================================

def summarize_post(post):
    """Generate concise summary."""
    prompt = f"Summarize this Reddit post in 2–3 sentences:\n\nTitle: {post['title']}\n\n{post['selftext']}"
    def call():
        resp = openai_client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an expert summarizer capturing key ideas and sentiment."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=120
        )
        return resp.choices[0].message.content.strip()
    return safe_llm_call(call)

def summarize_posts(posts):
    print(f"\n{'='*60}\nSTEP 2: Summarizing Posts\n{'='*60}")
    summarized = []
    for p in tqdm(posts, desc="Summarizing"):
        summary = summarize_post(p)
        p["summary"] = summary
        summarized.append(p)
        time.sleep(0.3)
    print(f"✓ Generated summaries for {len(summarized)} posts")
    return summarized

# ==============================================================
# STEP 3 — CATEGORIZE SUMMARIES
# ==============================================================

def categorize_post(post, categories):
    cats = "\n".join([f"{i+1}. {c}" for i, c in enumerate(categories)])
    prompt = f"""
    Categorize the following Reddit post summary into one of these categories:
    {cats}

    Post Summary:
    "{post['summary']}"

    Respond with only the category name.
    """
    def call():
        resp = openai_client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a precise text classifier."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=30
        )
        return resp.choices[0].message.content.strip()
    return safe_llm_call(call)

def categorize_posts(posts, categories):
    print(f"\n{'='*60}\nSTEP 3: Categorizing Summaries\n{'='*60}")
    for p in tqdm(posts, desc="Categorizing"):
        cat = categorize_post(p, categories)
        p["category"] = cat if cat in categories else "Uncategorized"
        time.sleep(0.2)
    print("✓ Categorization complete")
    return posts

# ==============================================================
# STEP 4 — DYNAMIC THRESHOLD-BASED CLUSTERING
# ==============================================================

def text_embed(text):
    """Generate embedding using Azure OpenAI."""
    emb = openai_client.embeddings.create(
        model=AZURE_EMBEDDING_DEPLOYMENT,
        input=text
    )
    return np.array(emb.data[0].embedding)

def generate_insights_threshold(posts, categories, similarity_threshold=0.75, min_cluster_size=2):
    """
    Cluster post summaries per category using cosine similarity threshold,
    then generate one insight per cluster.
    """
    print(f"\n{'='*60}\nSTEP 4: Threshold-Based Semantic Clustering\n{'='*60}")
    insights_db = {}

    for cat in categories:
        cat_posts = [p for p in posts if p.get("category") == cat]
        if not cat_posts:
            continue

        summaries = [p["summary"] for p in cat_posts]
        embeddings = np.vstack([text_embed(s) for s in summaries])

        distance_threshold = 1 - similarity_threshold
        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric="cosine",
            linkage="average",
            distance_threshold=distance_threshold
        ).fit(embeddings)

        labels = clustering.labels_
        unique_labels = set(labels)
        print(f"→ {cat}: formed {len(unique_labels)} clusters")

        cat_insights = []
        for cluster_id in unique_labels:
            cluster_posts = [cat_posts[i] for i, lbl in enumerate(labels) if lbl == cluster_id]
            if len(cluster_posts) < min_cluster_size:
                continue  # skip tiny/noisy clusters

            cluster_summaries = [p["summary"] for p in cluster_posts]
            combined = "\n".join([f"- ({p['created_iso'][:10]}, score={p['score']}) {p['summary']}" for p in cluster_posts[:25]])

            prompt = f"""
            You are a market insights analyst evaluating Reddit discussions within the category: {cat}.
            Each post includes its creation date and engagement metrics (score = upvotes).

            Your task:
            1. Identify key recurring themes, pain points, or motivations across time.
            2. Detect whether certain topics are increasing or decreasing in frequency or sentiment.
            3. Highlight any time-based trends (e.g., "recent posts show growing frustration about...").
            4. Translate these into 1–3 actionable insights or strategic recommendations for product or marketing teams.
            5. Include specific evidence from the data.

            Return your response in this structure:

            **Observed Trend(s) Over Time:**
            - ...

            **Evolving User Sentiment:**
            - ...

            **Underlying Drivers:**
            - ...

            **Actionable Recommendations:**
            - ...

            **Evidence & Examples:**
            - Mention 1–2 dated examples with upvotes to support your findings.

            Posts to analyze (each line shows date and engagement):
            {combined}
            """

            def call():
                resp = openai_client.chat.completions.create(
                    model=AZURE_DEPLOYMENT,
                    messages=[
                        {"role": "system", "content": "You are an expert analyst summarizing discussion clusters."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,
                    max_tokens=800
                )
                return resp.choices[0].message.content.strip()

            insight_text = safe_llm_call(call)

            cat_insights.append({
                "id": f"{cat[:4].lower()}_{cluster_id+1:02}",
                "category": cat,
                "summary": insight_text,
                "linked_posts": [p["id"] for p in cluster_posts],
                "last_updated": datetime.now().isoformat()
            })

        insights_db[cat] = cat_insights

    print("✓ Dynamic threshold-based insights generated")
    return insights_db

# ==============================================================
# STEP 5 — SAVE OUTPUTS
# ==============================================================

def save_outputs(subreddit, posts, insights):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subdir = os.path.join(OUTPUT_DIR, f"{subreddit}_{timestamp}")
    ensure_dir(subdir)

    with open(os.path.join(subdir, "posts.jsonl"), "w", encoding="utf-8") as f:
        for p in posts:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with open(os.path.join(subdir, "insights.json"), "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)

    report_path = os.path.join(subdir, "REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Reddit Analysis Report: r/{subreddit}\n\nGenerated: {datetime.now()}\n\n")
        for cat, ins_list in insights.items():
            f.write(f"## {cat}\n\n")
            for ins in ins_list:
                f.write(f"### {ins['id']}\n{ins['summary']}\n\n")
                f.write(f"Linked Posts: {', '.join(ins['linked_posts'])}\n\n")
    print(f"✅ Results saved to {subdir}")

# ==============================================================
# MAIN RUNNER
# ==============================================================

def run_pipeline(subreddit, max_posts=None):
    now = datetime.now(tz=timezone.utc)
    cutoff_dt = now - timedelta(days=30 * MONTHS_BACK)
    cutoff_utc = int(cutoff_dt.timestamp())

    posts = scrape_subreddit(subreddit, cutoff_utc, max_posts)
    summarized = summarize_posts(posts)
    categorized = categorize_posts(summarized, FIXED_CATEGORIES)
    insights = generate_insights_threshold(
        categorized, FIXED_CATEGORIES, similarity_threshold=0.6, min_cluster_size=3
    )
    save_outputs(subreddit, categorized, insights)
    print("🎯 Pipeline completed successfully!")

if __name__ == "__main__":
    run_pipeline("MakeupAddiction", max_posts=500)
