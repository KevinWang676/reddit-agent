import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

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
OUTPUT_DIR = Path("reddit_fashion_out")  
TOP_POSTS_PER_MONTH = 5 

dfs = []
for sub in SUBREDDITS:
    path = OUTPUT_DIR / sub / "posts_summary.csv"
    if path.exists():
        df = pd.read_csv(path)
        df['subreddit'] = sub
        dfs.append(df)
    else:
        print(f"[WARN] File not found for {sub}: {path}")

if not dfs:
    raise RuntimeError("No subreddit data found!")

data = pd.concat(dfs, ignore_index=True)

data['created_iso'] = pd.to_datetime(data['created_iso'], errors='coerce')
data['month'] = data['created_iso'].dt.to_period("M")

print("Total posts loaded:", len(data))
print("Subreddit counts:\n", data['subreddit'].value_counts())

posts_per_month = data.groupby(['subreddit', 'month']).size().unstack(0).fillna(0)
posts_per_month.plot(marker="o", figsize=(12,6))
plt.title("Posts per month by subreddit")
plt.ylabel("Number of posts")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# -----------------------
# Average Score per Post
# -----------------------
avg_score = data.groupby(['subreddit', 'month'])['score'].mean().unstack(0)
avg_score.plot(marker="o", figsize=(12,6))
plt.title("Average score per post (by month)")
plt.ylabel("Avg. Score")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# -----------------------
# Average Comments per Post
# -----------------------
avg_comments = data.groupby(['subreddit', 'month'])['num_comments'].mean().unstack(0)
avg_comments.plot(marker="o", figsize=(12,6))
plt.title("Average comments per post (by month)")
plt.ylabel("Avg. Comments")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# -----------------------
# Flair Distribution (top 10)
# -----------------------
if "link_flair_text" in data.columns:
    flair_counts = (
        data.groupby(['subreddit', 'link_flair_text']).size()
        .reset_index(name='count')
        .sort_values('count', ascending=False)
    )

    plt.figure(figsize=(12,6))
    sns.barplot(
        data=flair_counts.groupby("link_flair_text").sum()
             .nlargest(10, "count")
             .reset_index(),
        x="count", y="link_flair_text", palette="muted"
    )
    plt.title("Top 10 flairs across all subreddits")
    plt.xlabel("Post count")
    plt.ylabel("Flair")
    plt.tight_layout()
    plt.show()

# -----------------------
# Top Posts Extraction
# -----------------------
# Rank posts by score each month per subreddit
top_posts = (
    data.sort_values(['month','score'], ascending=[True,False])
    .groupby(['subreddit','month'])
    .head(TOP_POSTS_PER_MONTH)
    .reset_index(drop=True)
)

# Save to CSV for later LLM/NLP analysis
out_path = OUTPUT_DIR / "top_posts_by_month.csv"
top_posts.to_csv(out_path, index=False, encoding="utf-8")
print(f"Saved top posts per month to: {out_path}")

# Quick look
print(top_posts[['month','subreddit','title','score','num_comments']].head(15))
