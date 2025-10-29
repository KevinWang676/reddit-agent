#!/usr/bin/env python3
"""
Reddit Categorization & Insight Pipeline (Azure OpenAI version)
"""

import os
import re
import csv
import json
import time
import yaml
import praw
import random
import logging
import traceback
import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import AzureOpenAI

# ==============================================================
# CONFIGURATION
# ==============================================================

load_dotenv()

# Reddit credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USER_AGENT = os.getenv("USER_AGENT", "python:RedditPipeline:v1.0")

# Azure OpenAI credentials
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

# Initialize Azure OpenAI client
openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)
print(f"✓ Azure OpenAI initialized with deployment: {AZURE_DEPLOYMENT}")

# Pipeline defaults
MONTHS_BACK = 24
MIN_SCORE = 0
MIN_NUM_COMMENTS = 0
NUM_CATEGORIES = 8
OUTPUT_DIR = "pipeline_output"


# ==============================================================
# UTILITY FUNCTIONS
# ==============================================================

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def safe_llm_call(fn, retries=3, delay=3):
    """Retry wrapper for LLM calls."""
    for i in range(retries):
        try:
            return fn()
        except Exception as e:
            print(f"⚠️ LLM call failed (attempt {i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise


# ==============================================================
# STEP 1 — SCRAPE SUBREDDIT
# ==============================================================

def scrape_subreddit(subreddit_name: str, cutoff_utc: int, max_posts: Optional[int] = None) -> List[Dict]:
    print(f"\n{'='*60}\nSTEP 1: Scraping subreddit '{subreddit_name}'\n{'='*60}")
    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT
    )

    subreddit = reddit.subreddit(subreddit_name)
    posts = []
    for submission in tqdm(subreddit.new(limit=None), desc="Fetching posts"):
        if submission.created_utc < cutoff_utc:
            break
        if submission.score < MIN_SCORE or submission.num_comments < MIN_NUM_COMMENTS:
            continue

        post = {
            "id": submission.id,
            "created_utc": submission.created_utc,
            "created_iso": datetime.fromtimestamp(submission.created_utc).isoformat(),
            "title": submission.title,
            "selftext": submission.selftext or "",
            "author": str(submission.author),
            "score": submission.score,
            "num_comments": submission.num_comments,
            "link_flair_text": submission.link_flair_text or "",
            "permalink": f"https://reddit.com{submission.permalink}"
        }
        posts.append(post)

        if max_posts and len(posts) >= max_posts:
            break

    print(f"✓ Scraped {len(posts)} posts from r/{subreddit_name}")
    return posts


# ==============================================================
# STEP 2 — GENERATE CATEGORIES
# ==============================================================

def generate_categories(posts: List[Dict], num_categories: int, predefined_categories: Optional[List[str]] = None) -> List[str]:
    print(f"\n{'='*60}\nSTEP 2: Category Generation\n{'='*60}")

    if predefined_categories:
        print("Using predefined categories.")
        return predefined_categories

    sample_posts = random.sample(posts, min(len(posts), 100))
    sample_text = "\n\n".join([p['title'] + "\n" + p['selftext'][:200] for p in sample_posts])

    prompt = f"""
    Based on the Reddit posts below, generate {num_categories} distinct, meaningful, and concise category names.
    Return only one category per line.

    Posts:
    {sample_text}
    """

    def call_openai():
        response = openai_client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an expert content analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()

    raw = safe_llm_call(call_openai)
    categories = [re.sub(r"^[\d\.\-\)]+", "", c).strip() for c in raw.split("\n") if c.strip()]
    print(f"✓ Generated {len(categories)} categories")
    return categories[:num_categories]


# ==============================================================
# STEP 3 — CATEGORIZE POSTS
# ==============================================================

def categorize_posts(posts: List[Dict], categories: List[str]) -> List[Dict]:
    print(f"\n{'='*60}\nSTEP 3: Post Categorization\n{'='*60}")

    categorized_posts = []
    batch_size = 10
    for i in range(0, len(posts), batch_size):
        batch = posts[i:i+batch_size]

        batch_text = "\n\n".join([
            f"POST_{j+1}: {p['title']} - {p['selftext'][:200]}"
            for j, p in enumerate(batch)
        ])
        cats = "\n".join([f"{k+1}. {c}" for k, c in enumerate(categories)])

        prompt = f"""
        You are categorizing Reddit posts into the following categories:
        {cats}

        For each post below, output a single line:
        POST_X: <category_number> <confidence (0-1)>

        Posts:
        {batch_text}
        """

        def call_openai():
            response = openai_client.chat.completions.create(
                model=AZURE_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a precise text classifier."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()

        result = safe_llm_call(call_openai)
        lines = result.split("\n")

        for j, post in enumerate(batch):
            post_line = next((l for l in lines if f"POST_{j+1}:" in l), None)
            try:
                parts = post_line.split(":")[1].strip().split()
                cat_idx = int(parts[0]) - 1
                conf = float(parts[1]) if len(parts) > 1 else 0.8
                post["category"] = categories[cat_idx] if 0 <= cat_idx < len(categories) else "Uncategorized"
                post["category_confidence"] = conf
            except:
                post["category"] = "Uncategorized"
                post["category_confidence"] = 0.0
            categorized_posts.append(post)

        time.sleep(0.5)

    print(f"✓ Categorized {len(categorized_posts)} posts")
    return categorized_posts


# ==============================================================
# STEP 4 — GENERATE INSIGHTS
# ==============================================================

def generate_insights(posts: List[Dict], categories: List[str]) -> Dict[str, str]:
    print(f"\n{'='*60}\nSTEP 4: Insight Generation\n{'='*60}")

    insights = {}
    for category in tqdm(categories, desc="Generating insights", unit="category"):
        cat_posts = [p for p in posts if p.get("category") == category]
        if not cat_posts:
            insights[category] = "No posts found in this category."
            continue

        posts_summary = [
            f"• {p['title']} (Score: {p['score']}, Comments: {p['num_comments']})\n  {p['selftext'][:200]}"
            for p in cat_posts[:50]
        ]
        posts_text = "\n\n".join(posts_summary)

        avg_score = sum(p['score'] for p in cat_posts) / len(cat_posts)
        avg_comments = sum(p['num_comments'] for p in cat_posts) / len(cat_posts)
        top_post = max(cat_posts, key=lambda x: x['score'])

        prompt = f"""
        You are analyzing posts from the category "{category}".
        Total Posts: {len(cat_posts)}
        Average Score: {avg_score:.1f}
        Average Comments: {avg_comments:.1f}
        Top Post: "{top_post['title']}" ({top_post['score']} score)

        Posts:
        {posts_text}

        Write a 300–500 word insight report including:
        1. Main themes and trends
        2. Common user sentiments
        3. Engagement patterns
        4. Standout examples
        5. Actionable insights
        """

        def call_openai():
            resp = openai_client.chat.completions.create(
                model=AZURE_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a data analyst skilled at Reddit community insight generation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            return resp.choices[0].message.content.strip()

        insight = safe_llm_call(call_openai)
        insights[category] = insight
        time.sleep(0.5)

    print(f"✓ Generated {len(insights)} insights")
    return insights


# ==============================================================
# STEP 5 — SAVE RESULTS
# ==============================================================

def save_results(subreddit: str, posts: List[Dict], categories: List[str], insights: Dict[str, str], output_dir: str):
    print(f"\n{'='*60}\nSTEP 5: Saving Results\n{'='*60}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sub_dir = os.path.join(output_dir, f"{subreddit}_{timestamp}")
    ensure_dir(sub_dir)

    # Save categorized posts
    jsonl_path = os.path.join(sub_dir, "categorized_posts.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for p in posts:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # Save categories and insights
    with open(os.path.join(sub_dir, "categories.json"), "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)
    with open(os.path.join(sub_dir, "insights.json"), "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)

    # Save Markdown report
    report_path = os.path.join(sub_dir, "REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Reddit Analysis Report: r/{subreddit}\n\nGenerated: {datetime.now()}\n\n")
        for c in categories:
            f.write(f"## {c}\n\n{insights.get(c,'No insight generated.')}\n\n")

    print(f" All outputs saved to {sub_dir}")


# ==============================================================
# MAIN PIPELINE RUNNER
# ==============================================================

def run_pipeline(subreddit: str, predefined_categories: Optional[List[str]] = None,
                 num_categories: int = NUM_CATEGORIES, max_posts: Optional[int] = None):
    start = time.time()
    now = datetime.now(tz=timezone.utc)
    cutoff_dt = now - timedelta(days=30 * MONTHS_BACK)
    cutoff_utc = int(cutoff_dt.timestamp())

    posts = scrape_subreddit(subreddit, cutoff_utc, max_posts)
    categories = generate_categories(posts, num_categories, predefined_categories)
    categorized = categorize_posts(posts, categories)
    insights = generate_insights(categorized, categories)
    save_results(subreddit, categorized, categories, insights, OUTPUT_DIR)
    print(f"\n🎯 Pipeline completed in {time.time() - start:.2f}s")


if __name__ == "__main__":
    run_pipeline("MakeupAddiction",predefined_categories=["Product Efficacy & Usage","Purchase Drivers & Intent","Customer Journey Stage","Experience Friction"], num_categories=4, max_posts=3000)
