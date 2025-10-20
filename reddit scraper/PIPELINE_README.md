# Reddit Categorization & Insight Pipeline

A comprehensive pipeline that scrapes Reddit posts, uses OpenAI LLMs to generate categories, categorizes content, and generates high-quality insights.

## 🚀 Features

1. **Reddit Scraping**: Uses the same robust scraping method from `Scraper v1.py`
2. **LLM Category Generation**: Automatically generates meaningful category names from content
3. **Post Categorization**: Intelligently categorizes each post with confidence scores
4. **Insight Generation**: Creates detailed, actionable insights for each category
5. **Flexible Configuration**: Supports both auto-generated and human-provided categories

## 📋 Requirements

### API Credentials

You need two sets of credentials in your `.env` file:

```env
# Reddit API (from https://www.reddit.com/prefs/apps)
CLIENT_ID=your_reddit_client_id
CLIENT_SECRET=your_reddit_client_secret
USER_AGENT=python:YourApp:v1.0 (by /u/YourUsername)

# OpenAI API (from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-...
```

### Python Dependencies

```bash
pip install -r requirements_pipeline.txt
```

## 🎯 Usage

### Method 1: Command Line (Quick)

```bash
# Auto-generate categories
python categorization_pipeline.py --subreddit fashion

# Use predefined categories
python categorization_pipeline.py --subreddit fashion --categories "Street Style,Formal Wear,Thrift Finds,Sustainable Fashion"

# Limit posts and customize
python categorization_pipeline.py --subreddit streetwear --num-categories 6 --max-posts 200 --model gpt-4o
```

### Method 2: Configuration File (Recommended)

1. **Edit `pipeline_config.yaml`**:

```yaml
subreddit: "fashion"
num_auto_categories: 8
predefined_categories: []  # Leave empty for auto-generation
months_back: 6
min_score: 50
max_posts: null  # null = unlimited
```

2. **Run the pipeline**:

```bash
python run_pipeline.py
# Or with custom config:
python run_pipeline.py my_custom_config.yaml
```

### Method 3: Python Import

```python
from categorization_pipeline import run_pipeline

# Auto-generate categories
run_pipeline(subreddit="fashion", num_categories=8)

# Use predefined categories
categories = ["Street Style", "Formal Wear", "Thrift Finds"]
run_pipeline(subreddit="fashion", predefined_categories=categories)
```

## 📊 Output

The pipeline creates a timestamped folder with:

```
pipeline_output/
└── fashion_20241020_143022/
    ├── categorized_posts.jsonl      # Full post data with categories
    ├── posts_summary.csv             # Lightweight summary
    ├── categories.json               # List of categories
    ├── insights.json                 # Raw insights data
    └── REPORT.md                     # Human-readable report
```

### Example Report Structure

```markdown
# Reddit Analysis Report: r/fashion

**Generated:** 2024-10-20 14:30:22
**Total Posts Analyzed:** 342

## Categories
- Street Style: 89 posts (26.0%)
- Thrift Finds: 67 posts (19.6%)
- Outfit Questions: 54 posts (15.8%)
...

## Insights by Category

### Street Style
[Detailed 400-word insight about street style trends, engagement patterns, 
top themes, and actionable recommendations]

**Top Posts:**
1. **"My take on Y2K meets streetwear"** (1,234 score, 89 comments)
2. **"First time trying baggy fits"** (987 score, 67 comments)
...
```

## 🔧 Configuration Options

### Scraping Parameters

- `months_back`: How far back to scrape (default: 6 months)
- `min_score`: Minimum upvote threshold (default: 50)
- `min_num_comments`: Minimum comment count (default: 0)
- `fetch_all_comments`: Include full comment trees (default: true)
- `max_posts`: Limit total posts (default: unlimited)

### LLM Parameters

- `openai_model`: Model to use
  - `gpt-4o-mini` (default) - Fast, cost-effective
  - `gpt-4o` - More powerful, better quality
  - `gpt-4-turbo` - Balanced option
- `num_auto_categories`: Number of categories to generate (default: 8)
- `predefined_categories`: Human-provided category names (overrides auto-generation)

## 💡 Examples

### Example 1: Fashion Analysis with Auto Categories

```bash
python categorization_pipeline.py --subreddit fashion
```

Output categories might be:
- Street Style & Casual
- Formal & Business Wear
- Thrift & Vintage Finds
- Outfit Questions & Advice
- Shopping & Deals
- Sustainable Fashion
- Accessories & Details
- Inspiration & Mood Boards

### Example 2: Streetwear with Custom Categories

```yaml
# custom_streetwear.yaml
subreddit: "streetwear"
predefined_categories:
  - "Outfit Showcase"
  - "Sneaker Culture"
  - "Grails & Pickups"
  - "W2C & ID Requests"
  - "Discussion & News"
  - "Thrift & Budget"
```

```bash
python run_pipeline.py custom_streetwear.yaml
```

### Example 3: Quick Test Run

```bash
# Fast test with limited data
python categorization_pipeline.py \
  --subreddit malefashionadvice \
  --max-posts 100 \
  --num-categories 5 \
  --model gpt-4o-mini
```

## 🧪 Testing

Test the pipeline with a small dataset:

```bash
# Test with limited posts
python categorization_pipeline.py --subreddit fashion --max-posts 50

# Expected output:
# ✓ Scrape 50 posts
# ✓ Generate 8 categories
# ✓ Categorize all posts
# ✓ Generate 8 insight reports
# ✓ Save results to pipeline_output/
```

## 📈 Performance

- **Scraping**: ~5-10 posts/second (Reddit API limited)
- **Category Generation**: ~5-10 seconds (one-time per run)
- **Categorization**: ~1-2 seconds per batch (10 posts)
- **Insight Generation**: ~5-10 seconds per category

**Example timing for 300 posts**:
- Scraping: ~2-3 minutes
- Category generation: ~10 seconds
- Categorization: ~1-2 minutes
- Insight generation (8 categories): ~1 minute
- **Total: ~5-7 minutes**

## 💰 Cost Estimation

Using `gpt-4o-mini` (as of Oct 2024):
- Input: $0.150 / 1M tokens
- Output: $0.600 / 1M tokens

**Estimated cost for 300 posts**:
- Category generation: ~$0.01
- Categorization: ~$0.05
- Insight generation: ~$0.10
- **Total: ~$0.15-0.20 per run**

## 🐛 Troubleshooting

### "Missing OPENAI_API_KEY"
- Add your OpenAI API key to `.env`
- Get key from: https://platform.openai.com/api-keys

### "Missing Reddit credentials"
- Add Reddit API credentials to `.env`
- Create app at: https://www.reddit.com/prefs/apps

### "Rate limit exceeded"
- The pipeline includes automatic retry logic
- If persistent, increase sleep delays in code

### "No posts found"
- Lower `min_score` threshold
- Increase `months_back` time window
- Check subreddit name spelling

## 🔍 Advanced Usage

### Analyzing Existing Scraped Data

If you already have scraped data in JSONL format:

```python
import json
from categorization_pipeline import generate_categories, categorize_posts, generate_insights

# Load existing posts
posts = []
with open("existing_posts.jsonl") as f:
    for line in f:
        posts.append(json.loads(line))

# Run analysis only (skip scraping)
categories = generate_categories(posts, num_categories=8)
categorized = categorize_posts(posts, categories)
insights = generate_insights(categorized, categories)
```

### Custom Category Logic

```python
from categorization_pipeline import run_pipeline

# Mix of predefined and auto-generated
predefined = ["Hot Topics", "Beginner Questions"]
run_pipeline(
    subreddit="fashion",
    predefined_categories=predefined,
    num_categories=8  # Will generate 6 more to total 8
)
```

## 📚 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: SCRAPE                                             │
│  ├─ Use PRAW to fetch posts from subreddit                 │
│  ├─ Filter by score, time, comments                        │
│  └─ Fetch full comment trees                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: GENERATE CATEGORIES                                │
│  ├─ Sample 100 posts                                        │
│  ├─ Send to OpenAI LLM                                      │
│  └─ Get 8 category names                                    │
│     OR use predefined categories                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: CATEGORIZE POSTS                                   │
│  ├─ Process posts in batches of 10                         │
│  ├─ Send post content + categories to LLM                  │
│  └─ Assign category + confidence to each post              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: GENERATE INSIGHTS                                  │
│  ├─ For each category:                                      │
│  │   ├─ Collect all posts in category                      │
│  │   ├─ Calculate statistics                               │
│  │   ├─ Send to LLM for analysis                           │
│  │   └─ Get detailed insight report                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: SAVE RESULTS                                       │
│  ├─ categorized_posts.jsonl (full data)                    │
│  ├─ posts_summary.csv (summary table)                      │
│  ├─ categories.json (category list)                        │
│  ├─ insights.json (insights data)                          │
│  └─ REPORT.md (human-readable)                             │
└─────────────────────────────────────────────────────────────┘
```

## 🤝 Integration with Existing Scraper

This pipeline is fully compatible with `Scraper v1.py`:

- Uses identical Reddit authentication
- Same post data structure
- Can analyze previously scraped data
- Extends functionality without breaking existing workflow

## 📝 License

Same as parent project.

## 🙋 Support

For issues or questions, please refer to the main project documentation.

