# Quick Start - Reddit Categorization Pipeline

## 5-Minute Setup

### 1. Install
```bash
cd "reddit scraper"
pip install -r requirements_pipeline.txt
```

### 2. Configure (create `.env` file)
```bash
CLIENT_ID=your_reddit_client_id
CLIENT_SECRET=your_reddit_client_secret
USER_AGENT=python:AppName:v1.0 (by /u/username)
OPENAI_API_KEY=sk-your-openai-key
```

Get credentials:
- Reddit: https://www.reddit.com/prefs/apps (create "script" app)
- OpenAI: https://platform.openai.com/api-keys

### 3. Test
```bash
python test_pipeline.py
```

### 4. Run
```bash
# Quick test (50 posts)
python categorization_pipeline.py --subreddit fashion --max-posts 50

# Full analysis
python categorization_pipeline.py --subreddit fashion
```

---

## Common Commands

### Auto-generate categories
```bash
python categorization_pipeline.py --subreddit fashion
```

### Use your own categories
```bash
python categorization_pipeline.py --subreddit fashion \
  --categories "Street Style,Formal Wear,Thrift Finds,Outfit Questions"
```

### Quick test (recommended first time)
```bash
python categorization_pipeline.py --subreddit fashion --max-posts 50
```

### Use config file
```bash
# Edit pipeline_config.yaml first
python run_pipeline.py
```

### Run example
```bash
python example_usage.py 4  # Quick test example
```

---

## Output Location

Results saved to: `pipeline_output/SUBREDDIT_TIMESTAMP/`

Key files:
- `REPORT.md` - **Start here!** Human-readable insights
- `posts_summary.csv` - Open in Excel/Sheets
- `categorized_posts.jsonl` - Full data (for analysis)
- `insights.json` - Raw insights (for processing)

---

## Troubleshooting

**"No module named 'praw'"**
```bash
pip install -r requirements_pipeline.txt
```

**"Missing Reddit credentials"**
- Create `.env` file in `reddit scraper/` folder
- Add CLIENT_ID, CLIENT_SECRET, USER_AGENT

**"Missing OPENAI_API_KEY"**
- Add OPENAI_API_KEY to `.env` file
- Get from: https://platform.openai.com/api-keys

**"No posts found"**
- Lower min_score in config: `min_score: 25`
- Or increase time window: `months_back: 12`

---

## Configuration

Edit `pipeline_config.yaml`:

```yaml
# Required
subreddit: "fashion"

# Categories (choose one)
predefined_categories: []  # Empty = auto-generate
# OR
predefined_categories:
  - "Street Style"
  - "Formal Wear"
  - "Thrift Finds"

# Optional
num_auto_categories: 8  # If auto-generating
max_posts: null         # null = unlimited
months_back: 6          # How far back to scrape
min_score: 50          # Minimum upvotes
openai_model: "gpt-4o-mini"  # Cost-effective
```

---

## Cost Estimate

Using `gpt-4o-mini` (default):
- 50 posts: ~$0.03
- 300 posts: ~$0.15-0.20
- 1000 posts: ~$0.50-0.75

💡 Start with 50 posts to test before scaling up!

---

## Pipeline Steps

```
1. SCRAPE posts from subreddit
   └─ Filters by score, time window, comments
   
2. GENERATE categories (LLM)
   └─ Auto-generates 8 categories from content
   └─ OR uses your predefined categories
   
3. CATEGORIZE each post (LLM)
   └─ Assigns category + confidence score
   
4. GENERATE insights (LLM)
   └─ 300-500 word analysis per category
   
5. SAVE results
   └─ JSONL, CSV, JSON, Markdown
```

---

## Full Documentation

- `SETUP_GUIDE.md` - Detailed setup instructions
- `PIPELINE_README.md` - Complete documentation
- `PIPELINE_SUMMARY.md` - Implementation overview
- `test_pipeline.py` - Run to verify setup

---

## Support

1. Run diagnostics: `python test_pipeline.py`
2. Check documentation in folder
3. Review example_usage.py for code examples

Happy analyzing! 🚀

