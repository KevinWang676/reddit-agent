# Reddit Insights Dashboard

A professional, enterprise-grade platform for analyzing Reddit discussions with AI-powered insights and multi-subreddit support.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- Reddit API credentials
- Azure OpenAI credentials

### 1. Setup Environment Variables

Create a `.env` file in this directory:

```bash
# Reddit API Credentials (from https://www.reddit.com/prefs/apps)
CLIENT_ID=your_reddit_client_id
CLIENT_SECRET=your_reddit_client_secret
USER_AGENT=python:RedditPipeline:v4.0

# Azure OpenAI Credentials (from https://portal.azure.com)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### 2. Install Dependencies

**Backend:**
```bash
cd backend
pip install fastapi uvicorn pydantic
cd ..
```

**Pipeline Dependencies:**
```bash
pip install praw tqdm python-dotenv openai
```

**Frontend:**
```bash
cd frontend
npm install
```

### 3. Start Services

**Terminal 1 - Backend:**
```bash
./start-backend.sh
# Or manually: cd backend && uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
./start-frontend.sh
# Or manually: cd frontend && npm run dev
```

### 4. Access Dashboard

Open your browser: **http://localhost:5173**

## ✨ Features

### One-Click Pipeline Execution
- Run Reddit analysis pipelines directly from the UI
- No command-line required
- Real-time job status tracking
- Automatic result loading

### Multi-Subreddit Support
- Analyze multiple subreddits with tab navigation
- Each subreddit maintains independent data
- Switch between dashboards instantly
- All data persists across restarts

### Smart Update Mode
- Update existing dashboards with one click
- System automatically calculates optimal date range
- Only need to set max posts - that's it!
- Fetches posts since last run with 7-day buffer
- Creates fresh independent clusters each time

### Professional UI
- Modern gradient design
- Real-time status updates
- Interactive charts and visualizations
- Sortable tables
- Responsive layout

## 📖 Usage

### Create New Dashboard

1. Click **"+ New Pipeline"**
2. Enter subreddit name (e.g., "MakeupAddiction")
3. Configure parameters:
   - **Lookback Days**: How far back to analyze (default: 365)
   - **Max Posts**: Maximum posts to scrape (default: 700)
   - **Min Cluster Size**: Minimum posts per cluster (default: 3)
4. Click **"Run Pipeline"**
5. Wait 5-15 minutes for completion
6. Results appear automatically in a new tab

### Update Existing Dashboard

1. Select a subreddit tab
2. Click green **"Update"** button
3. Set **max posts** (default: 700)
   - System automatically calculates date range
   - Fetches posts since your last run
   - No date math required!
4. Click **"Update Dashboard"**
5. Wait for completion
6. Updated insights appear automatically

### View Insights

- **Home View**: Browse all insights grouped by category
- **Sort**: By posts, engagement, or default order
- **Expand Categories**: Click to see insights in each category
- **Detail View**: Click any insight card for detailed analysis with charts
- **Posts Table**: View all source posts with clickable Reddit links

## 🎯 Key Concepts

### Independent Clustering

Each pipeline run (new or update) analyzes posts **independently**:
- Fresh LLM-based semantic clustering
- New themes automatically form new clusters
- No merging with previous runs
- Clean per-period analysis

Think of it as: "What are people discussing **this period**?" not "What changed from last period?"

### Version Management

Each run creates a timestamped directory:
```
pipeline_output/
├── MakeupAddiction_20251113_213310/  ← Run 1
├── MakeupAddiction_20251114_102030/  ← Run 2 (Update)
└── SkincareAddiction_20251114_120000/  ← Different subreddit
```

- Dashboard always shows **latest** version
- Old versions preserved for history
- Each run is self-contained

### Auto-Synchronization

- Dashboard auto-refreshes every 10 seconds
- New tabs appear automatically after pipeline completion
- No manual refresh needed
- Multi-browser sync support

## 🔧 API Endpoints

The backend provides these REST endpoints:

**Pipeline Management:**
- `POST /pipeline/run` - Trigger pipeline execution
- `GET /pipeline/status/{job_id}` - Get job status
- `GET /pipeline/jobs` - List all jobs

**Data Access:**
- `GET /subreddits` - List all available subreddits
- `GET /data/{subreddit}` - Get full dashboard data
- `GET /data/{subreddit}/metadata` - Get metadata
- `GET /data/{subreddit}/categories` - Get categories
- `GET /data/{subreddit}/insights` - Get all insights
- `GET /data/{subreddit}/insights/{id}` - Get specific insight
- `GET /data/{subreddit}/history` - Get all historical runs

**Health:**
- `GET /health` - Health check
- `GET /` - API info

## 🐛 Troubleshooting

### Backend won't start

**Check:**
- All Python dependencies installed: `pip install fastapi uvicorn pydantic praw tqdm python-dotenv openai`
- `.env` file exists in the parent directory
- Port 8000 is available

**Test:**
```bash
curl http://127.0.0.1:8000/health
```

### Frontend won't start

**Check:**
- Node dependencies installed: `cd frontend && npm install`
- Backend is running on port 8000
- Port 5173 is available

### Pipeline fails immediately

**Check:**
- `.env` file has valid credentials
- Reddit API credentials are correct
- Azure OpenAI credentials are correct

**Verify credentials:**
```bash
python -c "import praw; import os; from dotenv import load_dotenv; load_dotenv(); reddit = praw.Reddit(client_id=os.getenv('CLIENT_ID'), client_secret=os.getenv('CLIENT_SECRET'), user_agent=os.getenv('USER_AGENT')); print('✓ Reddit auth OK' if reddit.read_only else '✗ Auth failed')"
```

### No data appears after pipeline completes

**Check:**
- Backend logs for errors
- Look for `pipeline_output/{subreddit}_{timestamp}/` directory
- Check if `dashboard_data.json` exists in the directory
- Wait 10 seconds for auto-refresh or restart frontend

### Update button doesn't appear

**Check:**
- Make sure a subreddit tab is selected
- Button only shows when activeSubreddit is set

## 📊 Architecture

```
Frontend (React + Vite)
    ↓ HTTP
Backend (FastAPI)
    ↓ Subprocess
Pipeline Script (Python)
    ↓ API Calls
Reddit API + Azure OpenAI
    ↓ Results
File System (pipeline_output/)
```

## 🔐 Security Notes

- Keep `.env` file secure and never commit it
- The backend allows CORS from all origins (development only)
- For production: restrict CORS, add authentication
- GitHub tokens should never be shared publicly

## 📈 Performance

**Typical Pipeline Execution:**
- 100 posts: ~2-5 minutes
- 500 posts: ~5-10 minutes
- 1000 posts: ~10-20 minutes

**Factors:**
- Number of posts to process
- Azure OpenAI API rate limits
- Reddit API rate limits
- Batch processing (10 posts per call)

## 🎯 Use Cases

- **Brand Monitoring**: Track sentiment about products
- **Trend Analysis**: Identify emerging topics
- **Competitive Intelligence**: Compare multiple communities
- **Customer Research**: Understand pain points and needs
- **Content Strategy**: Find high-engagement themes
- **Product Development**: Discover feature requests

## 📝 Data Output

Each pipeline run generates:
- `posts.jsonl` - All scraped posts
- `posts_summary.csv` - Posts summary table
- `categories.json` - List of categories
- `insights.json` - Generated insights
- `dashboard_data.json` - Complete dashboard data
- `REPORT.md` - Markdown report

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backend terminal logs for errors
3. Check browser console for frontend errors
4. Verify `.env` file configuration

## 📄 License

See LICENSE file in the repository.

---

**Version:** 2.3.1  
**Status:** Production Ready  
**Last Updated:** November 2024

