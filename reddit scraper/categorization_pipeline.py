"""
Reddit Content Categorization & Insight Pipeline

This pipeline:
1. Scrapes posts from specified subreddits using PRAW
2. Uses OpenAI LLM to generate category names from content (or accepts predefined categories)
3. Categorizes each post using OpenAI LLM
4. Generates high-quality insights for each category using OpenAI LLM

Usage:
    python categorization_pipeline.py --subreddit fashion --categories "Street Style,Formal Wear,Thrift Finds"
    python categorization_pipeline.py --subreddit fashion  # Auto-generate categories
"""

import os
import json
import csv
import time
import pathlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
import argparse

from dotenv import load_dotenv
import praw
from prawcore import RequestException, ResponseException, Forbidden, ServerError
from openai import OpenAI
from tqdm import tqdm

# -----------------------------
# Configuration
# -----------------------------
load_dotenv()

# Reddit API credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USER_AGENT = os.getenv("USER_AGENT")

# OpenAI credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Pipeline settings
MONTHS_BACK = 6  # Shorter window for focused analysis
MIN_SCORE = 50
MIN_NUM_COMMENTS = 0
FETCH_ALL_COMMENTS = True
OUTPUT_DIR = "pipeline_output"
LOG_EVERY = 20

# LLM settings
DEFAULT_MODEL = "gpt-4o-mini"  # Cost-effective for analysis
NUM_CATEGORIES = 8  # Default number of auto-generated categories
MAX_POSTS_FOR_CATEGORY_GEN = 100  # Sample size for category generation
BATCH_SIZE = 10  # Posts to categorize per API call

# -----------------------------
# Validation
# -----------------------------
if not all([CLIENT_ID, CLIENT_SECRET, USER_AGENT]):
    raise RuntimeError("Missing Reddit credentials in .env: CLIENT_ID, CLIENT_SECRET, USER_AGENT")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")

# -----------------------------
# Initialize APIs
# -----------------------------
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
    check_for_async=False
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

print(f"✓ Reddit initialized (read-only mode)")
print(f"✓ OpenAI initialized with model: {DEFAULT_MODEL}")

# -----------------------------
# Utility Functions
# -----------------------------
def ensure_dir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def backoff_sleep(attempt):
    delay = min(60, (2 ** attempt)) + 0.25 * attempt
    time.sleep(delay)

def safe_llm_call(func, max_retries=3):
    """Wrapper for OpenAI API calls with retry logic"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"[WARN] LLM API error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

# -----------------------------
# Scraping Functions (adapted from Scraper v1.py)
# -----------------------------
def submission_to_post_dict(s):
    """Convert PRAW submission to structured dict"""
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
    }

def fetch_all_comments(submission):
    """Expand full comment tree"""
    submission.comments.replace_more(limit=None)
    out = []
    for c in submission.comments.list():
        out.append({
            "id": c.id,
            "author": str(c.author) if getattr(c, "author", None) else None,
            "body": c.body,
            "score": int(getattr(c, "score", 0) or 0),
            "created_utc": int(c.created_utc),
        })
    return out

def scrape_subreddit(subreddit_name: str, cutoff_utc: int, max_posts: Optional[int] = None) -> List[Dict]:
    """
    Scrape posts from a subreddit
    
    Args:
        subreddit_name: Name of subreddit to scrape
        cutoff_utc: Unix timestamp - stop scraping posts older than this
        max_posts: Optional limit on number of posts to scrape
    
    Returns:
        List of post dictionaries
    """
    print(f"\n{'='*60}")
    print(f"STEP 1: Scraping r/{subreddit_name}")
    print(f"{'='*60}")
    
    posts = []
    processed = 0
    
    try:
        submissions = reddit.subreddit(subreddit_name).new(limit=None)
        
        with tqdm(desc=f"Scraping r/{subreddit_name}", unit="post") as pbar:
            for subm in submissions:
                processed += 1
                pbar.update(1)
                
                # Stop conditions
                if int(subm.created_utc) < cutoff_utc:
                    break
                if max_posts and len(posts) >= max_posts:
                    break
                
                # Filter by popularity
                if subm.score < MIN_SCORE:
                    continue
                if MIN_NUM_COMMENTS > 0 and subm.num_comments < MIN_NUM_COMMENTS:
                    continue
                
                # Convert to dict
                post_rec = submission_to_post_dict(subm)
                
                # Fetch comments if requested
                if FETCH_ALL_COMMENTS:
                    try:
                        comments = fetch_all_comments(subm)
                        post_rec["comments"] = comments
                    except Exception as e:
                        print(f"[WARN] Comments failed for {subm.id}: {e}")
                        post_rec["comments"] = []
                
                posts.append(post_rec)
                
                if len(posts) % LOG_EVERY == 0:
                    print(f"  Scraped {len(posts)} posts so far...")
    
    except Exception as e:
        print(f"[ERROR] Scraping error: {e}")
    
    print(f"\n✓ Scraped {len(posts)} posts from r/{subreddit_name} (processed {processed} total)")
    return posts

# -----------------------------
# LLM Category Generation
# -----------------------------
def generate_categories(posts: List[Dict], num_categories: int = NUM_CATEGORIES, 
                       predefined_categories: Optional[List[str]] = None) -> List[str]:
    """
    Generate category names using OpenAI based on post content
    
    Args:
        posts: List of post dictionaries
        num_categories: Number of categories to generate
        predefined_categories: Optional list of human-provided categories
    
    Returns:
        List of category names
    """
    print(f"\n{'='*60}")
    print(f"STEP 2: Category Generation")
    print(f"{'='*60}")
    
    if predefined_categories:
        print(f"✓ Using {len(predefined_categories)} predefined categories:")
        for cat in predefined_categories:
            print(f"  - {cat}")
        return predefined_categories
    
    # Check if we have posts to analyze
    if not posts:
        print("[WARN] No posts available for category generation")
        print("Returning empty category list")
        return []
    
    # Sample posts for category generation
    sample_posts = posts[:MAX_POSTS_FOR_CATEGORY_GEN]
    
    # Prepare post summaries for LLM
    post_summaries = []
    for post in sample_posts:
        summary = f"Title: {post['title']}"
        if post.get('selftext'):
            summary += f"\nContent: {post['selftext'][:200]}..."
        if post.get('link_flair_text'):
            summary += f"\nFlair: {post['link_flair_text']}"
        post_summaries.append(summary)
    
    posts_text = "\n\n---\n\n".join(post_summaries[:50])  # Limit for token size
    
    prompt = f"""You are analyzing posts from a subreddit to identify the main themes and topics.

Based on the following sample posts, generate {num_categories} distinct, meaningful category names that best represent the different types of content.

Requirements:
- Categories should be specific and descriptive (2-4 words each)
- Categories should cover diverse aspects of the content
- Categories should be mutually exclusive where possible
- Use title case (e.g., "Street Style", "Thrift Finds")
- Return ONLY the category names, one per line, no numbering or explanation

Sample Posts:
{posts_text}

Generate {num_categories} category names:"""
    
    print(f"Generating categories from {len(sample_posts)} sample posts...")
    
    def call_openai():
        response = openai_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert at content categorization and thematic analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    
    categories_text = safe_llm_call(call_openai)
    categories = [cat.strip() for cat in categories_text.split('\n') if cat.strip()]
    
    # Clean up any numbering or bullets
    categories = [cat.lstrip('0123456789.-) ').strip() for cat in categories]
    categories = [cat for cat in categories if len(cat) > 2][:num_categories]
    
    print(f"\n✓ Generated {len(categories)} categories:")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")
    
    return categories

# -----------------------------
# LLM Post Categorization
# -----------------------------
def categorize_posts(posts: List[Dict], categories: List[str]) -> List[Dict]:
    """
    Categorize each post into one of the generated categories
    
    Args:
        posts: List of post dictionaries
        categories: List of category names
    
    Returns:
        List of posts with 'category' and 'category_confidence' fields added
    """
    print(f"\n{'='*60}")
    print(f"STEP 3: Post Categorization")
    print(f"{'='*60}")
    
    categories_list = "\n".join([f"{i+1}. {cat}" for i, cat in enumerate(categories)])
    categorized_posts = []
    
    # Process in batches for efficiency
    with tqdm(total=len(posts), desc="Categorizing posts", unit="post") as pbar:
        for i in range(0, len(posts), BATCH_SIZE):
            batch = posts[i:i+BATCH_SIZE]
            
            # Prepare batch prompt
            posts_for_prompt = []
            for j, post in enumerate(batch):
                post_text = f"POST_{j+1}:\n"
                post_text += f"Title: {post['title']}\n"
                if post.get('selftext'):
                    post_text += f"Content: {post['selftext'][:300]}...\n"
                if post.get('link_flair_text'):
                    post_text += f"Flair: {post['link_flair_text']}\n"
                # Include top comments for context
                if post.get('comments'):
                    top_comments = sorted(post['comments'], key=lambda x: x['score'], reverse=True)[:3]
                    if top_comments:
                        post_text += "Top comments:\n"
                        for comment in top_comments:
                            post_text += f"  - {comment['body'][:100]}...\n"
                posts_for_prompt.append(post_text)
            
            batch_text = "\n\n".join(posts_for_prompt)
            
            prompt = f"""Categorize each post into ONE of the following categories:

{categories_list}

For each post, respond with ONLY the category number (1-{len(categories)}) followed by a confidence score (0.0-1.0).
Format: POST_X: <category_number> <confidence>

Example response:
POST_1: 3 0.85
POST_2: 1 0.92

Posts to categorize:
{batch_text}

Your categorization:"""
            
            def call_openai():
                response = openai_client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert content categorizer. Analyze each post carefully and assign it to the most appropriate category."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                return response.choices[0].message.content.strip()
            
            result = safe_llm_call(call_openai)
            
            # Parse results
            lines = result.split('\n')
            for j, post in enumerate(batch):
                # Find the line for this post
                post_line = None
                for line in lines:
                    if f"POST_{j+1}:" in line:
                        post_line = line
                        break
                
                if post_line:
                    try:
                        # Parse: "POST_X: 3 0.85"
                        parts = post_line.split(':')[1].strip().split()
                        cat_num = int(parts[0])
                        confidence = float(parts[1]) if len(parts) > 1 else 0.8
                        
                        if 1 <= cat_num <= len(categories):
                            post['category'] = categories[cat_num - 1]
                            post['category_confidence'] = confidence
                        else:
                            post['category'] = "Uncategorized"
                            post['category_confidence'] = 0.0
                    except:
                        post['category'] = "Uncategorized"
                        post['category_confidence'] = 0.0
                else:
                    post['category'] = "Uncategorized"
                    post['category_confidence'] = 0.0
                
                categorized_posts.append(post)
            
            pbar.update(len(batch))
            time.sleep(0.5)  # Rate limiting
    
    # Print categorization summary
    category_counts = {}
    for post in categorized_posts:
        cat = post.get('category', 'Uncategorized')
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print(f"\n✓ Categorization complete:")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count} posts")
    
    return categorized_posts

# -----------------------------
# LLM Insight Generation
# -----------------------------
def generate_insights(posts: List[Dict], categories: List[str]) -> Dict[str, str]:
    """
    Generate insights for each category using OpenAI
    
    Args:
        posts: List of categorized post dictionaries
        categories: List of category names
    
    Returns:
        Dictionary mapping category names to insight text
    """
    print(f"\n{'='*60}")
    print(f"STEP 4: Insight Generation")
    print(f"{'='*60}")
    
    insights = {}
    
    for category in tqdm(categories, desc="Generating insights", unit="category"):
        # Get posts in this category
        cat_posts = [p for p in posts if p.get('category') == category]
        
        if not cat_posts:
            insights[category] = "No posts found in this category."
            continue
        
        # Prepare post data for LLM
        posts_summary = []
        for post in cat_posts[:50]:  # Limit to top 50 posts per category
            summary = f"• {post['title']} (Score: {post['score']}, Comments: {post['num_comments']})"
            if post.get('selftext'):
                summary += f"\n  Content: {post['selftext'][:200]}..."
            posts_summary.append(summary)
        
        posts_text = "\n\n".join(posts_summary)
        
        # Calculate stats
        total_posts = len(cat_posts)
        avg_score = sum(p['score'] for p in cat_posts) / len(cat_posts)
        avg_comments = sum(p['num_comments'] for p in cat_posts) / len(cat_posts)
        top_post = max(cat_posts, key=lambda x: x['score'])
        
        prompt = f"""You are analyzing posts from the "{category}" category. Generate a comprehensive, high-quality insight report.

Category: {category}
Total Posts: {total_posts}
Average Score: {avg_score:.1f}
Average Comments: {avg_comments:.1f}

Top Post: "{top_post['title']}" ({top_post['score']} score)

Sample Posts:
{posts_text}

Generate a detailed insight report (300-500 words) covering:
1. Main themes and patterns in this category
2. Common user interests and pain points
3. Engagement trends (what gets upvoted/discussed)
4. Notable examples and standout content
5. Actionable insights for content creators or community managers

Be specific, data-driven, and provide actionable insights:"""
        
        def call_openai():
            response = openai_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert data analyst specializing in social media insights and community analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        
        insight = safe_llm_call(call_openai)
        insights[category] = insight
        
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n✓ Generated insights for {len(insights)} categories")
    return insights

# -----------------------------
# Output Functions
# -----------------------------
def save_results(subreddit: str, posts: List[Dict], categories: List[str], 
                insights: Dict[str, str], output_dir: str):
    """Save all pipeline results to files"""
    print(f"\n{'='*60}")
    print(f"STEP 5: Saving Results")
    print(f"{'='*60}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sub_dir = os.path.join(output_dir, f"{subreddit}_{timestamp}")
    ensure_dir(sub_dir)
    
    # 1. Save categorized posts (JSONL)
    posts_path = os.path.join(sub_dir, "categorized_posts.jsonl")
    with open(posts_path, "w", encoding="utf-8") as f:
        for post in posts:
            f.write(json.dumps(post, ensure_ascii=False) + "\n")
    print(f"✓ Saved {len(posts)} posts to: {posts_path}")
    
    # 2. Save posts summary (CSV)
    csv_path = os.path.join(sub_dir, "posts_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "created_iso", "title", "author", "score", "num_comments",
            "category", "category_confidence", "link_flair_text"
        ])
        for post in posts:
            writer.writerow([
                post['id'],
                post['created_iso'],
                post['title'],
                post['author'],
                post['score'],
                post['num_comments'],
                post.get('category', 'Uncategorized'),
                post.get('category_confidence', 0.0),
                post.get('link_flair_text', '')
            ])
    print(f"✓ Saved summary CSV to: {csv_path}")
    
    # 3. Save categories
    categories_path = os.path.join(sub_dir, "categories.json")
    with open(categories_path, "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(categories)} categories to: {categories_path}")
    
    # 4. Save insights
    insights_path = os.path.join(sub_dir, "insights.json")
    with open(insights_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved insights to: {insights_path}")
    
    # 5. Generate human-readable report
    report_path = os.path.join(sub_dir, "REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Reddit Analysis Report: r/{subreddit}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Posts Analyzed:** {len(posts)}\n\n")
        f.write(f"**Time Range:** {MONTHS_BACK} months\n\n")
        f.write(f"**Filters:** Min Score = {MIN_SCORE}, Min Comments = {MIN_NUM_COMMENTS}\n\n")
        
        f.write("---\n\n")
        f.write("## Categories\n\n")
        
        # Category distribution
        category_counts = {}
        for post in posts:
            cat = post.get('category', 'Uncategorized')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        for cat in categories:
            count = category_counts.get(cat, 0)
            pct = (count / len(posts) * 100) if posts else 0
            f.write(f"- **{cat}**: {count} posts ({pct:.1f}%)\n")
        
        f.write("\n---\n\n")
        f.write("## Insights by Category\n\n")
        
        for category in categories:
            f.write(f"### {category}\n\n")
            f.write(insights.get(category, "No insights generated."))
            f.write("\n\n")
            
            # Add top 3 posts from this category
            cat_posts = [p for p in posts if p.get('category') == category]
            if cat_posts:
                cat_posts.sort(key=lambda x: x['score'], reverse=True)
                f.write("**Top Posts:**\n\n")
                for i, post in enumerate(cat_posts[:3], 1):
                    f.write(f"{i}. **{post['title']}** ({post['score']} score, {post['num_comments']} comments)\n")
                    if post.get('selftext'):
                        f.write(f"   > {post['selftext'][:150]}...\n")
                f.write("\n")
            
            f.write("---\n\n")
    
    print(f"✓ Saved readable report to: {report_path}")
    print(f"\n{'='*60}")
    print(f"✅ All results saved to: {sub_dir}")
    print(f"{'='*60}")
    
    return sub_dir

# -----------------------------
# Main Pipeline
# -----------------------------
def run_pipeline(subreddit: str, predefined_categories: Optional[List[str]] = None,
                num_categories: int = NUM_CATEGORIES, max_posts: Optional[int] = None):
    """
    Execute the complete categorization and insight pipeline
    
    Args:
        subreddit: Name of subreddit to analyze
        predefined_categories: Optional list of human-provided category names
        num_categories: Number of categories to auto-generate (if no predefined)
        max_posts: Optional limit on posts to scrape
    """
    print(f"\n{'#'*60}")
    print(f"# Reddit Categorization & Insight Pipeline")
    print(f"# Subreddit: r/{subreddit}")
    print(f"# Model: {DEFAULT_MODEL}")
    print(f"{'#'*60}\n")
    
    start_time = time.time()
    
    # Calculate time window
    now = datetime.now(tz=timezone.utc)
    cutoff_dt = now - timedelta(days=30 * MONTHS_BACK)
    cutoff_utc = int(cutoff_dt.timestamp())
    
    print(f"Time window: {cutoff_dt.date()} → {now.date()}")
    print(f"Filters: MIN_SCORE={MIN_SCORE}, MIN_NUM_COMMENTS={MIN_NUM_COMMENTS}")
    
    try:
        # Step 1: Scrape posts
        posts = scrape_subreddit(subreddit, cutoff_utc, max_posts)
        
        if not posts:
            print("\n❌ No posts found. Exiting.")
            return
        
        # Step 2: Generate or use predefined categories
        categories = generate_categories(posts, num_categories, predefined_categories)
        
        if not categories:
            print("\n❌ No categories generated. Exiting.")
            return
        
        # Step 3: Categorize posts
        categorized_posts = categorize_posts(posts, categories)
        
        # Step 4: Generate insights
        insights = generate_insights(categorized_posts, categories)
        
        # Step 5: Save results
        output_path = save_results(subreddit, categorized_posts, categories, insights, OUTPUT_DIR)
        
        elapsed = time.time() - start_time
        print(f"\n✅ Pipeline completed successfully in {elapsed:.1f}s")
        print(f"📁 Results: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        raise

# -----------------------------
# CLI Interface
# -----------------------------
def main():
    global DEFAULT_MODEL
    
    parser = argparse.ArgumentParser(
        description="Reddit Content Categorization & Insight Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-generate categories
  python categorization_pipeline.py --subreddit fashion
  
  # Use predefined categories
  python categorization_pipeline.py --subreddit fashion --categories "Street Style,Formal Wear,Thrift Finds"
  
  # Limit posts and specify number of categories
  python categorization_pipeline.py --subreddit streetwear --num-categories 6 --max-posts 200
        """
    )
    
    parser.add_argument(
        "--subreddit", "-s",
        required=True,
        help="Subreddit name to analyze (without r/)"
    )
    
    parser.add_argument(
        "--categories", "-c",
        type=str,
        default=None,
        help="Comma-separated predefined category names (e.g., 'Style A,Style B,Style C')"
    )
    
    parser.add_argument(
        "--num-categories", "-n",
        type=int,
        default=NUM_CATEGORIES,
        help=f"Number of categories to auto-generate (default: {NUM_CATEGORIES})"
    )
    
    parser.add_argument(
        "--max-posts", "-m",
        type=int,
        default=None,
        help="Maximum number of posts to scrape (default: unlimited)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use (default: {DEFAULT_MODEL})"
    )
    
    args = parser.parse_args()
    
    # Parse categories if provided
    predefined_cats = None
    if args.categories:
        predefined_cats = [cat.strip() for cat in args.categories.split(',') if cat.strip()]
    
    # Update global model if specified
    DEFAULT_MODEL = args.model
    
    # Run pipeline
    run_pipeline(
        subreddit=args.subreddit,
        predefined_categories=predefined_cats,
        num_categories=args.num_categories,
        max_posts=args.max_posts
    )

if __name__ == "__main__":
    main()

