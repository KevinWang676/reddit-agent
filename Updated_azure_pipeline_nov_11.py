#!/usr/bin/env python3
"""
Reddit Insight Evolution Pipeline (Azure OpenAI) - LLM CLUSTERING VERSION
--------------------------------------------------------------------------
Workflow:
1. Scrape posts from subreddit
2. Summarize posts (BATCHED for efficiency)
3. Categorize summaries into fixed categories (BATCHED)
4. Dynamically cluster summaries per category (LLM-based semantic clustering)
5. Generate one insight per cluster
6. Save all results (JSONL, CSV, JSON, Markdown)

Key Features:
- ✅ LLM-based semantic clustering (no embeddings or sklearn required)
- ✅ Batch processing for 10x efficiency
- ✅ Credential validation
- ✅ Fixed scraping logic
- ✅ Better error handling
- ✅ CSV export added
- ✅ Progress tracking
"""

import os
import csv
import json
import time
import praw
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
USER_AGENT = os.getenv("USER_AGENT", "python:RedditPipeline:v4.0")

# Azure OpenAI credentials
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

# Validate credentials
if not all([CLIENT_ID, CLIENT_SECRET]):
    raise RuntimeError("❌ Missing Reddit credentials in .env: CLIENT_ID, CLIENT_SECRET")

if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT]):
    raise RuntimeError("❌ Missing Azure OpenAI credentials in .env: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT")

# Initialize Azure OpenAI client
openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-08-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)
print(f"✓ Azure OpenAI initialized (LLM-based clustering)")
print(f"  - Deployment: {AZURE_DEPLOYMENT}")

# Pipeline defaults
OUTPUT_DIR = "pipeline_output"
MONTHS_BACK = 12
MIN_SCORE = 0
MIN_NUM_COMMENTS = 0
BATCH_SIZE = 10  # Posts per API call

# Fixed categories for makeup analysis
FIXED_CATEGORIES = [
    "Product Efficacy & Usage",
    "Purchase Drivers & Intent",
    "Customer Journey Stage",
    "Experience Friction"
]

# Validate categories
if not FIXED_CATEGORIES or len(FIXED_CATEGORIES) == 0:
    raise ValueError("❌ FIXED_CATEGORIES cannot be empty")

print(f"✓ Using {len(FIXED_CATEGORIES)} fixed categories")

# ==============================================================
# UTILITIES
# ==============================================================

def ensure_dir(path: str):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)

def safe_llm_call(fn, retries=3, delay=3):
    """Retry wrapper for LLM calls with exponential backoff"""
    for i in range(retries):
        try:
            return fn()
        except Exception as e:
            print(f"⚠️  LLM call failed (attempt {i+1}/{retries}): {e}")
            if i < retries - 1:
                wait_time = delay * (2 ** i)  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise

# ==============================================================
# STEP 1 — SCRAPE SUBREDDIT
# ==============================================================

def scrape_subreddit(subreddit_name: str, cutoff_utc: int, max_posts: Optional[int] = None) -> List[Dict]:
    """Scrape posts from subreddit with filters"""
    print(f"\n{'='*60}")
    print(f"STEP 1: Scraping r/{subreddit_name}")
    print(f"{'='*60}")
    
    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
        check_for_async=False
    )

    posts = []
    processed = 0
    
    try:
        with tqdm(desc=f"Scraping r/{subreddit_name}", unit="post") as pbar:
            for subm in reddit.subreddit(subreddit_name).new(limit=None):
                processed += 1
                pbar.update(1)
                
                # FIXED: Break when hitting old posts (don't continue)
                if int(subm.created_utc) < cutoff_utc:
                    break
                
                # Filter by score
                if subm.score < MIN_SCORE:
                    continue
                if MIN_NUM_COMMENTS > 0 and subm.num_comments < MIN_NUM_COMMENTS:
                    continue

                post = {
                    "id": subm.id,
                    "title": subm.title,
                    "selftext": subm.selftext or "",
                    "score": subm.score,
                    "num_comments": subm.num_comments,
                    "created_utc": subm.created_utc,
                    "created_iso": datetime.fromtimestamp(subm.created_utc, tz=timezone.utc).isoformat(),
                    "permalink": f"https://reddit.com{subm.permalink}",
                }
                posts.append(post)

                # Check max_posts limit
                if max_posts and len(posts) >= max_posts:
                    break
    
    except Exception as e:
        print(f"⚠️  Scraping error: {e}")
    
    print(f"✓ Scraped {len(posts)} posts from r/{subreddit_name} (processed {processed} total)")
    return posts

# --------------------------------------------------------------
# Optional: Time-sliced scraping using subreddit.top() listing
# --------------------------------------------------------------
def scrape_subreddit_top_timesliced(
    subreddit_name: str,
    end_dt: datetime,
    lookback_days: int = 365,
    slice_days: int = 14,
    per_slice: int = 30,
) -> List[Dict]:
    """Collect top posts per time slice using subreddit.top() then slice locally."""
    print(f"\n{'='*60}")
    print(f"STEP 1 (Timesliced): Scraping r/{subreddit_name} via top() listing")
    print(f"  Window end: {end_dt.isoformat()}  lookback_days={lookback_days}  slice_days={slice_days}  per_slice={per_slice}")
    print(f"{'='*60}")

    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
        check_for_async=False
    )

    end_ts = int(end_dt.timestamp())
    start_ts = end_ts - lookback_days * 86400

    # 1) Fetch top listing (year) capped at ~1000
    collected: List[Dict] = []
    try:
        for subm in reddit.subreddit(subreddit_name).top(time_filter="year", limit=1000):
            post = {
                "id": subm.id,
                "title": subm.title,
                "selftext": getattr(subm, "selftext", "") or "",
                "score": subm.score,
                "num_comments": subm.num_comments,
                "created_utc": subm.created_utc,
                "created_iso": datetime.fromtimestamp(subm.created_utc, tz=timezone.utc).isoformat(),
                "permalink": f"https://reddit.com{subm.permalink}",
            }
            collected.append(post)
    except Exception as e:
        print(f"    Error fetching top listing: {e}")

    if not collected:
        print("    No posts from top listing.")
        return []

    # 2) Filter to window
    window_posts = [p for p in collected if start_ts <= int(p.get("created_utc", 0)) <= end_ts]
    print(f"  Top listing fetched: {len(collected)}; in-window: {len(window_posts)}")

    if not window_posts:
        return []

    # 3) Slice locally and pick top per slice by score
    window_posts.sort(key=lambda x: x.get("created_utc", 0), reverse=True)
    result: List[Dict] = []

    current_end = end_ts
    while current_end > start_ts:
        current_start = max(start_ts, current_end - slice_days * 86400 + 1)
        slice_posts = [
            p for p in window_posts
            if current_start <= int(p.get("created_utc", 0)) <= current_end
            and p.get("score", 0) >= MIN_SCORE
            and (MIN_NUM_COMMENTS <= 0 or p.get("num_comments", 0) >= MIN_NUM_COMMENTS)
        ]
        if slice_posts:
            slice_posts.sort(key=lambda x: x.get("score", 0), reverse=True)
            selected = slice_posts[:per_slice]
            result.extend(selected)
            print(f"  Slice {datetime.fromtimestamp(current_start, tz=timezone.utc).date()} -> {datetime.fromtimestamp(current_end, tz=timezone.utc).date()}: {len(selected)}/{len(slice_posts)} selected")
        else:
            print(f"  Slice {datetime.fromtimestamp(current_start, tz=timezone.utc).date()} -> {datetime.fromtimestamp(current_end, tz=timezone.utc).date()}: 0 posts")

        current_end = current_start - 1

    # Deduplicate in case of boundary issues (by id, keep first occurrence)
    seen_ids = set()
    deduped: List[Dict] = []
    for p in result:
        pid = p.get("id")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            deduped.append(p)

    print(f"  Collected {len(deduped)} posts across slices (deduped)")
    return deduped

# ==============================================================
# STEP 2 — SUMMARIZE POSTS (BATCHED)
# ==============================================================

def summarize_batch(posts: List[Dict]) -> List[Dict[str, str]]:
    """Summarize multiple posts in one API call and produce sentiment labels"""
    # Build batch prompt
    batch_text = ""
    for i, p in enumerate(posts):
        title = p['title']
        content = p['selftext'][:300] if p['selftext'] else "[No text content]"
        batch_text += f"\nPOST_{i+1}:\nTitle: {title}\nContent: {content}\n"

    prompt = f"""Summarize each Reddit post in 2-3 concise sentences. Capture the main point, user sentiment, and any specific pain points or needs mentioned. Also provide an overall sentiment label for each post as one of: positive, neutral, negative.

{batch_text}

Return ONLY in this exact format (one line per post):
POST_1: [summary text here] || SENTIMENT: [positive|neutral|negative]
POST_2: [summary text here] || SENTIMENT: [positive|neutral|negative]
...

Be specific and preserve important details. Focus on what the user is asking, experiencing, or discussing.
"""

    def call():
        resp = openai_client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an expert at summarizing Reddit posts. You capture key ideas, sentiment, and user needs concisely."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        return resp.choices[0].message.content.strip()
    
    result = safe_llm_call(call)
    
    # Parse summaries + sentiments
    parsed_results: List[Dict[str, str]] = []
    lines = result.split('\n')
    for i in range(len(posts)):
        # Find line for this post
        post_line = None
        for line in lines:
            if line.strip().startswith(f"POST_{i+1}:"):
                post_line = line.strip()
                break
        summary_text = posts[i]['title']
        sentiment_label = "neutral"
        if post_line:
            try:
                # Split "POST_X: <summary> || SENTIMENT: <label>"
                after_colon = post_line.split(":", 1)[1].strip()
                if "||" in after_colon:
                    summary_part, sentiment_part = after_colon.split("||", 1)
                    summary_text = summary_part.strip()
                    if "SENTIMENT" in sentiment_part:
                        raw = sentiment_part.split("SENTIMENT", 1)[1]
                        raw = raw.split(":", 1)[1] if ":" in raw else raw
                        raw = raw.strip().lower()
                        if "pos" in raw:
                            sentiment_label = "positive"
                        elif "neg" in raw:
                            sentiment_label = "negative"
                        else:
                            sentiment_label = "neutral"
                else:
                    # If not provided in expected format, treat whole as summary
                    summary_text = after_colon
            except Exception:
                # Fallbacks already set
                pass
        parsed_results.append({"summary": summary_text, "sentiment": sentiment_label})
    
    return parsed_results

def summarize_posts(posts: List[Dict]) -> List[Dict]:
    """Summarize all posts using batch processing"""
    print(f"\n{'='*60}")
    print(f"STEP 2: Summarizing Posts (Batched)")
    print(f"{'='*60}")
    
    summarized = []
    with tqdm(total=len(posts), desc="Summarizing", unit="post") as pbar:
        for i in range(0, len(posts), BATCH_SIZE):
            batch = posts[i:i+BATCH_SIZE]
            
            try:
                summaries = summarize_batch(batch)
                for p, item in zip(batch, summaries):
                    p["summary"] = item["summary"]
                    p["sentiment"] = item["sentiment"]
                    summarized.append(p)
            except Exception as e:
                print(f"⚠️  Batch summarization failed: {e}")
                # Fallback: Use title as summary
                for p in batch:
                    p["summary"] = p["title"]
                    p["sentiment"] = "neutral"
                    summarized.append(p)
            
            pbar.update(len(batch))
            time.sleep(0.3)  # Rate limiting
    
    print(f"✓ Generated summaries for {len(summarized)} posts")
    return summarized

# ==============================================================
# STEP 3 — CATEGORIZE SUMMARIES (BATCHED)
# ==============================================================

def categorize_batch(posts: List[Dict], categories: List[str]) -> List[str]:
    """Categorize multiple posts in one API call"""
    cats_list = "\n".join([f"{i+1}. {c}" for i, c in enumerate(categories)])
    
    batch_text = ""
    for i, p in enumerate(posts):
        batch_text += f"\nPOST_{i+1}: {p['summary']}\n"
    
    prompt = f"""Categorize each post summary into exactly ONE category from this list:

{cats_list}

Instructions:
- Choose the single most relevant category for each post
- Respond with ONLY the category number (1–{len(categories)})
- Format: POST_X: <number>

Posts to categorize:
{batch_text}

Your categorization (one number per post):"""

    def call():
        resp = openai_client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a precise text classifier. You always return exactly one category number for each post."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        return resp.choices[0].message.content.strip()
    
    result = safe_llm_call(call)
    
    # Parse categorizations
    category_assignments = []
    lines = result.split('\n')
    for i in range(len(posts)):
        post_line = None
        for line in lines:
            if f"POST_{i+1}:" in line:
                post_line = line
                break
        
        if post_line:
            try:
                cat_num = int(post_line.split(':')[1].strip())
                if 1 <= cat_num <= len(categories):
                    category_assignments.append(categories[cat_num - 1])
                else:
                    category_assignments.append("Uncategorized")
            except:
                category_assignments.append("Uncategorized")
        else:
            category_assignments.append("Uncategorized")
    
    return category_assignments

def categorize_posts(posts: List[Dict], categories: List[str]) -> List[Dict]:
    """Categorize all posts using batch processing"""
    print(f"\n{'='*60}")
    print(f"STEP 3: Categorizing Summaries (Batched)")
    print(f"{'='*60}")
    
    categorized = []
    with tqdm(total=len(posts), desc="Categorizing", unit="post") as pbar:
        for i in range(0, len(posts), BATCH_SIZE):
            batch = posts[i:i+BATCH_SIZE]
            
            try:
                cats = categorize_batch(batch, categories)
                for p, cat in zip(batch, cats):
                    p["category"] = cat
                    categorized.append(p)
            except Exception as e:
                print(f"⚠️  Batch categorization failed: {e}")
                # Fallback: Mark as Uncategorized
                for p in batch:
                    p["category"] = "Uncategorized"
                    categorized.append(p)
            
            pbar.update(len(batch))
            time.sleep(0.3)  # Rate limiting
    
    # Print distribution
    cat_counts = {}
    for p in categorized:
        cat = p.get('category', 'Uncategorized')
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    
    print(f"✓ Categorization complete:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count} posts")
    
    return categorized

# ==============================================================
# STEP 4 — LLM-BASED SEMANTIC CLUSTERING
# ==============================================================

def _cluster_initial_sample(posts: List[Dict], category: str, min_cluster_size: int) -> Dict[int, List[int]]:
    """
    Cluster a sample of posts to identify natural themes.

    Args:
        posts: List of posts to cluster (should be <= 100)
        category: Category name
        min_cluster_size: Minimum posts per cluster

    Returns:
        Dict mapping cluster_id to list of post indices
    """
    num_posts = len(posts)

    # Prepare posts for LLM
    posts_text = ""
    for i, p in enumerate(posts):
        summary = p['summary'][:300] if len(p['summary']) > 300 else p['summary']
        posts_text += f"\nPOST_{i}: {summary}\n"

    prompt = f"""You are clustering Reddit post summaries in the category "{category}".

Task: Group these {num_posts} posts into thematic clusters. Posts discussing similar topics, issues, or themes belong together.

Guidelines:
- Create as many clusters as needed (no fixed limit)
- Posts in a cluster should share a specific, coherent theme (topic, problem, claim, or experience)
- ALL posts must be assigned to exactly one cluster

Posts to cluster (index 0 to {num_posts-1}):
{posts_text}

Return ONLY a JSON array where each element is a cluster (array of post indices 0-{num_posts-1}).

Example format:
[
  [0, 3, 7, 15],
  [1, 5, 9, 12, 14],
  [2, 4, 6, 8, 10, 11, 13]
]

Critical: Ensure ALL indices from 0 to {num_posts-1} appear exactly once across all clusters.

Your clustering (JSON array only):"""

    def call():
        resp = openai_client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an expert at semantic clustering and pattern recognition. You always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        return resp.choices[0].message.content.strip()

    result = safe_llm_call(call)

    # Parse JSON response
    result = result.replace("```json", "").replace("```", "").strip()
    clusters_array = json.loads(result)

    # Validate and convert to dict format with CONSECUTIVE cluster IDs
    clusters = {}
    seen_indices = set()
    next_cluster_id = 0  # Ensure consecutive IDs starting from 0

    for indices in clusters_array:
        valid_indices = [i for i in indices if 0 <= i < num_posts and i not in seen_indices]
        if len(valid_indices) >= min_cluster_size:
            clusters[next_cluster_id] = valid_indices
            seen_indices.update(valid_indices)
            next_cluster_id += 1

    # Handle any missing posts
    missing_indices = [i for i in range(num_posts) if i not in seen_indices]
    if missing_indices:
        if clusters:
            largest_cluster = max(clusters.keys(), key=lambda k: len(clusters[k]))
            clusters[largest_cluster].extend(missing_indices)
        else:
            clusters[0] = list(range(num_posts))

    return clusters if clusters else {0: list(range(num_posts))}


def _extract_cluster_themes(posts: List[Dict], clusters: Dict[int, List[int]], category: str) -> Dict[int, str]:
    """
    Extract a descriptive theme for each cluster.

    Args:
        posts: Original posts list
        clusters: Cluster assignments (cluster_id -> list of indices)
        category: Category name

    Returns:
        Dict mapping cluster_id to theme description
    """
    cluster_themes = {}

    for cluster_id, indices in clusters.items():
        # Get summaries for this cluster (limit to 20 for token efficiency)
        cluster_posts = [posts[i] for i in indices[:20]]
        summaries = "\n".join([f"- {p['summary'][:200]}" for p in cluster_posts])

        prompt = f"""Analyze these {len(indices)} Reddit posts from the "{category}" category and identify their unifying theme.

Sample posts (showing {len(cluster_posts)} of {len(indices)}):
{summaries}

Write a single, clear sentence (20-30 words) that describes the main theme, topic, or issue that connects these posts.

Focus on: What specific topic, problem, or discussion area do these posts share?

Theme:"""

        def call():
            resp = openai_client.chat.completions.create(
                model=AZURE_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are an expert at identifying themes and patterns in social media discussions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=100
            )
            return resp.choices[0].message.content.strip()

        theme = safe_llm_call(call)
        cluster_themes[cluster_id] = theme
        print(f"      Cluster {cluster_id}: \"{theme}\" ({len(indices)} posts)")
        time.sleep(0.3)  # Rate limiting

    return cluster_themes


def _assign_posts_to_clusters(posts: List[Dict], cluster_themes: Dict[int, str],
                               clusters: Dict[int, List[int]], start_idx: int,
                               category: str, batch_size: int = 30):
    """
    Assign remaining posts to existing clusters based on themes.

    Args:
        posts: Posts to assign (from start_idx onwards in original list)
        cluster_themes: Theme descriptions for each cluster
        clusters: Existing cluster assignments (will be modified in-place)
        start_idx: Starting index in original post list
        category: Category name
        batch_size: Number of posts to assign per API call
    """
    num_posts = len(posts)

    print(f"    → Assigning {num_posts} remaining posts to {len(cluster_themes)} clusters")

    # Prepare cluster descriptions with cluster IDs listed
    cluster_ids = sorted(cluster_themes.keys())
    themes_text = "\n".join([f"CLUSTER_{cid}: {cluster_themes[cid]}" for cid in cluster_ids])
    cluster_ids_str = ", ".join([str(cid) for cid in cluster_ids])

    for i in range(0, num_posts, batch_size):
        batch = posts[i:i+batch_size]
        batch_start = start_idx + i

        # Prepare batch text
        posts_text = ""
        for j, p in enumerate(batch):
            summary = p['summary'][:250]
            posts_text += f"\nPOST_{batch_start + j}: {summary}\n"

        prompt = f"""Assign each post to the most relevant cluster based on thematic similarity.

Category: "{category}"

Available Clusters ({cluster_ids_str}):
{themes_text}

Posts to assign:
{posts_text}

Instructions:
- Assign each post to exactly ONE cluster: {cluster_ids_str}
- Choose the cluster whose theme best matches the post's content
- Return ONLY in this format:
POST_X: <cluster_number>
POST_Y: <cluster_number>

Your assignments:"""

        def call():
            resp = openai_client.chat.completions.create(
                model=AZURE_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are an expert at text classification and thematic matching."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            return resp.choices[0].message.content.strip()

        try:
            result = safe_llm_call(call)
            lines = result.split('\n')

            # Parse assignments
            for j, p in enumerate(batch):
                post_idx = batch_start + j
                assigned = False

                for line in lines:
                    if f"POST_{post_idx}:" in line:
                        try:
                            cluster_num = int(line.split(':')[1].strip())
                            if cluster_num in clusters:
                                clusters[cluster_num].append(post_idx)
                                assigned = True
                                break
                        except:
                            continue

                # Fallback: assign to largest cluster
                if not assigned:
                    largest = max(clusters.keys(), key=lambda k: len(clusters[k]))
                    clusters[largest].append(post_idx)

        except Exception as e:
            print(f"      ⚠️  Batch assignment error: {e}, assigning to largest cluster")
            largest = max(clusters.keys(), key=lambda k: len(clusters[k]))
            for j in range(len(batch)):
                clusters[largest].append(batch_start + j)

        time.sleep(0.3)  # Rate limiting

        if (i + batch_size) < num_posts:
            print(f"      Assigned {i + len(batch)}/{num_posts} posts...")

    # Summary: Show final cluster sizes after assignment
    print(f"    → Assignment complete:")
    for cid in sorted(clusters.keys()):
        print(f"      Cluster {cid}: {len(clusters[cid])} posts")


def llm_cluster_posts(posts: List[Dict], category: str, min_cluster_size: int = 2) -> Dict[int, List[int]]:
    """
    Use LLM to cluster posts by semantic similarity.

    Two-phase approach for large categories:
    1. Cluster initial sample (100 posts) to identify natural themes
    2. Extract theme descriptions for each cluster
    3. Assign remaining posts to clusters in batches

    Args:
        posts: List of posts with summaries
        category: Category name for context
        min_cluster_size: Minimum posts per cluster

    Returns:
        Dict mapping cluster_id to list of post indices
    """
    num_posts = len(posts)
    INITIAL_SAMPLE_SIZE = 100

    # Small category: direct clustering
    if num_posts <= INITIAL_SAMPLE_SIZE:
        print(f"    → Clustering {num_posts} posts directly")
        try:
            return _cluster_initial_sample(posts, category, min_cluster_size)
        except Exception as e:
            print(f"    ⚠️  Clustering error: {e}")
            return {0: list(range(num_posts))}

    # Large category: two-phase clustering
    print(f"    → Large category ({num_posts} posts), using two-phase approach")

    try:
        # Phase 1: Cluster initial sample
        print(f"    → Phase 1: Clustering first {INITIAL_SAMPLE_SIZE} posts")
        sample_posts = posts[:INITIAL_SAMPLE_SIZE]
        clusters = _cluster_initial_sample(sample_posts, category, min_cluster_size)

        if not clusters:
            print(f"    → No valid clusters formed, creating single cluster")
            return {0: list(range(num_posts))}

        print(f"    → Formed {len(clusters)} initial clusters")

        # Phase 2: Extract cluster themes
        print(f"    → Phase 2: Extracting cluster themes")
        cluster_themes = _extract_cluster_themes(posts, clusters, category)

        # Phase 3: Assign remaining posts
        remaining_posts = posts[INITIAL_SAMPLE_SIZE:]
        if remaining_posts:
            print(f"    → Phase 3: Assigning remaining posts")
            _assign_posts_to_clusters(remaining_posts, cluster_themes, clusters,
                                     INITIAL_SAMPLE_SIZE, category)

        # Validate all posts assigned
        total_assigned = sum(len(indices) for indices in clusters.values())
        print(f"    → Total posts assigned: {total_assigned}/{num_posts}")

        return clusters

    except Exception as e:
        print(f"    ⚠️  LLM clustering error: {e}")
        # Fallback: Put all posts in one cluster
        return {0: list(range(num_posts))}

def generate_insights_llm_clustering(posts: List[Dict], categories: List[str],
                                     min_cluster_size: int = 2) -> Dict:
    """
    Cluster post summaries per category using LLM-based semantic clustering,
    then generate one insight per cluster.

    Args:
        posts: List of categorized posts with summaries
        categories: List of category names
        min_cluster_size: Minimum posts per cluster

    Returns:
        Dict mapping categories to lists of insight objects
    """
    print(f"\n{'='*60}")
    print(f"STEP 4: LLM-Based Semantic Clustering")
    print(f"{'='*60}")
    print(f"Settings: min_cluster_size={min_cluster_size}")
    
    insights_db = {}

    for cat in categories:
        cat_posts = [p for p in posts if p.get("category") == cat]
        if not cat_posts:
            print(f"  {cat}: No posts")
            continue

        print(f"\n  Processing: {cat} ({len(cat_posts)} posts)")

        # Check if we have enough posts to cluster
        if len(cat_posts) < 2:
            print(f"    → Only 1 post, generating direct insight (no clustering)")
            # Generate insight for single post
            insight_text = generate_single_insight(cat, cat_posts)
            insights_db[cat] = [{
                "id": f"{cat[:4].lower()}_01",
                "category": cat,
                "summary": insight_text,
                "linked_posts": [cat_posts[0]["id"]],
                "cluster_size": 1,
                "last_updated": datetime.now().isoformat()
            }]
            continue

        try:
            # LLM-based clustering
            print(f"    → Clustering with LLM...")
            clusters = llm_cluster_posts(cat_posts, cat, min_cluster_size)
            print(f"    → Formed {len(clusters)} clusters")

            cat_insights = []
            for cluster_id, post_indices in sorted(clusters.items()):
                cluster_posts = [cat_posts[i] for i in post_indices if i < len(cat_posts)]
                
                if len(cluster_posts) < min_cluster_size:
                    print(f"      Cluster {cluster_id+1}: {len(cluster_posts)} posts (skipped - too small)")
                    continue

                print(f"      Cluster {cluster_id+1}: {len(cluster_posts)} posts → generating insight")

                # Generate insight for this cluster
                # Sort by date to show chronological patterns
                cluster_posts_sorted = sorted(cluster_posts, key=lambda x: x['created_iso'])
                combined = "\n".join([
                    f"- [{p['created_iso'][:10]}] (↑{p['score']} upvotes, {p['num_comments']} comments) [{p.get('sentiment','neutral')}] {p['summary']}"
                    for p in cluster_posts_sorted[:25]  # Limit to 25 for token size
                ])

                prompt = f"""You are a market insights analyst evaluating Reddit discussions in the "{cat}" category.

Context: You are analyzing a cluster of {len(cluster_posts)} thematically similar posts. Each post shows its date, upvotes (↑), comment count, sentiment label in brackets [positive|neutral|negative], and summary.

Your task:
1. Identify the single main theme connecting these posts.
2. Provide exactly ONE key insight summarizing the most important pattern, sentiment, or takeaway found across the posts.
3. Include supporting evidence from 1–2 posts (dates, upvotes, or quotes) that justify this insight.
4. Do NOT provide business or marketing recommendations.

Structure your analysis exactly in this format:

**Theme:**
[One concise sentence describing the unifying topic]

**Key Insight:**
[One concise paragraph (3–4 sentences) explaining the single most important finding across these posts]

**Supporting Evidence:**
[List 1–2 posts with brief notes, e.g. “Post from 2024-05-10 (↑250): users frustrated with shade mismatch”]

Posts (chronologically ordered, {len(cluster_posts)} total, showing top 25):
{combined}
"""

                def call():
                    resp = openai_client.chat.completions.create(
                        model=AZURE_DEPLOYMENT,
                        messages=[
                            {"role": "system", "content": "You are an expert market insights analyst who transforms Reddit discussions into actionable business intelligence. You focus on patterns, sentiment, and practical recommendations."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.6,
                        max_tokens=4096
                    )
                    return resp.choices[0].message.content.strip()

                insight_text = safe_llm_call(call)

                cat_insights.append({
                    "id": f"{cat[:4].lower()}_{cluster_id+1:02}",
                    "category": cat,
                    "summary": insight_text,
                    "linked_posts": [p["id"] for p in cluster_posts],
                    "cluster_size": len(cluster_posts),
                    "last_updated": datetime.now().isoformat()
                })
                
                time.sleep(0.5)  # Rate limiting

            # FIXED: Handle case where no clusters meet minimum size
            if not cat_insights:
                print(f"    → No clusters met minimum size, generating single insight for all posts")
                insight_text = generate_category_insight(cat, cat_posts)
                cat_insights.append({
                    "id": f"{cat[:4].lower()}_all",
                    "category": cat,
                    "summary": insight_text,
                    "linked_posts": [p["id"] for p in cat_posts],
                    "cluster_size": len(cat_posts),
                    "last_updated": datetime.now().isoformat()
                })

            insights_db[cat] = cat_insights
            
        except Exception as e:
            print(f"    ❌ Clustering failed for {cat}: {e}")
            # Generate fallback insight without clustering
            try:
                insight_text = generate_category_insight(cat, cat_posts)
                insights_db[cat] = [{
                    "id": f"{cat[:4].lower()}_fallback",
                    "category": cat,
                    "summary": insight_text,
                    "linked_posts": [p["id"] for p in cat_posts],
                    "cluster_size": len(cat_posts),
                    "last_updated": datetime.now().isoformat()
                }]
            except Exception as e2:
                print(f"    ❌ Fallback insight also failed: {e2}")
                insights_db[cat] = []

    print(f"\n✓ LLM-based semantic clustering complete")
    total_insights = sum(len(v) for v in insights_db.values())
    print(f"  Total insights: {total_insights}")
    return insights_db

def generate_single_insight(category: str, posts: List[Dict]) -> str:
    """Generate insight for a single post using LLM"""
    p = posts[0]

    prompt = f"""Analyze this single Reddit post from the "{category}" category and extract meaningful insights.

Post Details:
- Title: {p['title']}
- Date: {p['created_iso'][:10]}
- Engagement: {p['score']} upvotes, {p['num_comments']} comments
- Summary: {p['summary']}

Provide a brief analysis (100-150 words) covering:
1. What this post reveals about user needs or pain points
2. The significance of its engagement level
"""

    def call():
        resp = openai_client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an expert market insights analyst. Extract valuable insights even from single data points."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=300
        )
        return resp.choices[0].message.content.strip()

    return safe_llm_call(call)

def generate_category_insight(category: str, posts: List[Dict]) -> str:
    """Generate insight for entire category (no clustering)"""
    # Sort by date for temporal analysis
    posts_sorted = sorted(posts, key=lambda x: x['created_iso'])
    combined = "\n".join([
        f"- [{p['created_iso'][:10]}] (↑{p['score']}, {p['num_comments']} comments) [{p.get('sentiment','neutral')}] {p['summary']}"
        for p in posts_sorted[:50]
    ])

    avg_score = sum(p['score'] for p in posts) / len(posts)
    avg_comments = sum(p['num_comments'] for p in posts) / len(posts)
    # Sentiment distribution
    pos = sum(1 for p in posts if str(p.get('sentiment','neutral')).lower().startswith('pos'))
    neg = sum(1 for p in posts if str(p.get('sentiment','neutral')).lower().startswith('neg'))
    neu = len(posts) - pos - neg
    pos_pct = (pos / len(posts)) * 100 if posts else 0
    neu_pct = (neu / len(posts)) * 100 if posts else 0
    neg_pct = (neg / len(posts)) * 100 if posts else 0

    prompt = f"""Analyze these {len(posts)} Reddit posts in the "{category}" category.

Engagement Stats:
- Average Score: {avg_score:.1f} upvotes
- Average Comments: {avg_comments:.1f}
Sentiment Distribution:
- Positive: {pos} ({pos_pct:.1f}%)
- Neutral: {neu} ({neu_pct:.1f}%)
- Negative: {neg} ({neg_pct:.1f}%)

Your task:
1. Identify 2-3 main themes across all posts
2. Detect any temporal patterns or trends
3. Assess overall user sentiment
4. Provide 2-3 actionable recommendations

Structure:

**Main Themes:**
- [Theme 1]
- [Theme 2]

**User Sentiment & Trends:**
[Analysis of sentiment and any patterns over time]

**Actionable Recommendations:**
1. [Specific recommendation]
2. [Specific recommendation]

Posts (chronologically ordered, showing up to 50):
{combined}
"""

    def call():
        resp = openai_client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an expert market insights analyst who identifies patterns and provides actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=800
        )
        return resp.choices[0].message.content.strip()

    return safe_llm_call(call)

# ==============================================================
# STEP 5 — SAVE OUTPUTS
# ==============================================================

def save_outputs(subreddit: str, posts: List[Dict], insights: Dict, lookback_days: int = 365):
    """Save all results in multiple formats"""
    print(f"\n{'='*60}")
    print(f"STEP 5: Saving Results")
    print(f"{'='*60}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subdir = os.path.join(OUTPUT_DIR, f"{subreddit}_{timestamp}")
    ensure_dir(subdir)

    # 1. Save posts (JSONL)
    jsonl_path = os.path.join(subdir, "posts.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for p in posts:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"✓ Saved {len(posts)} posts to: {jsonl_path}")

    # 2. Save posts summary (CSV) - ADDED
    csv_path = os.path.join(subdir, "posts_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "created_iso", "title", "score", "num_comments", "category", "sentiment", "summary"])
        for p in posts:
            writer.writerow([
                p['id'],
                p['created_iso'],
                p['title'],
                p['score'],
                p['num_comments'],
                p.get('category', 'Uncategorized'),
                p.get('sentiment', ''),
                p.get('summary', '')[:100]  # Truncate for CSV
            ])
    print(f"✓ Saved CSV to: {csv_path}")

    # 3. Save categories - ADDED
    categories_used = sorted(set([p.get('category', 'Uncategorized') for p in posts]))
    with open(os.path.join(subdir, "categories.json"), "w", encoding="utf-8") as f:
        json.dump(categories_used, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(categories_used)} categories")

    # 4. Save insights (JSON)
    insights_path = os.path.join(subdir, "insights.json")
    with open(insights_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved insights to: {insights_path}")

    # 5. Save Markdown report
    report_path = os.path.join(subdir, "REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Reddit Analysis Report: r/{subreddit}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Posts:** {len(posts)}\n\n")
        f.write(f"**Lookback Period:** {lookback_days} days\n\n")
        f.write(f"**Categories:** {len(categories_used)}\n\n")
        
        # Write cluster count per category
        f.write("## Category Overview\n\n")
        for cat in FIXED_CATEGORIES:
            cat_posts = [p for p in posts if p.get('category') == cat]
            num_clusters = len(insights.get(cat, []))
            f.write(f"- **{cat}**: {len(cat_posts)} posts, {num_clusters} clusters\n")
        f.write("\n---\n\n")
        
        # Write insights
        for cat, ins_list in insights.items():
            f.write(f"## {cat}\n\n")
            if not ins_list:
                f.write("*No insights generated for this category.*\n\n")
            for ins in ins_list:
                f.write(f"### Cluster {ins['id']} ({ins['cluster_size']} posts)\n\n")
                f.write(f"{ins['summary']}\n\n")
                f.write(f"**Linked Posts:** {', '.join(ins['linked_posts'])}\n\n")
                f.write("---\n\n")
    
    print(f"✓ Saved report to: {report_path}")
    print(f"\n{'='*60}")
    print(f"✅ All results saved to: {subdir}")
    print(f"{'='*60}")
    return subdir

# ==============================================================
# STEP 6 — GENERATE FRONT-END DASHBOARD JSON
# ==============================================================

def generate_dashboard_json(subreddit: str, posts: List[Dict], insights: Dict, output_dir: str):
    """
    Create a unified dashboard_data.json for front-end visualization.
    Includes metadata, category aggregates, structured insights, and posts.
    """
    import re
    from statistics import mean
    from datetime import datetime

    print(f"\n{'='*60}")
    print("STEP 6: Building front-end dashboard JSON")
    print(f"{'='*60}")

    # Helper: sentiment → numeric
    def sentiment_to_num(s):
        s = str(s).lower()
        if "pos" in s:
            return 1
        if "neg" in s:
            return -1
        return 0

    # -----------------------------------------------------------------
    # 1. Index posts by ID for quick lookup
    # -----------------------------------------------------------------
    post_lookup = {p["id"]: p for p in posts}

    # -----------------------------------------------------------------
    # 2. Parse insights into structured fields
    # -----------------------------------------------------------------
    insights_flat = []
    for cat, cat_insights in insights.items():
        for ins in cat_insights:
            text = ins.get("summary", "")
            # Extract Theme, Key Insight, Supporting Evidence via regex
            theme_match = re.search(r"\*\*Theme:\*\*\s*(.*?)\n", text, re.S)
            key_match = re.search(r"\*\*Key Insight:\*\*\s*(.*?)\n", text, re.S)
            ev_match = re.search(r"\*\*Supporting Evidence:\*\*\s*(.*)", text, re.S)

            theme = theme_match.group(1).strip() if theme_match else ""
            key_insight = key_match.group(1).strip() if key_match else ""
            supporting_evidence = []
            if ev_match:
                # Split evidence lines
                lines = [l.strip("-• ").strip() for l in ev_match.group(1).split("\n") if l.strip()]
                supporting_evidence = lines

            linked_posts = ins.get("linked_posts", [])
            linked = [post_lookup[i] for i in linked_posts if i in post_lookup]

            # Compute metrics for this cluster
            if linked:
                avg_sent = mean([sentiment_to_num(p.get("sentiment", "neutral")) for p in linked])
                total_eng = sum(p.get("score", 0) + p.get("num_comments", 0) for p in linked)
                time_vals = sorted(p["created_iso"] for p in linked)
                time_range = [time_vals[0], time_vals[-1]]
            else:
                avg_sent, total_eng, time_range = 0, 0, []

            insights_flat.append({
                "id": ins.get("id"),
                "category": cat,
                "theme": theme,
                "key_insight": key_insight,
                "supporting_evidence": supporting_evidence,
                "cluster_size": ins.get("cluster_size", 0),
                "avg_sentiment": round(avg_sent, 3),
                "total_engagement": total_eng,
                "time_range": time_range,
                "linked_posts": linked_posts,
                "linked_posts_full": [
                    {
                        "id": p["id"],
                        "title": p.get("title", ""),
                        "score": p.get("score", 0),
                        "num_comments": p.get("num_comments", 0),
                        "sentiment": p.get("sentiment", "neutral"),
                        "created_iso": p.get("created_iso", ""),
                        "created_utc": p.get("created_utc", 0),
                        "permalink": p.get("permalink", "")
                    }
                    for p in linked
                ],
                "last_updated": ins.get("last_updated")
            })


    # -----------------------------------------------------------------
    # 3. Aggregate metrics by category
    # -----------------------------------------------------------------
    categories_agg = []
    category_names = sorted(set(p.get("category", "Uncategorized") for p in posts))
    for cat in category_names:
        cat_posts = [p for p in posts if p.get("category") == cat]
        cat_insights = [i for i in insights_flat if i["category"] == cat]

        if not cat_posts:
            continue
        avg_sent = mean([sentiment_to_num(p.get("sentiment")) for p in cat_posts])
        avg_score = mean([p.get("score", 0) for p in cat_posts])
        avg_comments = mean([p.get("num_comments", 0) for p in cat_posts])

        categories_agg.append({
            "name": cat,
            "num_posts": len(cat_posts),
            "num_clusters": len(cat_insights),
            "avg_sentiment": round(avg_sent, 3),
            "avg_score": round(avg_score, 1),
            "avg_comments": round(avg_comments, 1)
        })

    # -----------------------------------------------------------------
    # 4. Build final JSON structure
    # -----------------------------------------------------------------
    dashboard_data = {
        "metadata": {
            "subreddit": subreddit,
            "generated_at": datetime.now().isoformat(),
            "num_posts": len(posts),
            "num_insights": len(insights_flat)
        },
        "categories": categories_agg,
        "insights": insights_flat,
        "posts": posts
    }

    out_path = os.path.join(output_dir, "dashboard_data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Front-end JSON saved → {out_path}")
    print(f"{'='*60}\n")

# ==============================================================
# MAIN RUNNER
# ==============================================================

def run_pipeline(subreddit: str, max_posts: Optional[int] = None,
                min_cluster_size: int = 3,
                before_date: Optional[str] = None,
                slice_days: int = 0,
                top_per_slice: int = 0,
                lookback_days: int = 365):
    """
    Execute the complete clustering pipeline using LLM-based semantic clustering

    Args:
        subreddit: Subreddit name to analyze
        max_posts: Maximum posts to scrape (None = unlimited)
        min_cluster_size: Minimum posts per cluster
    """
    print(f"\n{'#'*60}")
    print(f"# Reddit Clustering Pipeline (Azure OpenAI)")
    print(f"# Subreddit: r/{subreddit}")
    print(f"# Max Posts: {max_posts or 'Unlimited'}")
    if slice_days and top_per_slice:
        print(f"# Time-slicing: {top_per_slice} posts every {slice_days} days, lookback={lookback_days} days")
        if before_date:
            print(f"# End date: {before_date}")
    print(f"{'#'*60}\n")
    
    start_time = time.time()
    
    # Calculate time window (for default mode)
    now = datetime.now(tz=timezone.utc)
    # FIXED: Use lookback_days parameter instead of hardcoded MONTHS_BACK
    cutoff_dt = now - timedelta(days=lookback_days)
    cutoff_utc = int(cutoff_dt.timestamp())
    
    if slice_days and top_per_slice:
        print(f"Timeslice Mode")
        print(f"Filters: MIN_SCORE={MIN_SCORE}, MIN_NUM_COMMENTS={MIN_NUM_COMMENTS}")
    else:
        print(f"Time window: {cutoff_dt.date()} → {now.date()} (lookback={lookback_days} days)")
        print(f"Filters: MIN_SCORE={MIN_SCORE}, MIN_NUM_COMMENTS={MIN_NUM_COMMENTS}")
    print(f"Categories: {FIXED_CATEGORIES}")

    try:
        # Execute pipeline
        if slice_days and top_per_slice:
            # Parse end date or use now
            if before_date:
                try:
                    if "T" in before_date:
                        end_dt = datetime.fromisoformat(before_date)
                    else:
                        end_dt = datetime.fromisoformat(before_date + "T23:59:59")
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    raise ValueError("Invalid before_date. Use YYYY-MM-DD or ISO 8601.")
            else:
                end_dt = now
            posts = scrape_subreddit_top_timesliced(
                subreddit_name=subreddit,
                end_dt=end_dt,
                lookback_days=lookback_days,
                slice_days=slice_days,
                per_slice=top_per_slice,
            )
        else:
            posts = scrape_subreddit(subreddit, cutoff_utc, max_posts)
        
        if not posts:
            print("\n❌ No posts found. Exiting.")
            return
        
        summarized = summarize_posts(posts)
        categorized = categorize_posts(summarized, FIXED_CATEGORIES)
        insights = generate_insights_llm_clustering(
            categorized,
            FIXED_CATEGORIES,
            min_cluster_size=min_cluster_size
        )
        output_path = save_outputs(subreddit, categorized, insights, lookback_days)
        generate_dashboard_json(subreddit, categorized, insights, output_path)
        
        elapsed = time.time() - start_time
        print(f"\n✅ Pipeline completed successfully in {elapsed:.1f}s")
        print(f"📁 Results: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        raise

# ==============================================================
# CLI INTERFACE
# ==============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reddit Clustering Pipeline with Azure OpenAI (LLM-based clustering)")
    parser.add_argument("--subreddit", "-s", default="MakeupAddiction", help="Subreddit to analyze")
    parser.add_argument("--max-posts", "-m", type=int, default=700, help="Maximum posts to scrape")
    parser.add_argument("--min-cluster", type=int, default=3, help="Minimum posts per cluster")
    # Time-slice options (optional)
    parser.add_argument("--before-date", type=str, help="End date (inclusive). YYYY-MM-DD or ISO 8601. Default: now")
    parser.add_argument("--slice-days", type=int, default=0, help="Time slice size in days (0 = disabled)")
    parser.add_argument("--top-per-slice", type=int, default=0, help="Top posts per slice by score (0 = disabled)")
    parser.add_argument("--lookback-days", type=int, default=365, help="Total lookback range in days (default: 365)")

    args = parser.parse_args()

    run_pipeline(
        subreddit=args.subreddit,
        max_posts=args.max_posts,
        min_cluster_size=args.min_cluster,
        before_date=args.before_date,
        slice_days=args.slice_days,
        top_per_slice=args.top_per_slice,
        lookback_days=args.lookback_days,
    )



