from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import sys
import subprocess
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import threading

app = FastAPI(title="Reddit Insights Dashboard API")

# === CORS Configuration ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Paths Configuration ===
BACKEND_DIR = Path(__file__).parent
PIPELINE_SCRIPT = BACKEND_DIR.parent / "Updated_azure_pipeline_nov_11.py"
PIPELINE_OUTPUT_DIR = BACKEND_DIR.parent / "pipeline_output"

# === Job Tracking ===
jobs: Dict[str, Dict] = {}
subreddit_data: Dict[str, Dict] = {}  # subreddit_name -> latest data

# === Request Models ===
class PipelineRequest(BaseModel):
    subreddit: str
    lookback_days: int = 365
    max_posts: int = 700
    min_cluster: int = 3
    slice_days: int = 0
    top_per_slice: int = 0
    before_date: Optional[str] = None  # For incremental updates
    is_update: bool = False  # Flag to indicate this is an update (auto-calculate dates)

# === Helper Functions ===
def load_dashboard_data(output_path: Path) -> Optional[Dict]:
    """Load dashboard_data.json from pipeline output directory"""
    dashboard_file = output_path / "dashboard_data.json"
    if dashboard_file.exists():
        with open(dashboard_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def find_latest_output(subreddit: str) -> Optional[Path]:
    """Find the latest output directory for a subreddit"""
    if not PIPELINE_OUTPUT_DIR.exists():
        return None
    
    # Find all directories matching subreddit pattern
    matching_dirs = []
    for item in PIPELINE_OUTPUT_DIR.iterdir():
        if item.is_dir() and item.name.startswith(f"{subreddit}_"):
            matching_dirs.append(item)
    
    if not matching_dirs:
        return None
    
    # Sort by modification time and return latest
    matching_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return matching_dirs[0]

def run_pipeline_process(job_id: str, request: PipelineRequest):
    """Run the pipeline script as a subprocess"""
    import time
    from datetime import datetime as dt, timedelta, timezone
    
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        # Auto-calculate date range for updates
        calculated_lookback = request.lookback_days
        calculated_before_date = request.before_date
        
        if request.is_update and request.subreddit in subreddit_data:
            print(f"\n🔄 UPDATE MODE: Auto-calculating date range")
            
            # Get the last run's end date
            posts = subreddit_data[request.subreddit]["data"].get("posts", [])
            if posts:
                dates = [p.get("created_iso") for p in posts if p.get("created_iso")]
                if dates:
                    dates.sort()
                    last_end_date_str = dates[-1]
                    
                    try:
                        last_end_dt = dt.fromisoformat(last_end_date_str)
                        if last_end_dt.tzinfo is None:
                            last_end_dt = last_end_dt.replace(tzinfo=timezone.utc)
                        
                        # Calculate from day after last end date to now
                        now = dt.now(timezone.utc)
                        days_since_last = (now - last_end_dt).days
                        
                        # Add buffer to ensure we capture all posts
                        calculated_lookback = max(days_since_last + 7, 30)  # At least 30 days
                        calculated_before_date = None  # Get most recent posts
                        
                        print(f"   Last data end: {last_end_date_str[:10]}")
                        print(f"   Days since last: {days_since_last}")
                        print(f"   Auto-calculated lookback: {calculated_lookback} days")
                        print(f"   Will fetch posts from ~{(now - timedelta(days=calculated_lookback)).date()} to now")
                    except Exception as e:
                        print(f"   ⚠️  Could not parse date, using defaults: {e}")
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting pipeline for r/{request.subreddit}")
        print(f"   Job ID: {job_id}")
        print(f"   Mode: {'UPDATE' if request.is_update else 'NEW'}")
        print(f"   Parameters: lookback={calculated_lookback}d, max_posts={request.max_posts}")
        print(f"{'='*60}\n")
        
        # Build command using calculated values
        cmd = [
            sys.executable,
            str(PIPELINE_SCRIPT),
            "--subreddit", request.subreddit,
            "--lookback-days", str(calculated_lookback),  # Use calculated value
            "--max-posts", str(request.max_posts),
            "--min-cluster", str(request.min_cluster)
        ]
        
        # Add before_date if specified (for incremental updates)
        if calculated_before_date:
            cmd.extend(["--before-date", calculated_before_date])
            print(f"   Before date: {calculated_before_date}")
        
        if request.slice_days > 0 and request.top_per_slice > 0:
            cmd.extend([
                "--slice-days", str(request.slice_days),
                "--top-per-slice", str(request.top_per_slice)
            ])
        
        print(f"📝 Command: {' '.join(cmd)}")
        print(f"📂 Working directory: {BACKEND_DIR.parent}")
        print(f"📂 Output directory: {PIPELINE_OUTPUT_DIR}\n")
        
        # Run pipeline
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR.parent)
        )
        
        print(f"\n{'='*60}")
        print(f"Pipeline process completed with return code: {result.returncode}")
        print(f"{'='*60}\n")
        
        if result.stdout:
            print("📄 STDOUT (last 500 chars):")
            print(result.stdout[-500:])
            print()
        
        if result.stderr:
            print("⚠️  STDERR (last 500 chars):")
            print(result.stderr[-500:])
            print()
        
        if result.returncode == 0:
            # Pipeline succeeded - wait a moment for files to be fully written
            print("✓ Pipeline execution successful, waiting for file sync...")
            time.sleep(2)
            
            # Find the output directory
            print(f"🔍 Looking for output directory for r/{request.subreddit}...")
            output_path = find_latest_output(request.subreddit)
            
            if output_path:
                print(f"✓ Found output directory: {output_path}")
                
                # Load the dashboard data
                print(f"📊 Loading dashboard_data.json...")
                data = load_dashboard_data(output_path)
                
                if data:
                    print(f"✓ Successfully loaded dashboard data")
                    print(f"   - Posts: {len(data.get('posts', []))}")
                    print(f"   - Insights: {len(data.get('insights', []))}")
                    print(f"   - Categories: {len(data.get('categories', []))}")
                    
                    # Store in subreddit_data
                    subreddit_data[request.subreddit] = {
                        "data": data,
                        "output_path": str(output_path),
                        "generated_at": datetime.now().isoformat()
                    }
                    jobs[job_id]["status"] = "completed"
                    jobs[job_id]["output_path"] = str(output_path)
                    jobs[job_id]["completed_at"] = datetime.now().isoformat()
                    
                    print(f"✅ Job {job_id} completed successfully!")
                    print(f"   Subreddit: r/{request.subreddit}")
                    print(f"   Available subreddits: {list(subreddit_data.keys())}\n")
                else:
                    error_msg = f"Failed to load dashboard_data.json from {output_path}"
                    print(f"❌ {error_msg}")
                    jobs[job_id]["status"] = "failed"
                    jobs[job_id]["error"] = error_msg
                    jobs[job_id]["completed_at"] = datetime.now().isoformat()
            else:
                error_msg = f"Output directory not found for r/{request.subreddit} in {PIPELINE_OUTPUT_DIR}"
                print(f"❌ {error_msg}")
                print(f"   Existing directories:")
                if PIPELINE_OUTPUT_DIR.exists():
                    for item in PIPELINE_OUTPUT_DIR.iterdir():
                        if item.is_dir():
                            print(f"     - {item.name}")
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = error_msg
                jobs[job_id]["completed_at"] = datetime.now().isoformat()
        else:
            # Pipeline failed
            error_msg = result.stderr[-1000:] if result.stderr else "Unknown error"
            print(f"❌ Pipeline failed with return code {result.returncode}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = error_msg
            jobs[job_id]["completed_at"] = datetime.now().isoformat()
    
    except Exception as e:
        print(f"❌ Exception during pipeline execution: {e}")
        import traceback
        traceback.print_exc()
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()

# === API Endpoints ===

@app.get("/")
def root():
    return {
        "message": "Reddit Insights Dashboard API",
        "version": "2.0",
        "endpoints": [
            "/subreddits",
            "/pipeline/run",
            "/pipeline/status/{job_id}",
            "/data/{subreddit}",
            "/health"
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/subreddits")
def list_subreddits():
    """List all available subreddits with data"""
    from datetime import datetime as dt
    
    subreddits_list = []
    for name, info in subreddit_data.items():
        # Get date range from metadata
        metadata = info["data"].get("metadata", {})
        date_range = {
            "start": None,
            "end": None,
            "end_timestamp": None  # For calculating next update
        }
        
        # Try to extract date range from posts
        posts = info["data"].get("posts", [])
        if posts:
            dates = [p.get("created_iso") for p in posts if p.get("created_iso")]
            if dates:
                dates.sort()
                date_range["start"] = dates[0][:10] if dates else None
                date_range["end"] = dates[-1][:10] if dates else None
                # Store end timestamp for calculating next update period
                if dates:
                    try:
                        end_dt = dt.fromisoformat(dates[-1])
                        date_range["end_timestamp"] = end_dt.timestamp()
                    except:
                        pass
        
        subreddits_list.append({
            "name": name,
            "generated_at": info["generated_at"],
            "output_path": info["output_path"],
            "num_posts": len(posts),
            "date_range": date_range
        })
    
    print(f"📋 /subreddits called - returning {len(subreddits_list)} subreddit(s): {[s['name'] for s in subreddits_list]}")
    return {"subreddits": subreddits_list}

@app.post("/pipeline/run")
def run_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    """Trigger pipeline execution for a subreddit"""
    
    # Validate inputs
    if not request.subreddit or len(request.subreddit.strip()) == 0:
        raise HTTPException(status_code=400, detail="Subreddit name is required")
    
    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id,
        "subreddit": request.subreddit,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "parameters": request.dict()
    }
    
    # Start pipeline in background
    thread = threading.Thread(target=run_pipeline_process, args=(job_id, request))
    thread.daemon = True
    thread.start()
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"Pipeline started for r/{request.subreddit}"
    }

@app.get("/pipeline/status/{job_id}")
def get_job_status(job_id: str):
    """Get status of a pipeline job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/pipeline/jobs")
def list_jobs():
    """List all pipeline jobs"""
    return {"jobs": list(jobs.values())}

@app.get("/data/{subreddit}/history")
def get_subreddit_history(subreddit: str):
    """Get all historical runs for a subreddit"""
    print(f"📜 /data/{subreddit}/history called")
    
    if not PIPELINE_OUTPUT_DIR.exists():
        return {"runs": []}
    
    # Find all directories for this subreddit
    matching_dirs = []
    for item in PIPELINE_OUTPUT_DIR.iterdir():
        if item.is_dir() and item.name.startswith(f"{subreddit}_"):
            matching_dirs.append(item)
    
    # Sort by modification time, newest first
    matching_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    runs = []
    for dir_path in matching_dirs:
        # Try to load metadata
        data = load_dashboard_data(dir_path)
        if data:
            posts = data.get("posts", [])
            dates = [p.get("created_iso") for p in posts if p.get("created_iso")]
            
            date_range = {"start": None, "end": None}
            if dates:
                dates.sort()
                date_range["start"] = dates[0][:10]
                date_range["end"] = dates[-1][:10]
            
            runs.append({
                "directory": dir_path.name,
                "generated_at": datetime.fromtimestamp(dir_path.stat().st_mtime).isoformat(),
                "num_posts": len(posts),
                "num_insights": len(data.get("insights", [])),
                "date_range": date_range,
                "is_current": dir_path.name == Path(subreddit_data.get(subreddit, {}).get("output_path", "")).name if subreddit in subreddit_data else False
            })
    
    print(f"✓ Found {len(runs)} run(s) for r/{subreddit}")
    return {"runs": runs}

@app.get("/data/{subreddit}")
def get_subreddit_data(subreddit: str):
    """Get full dashboard data for a subreddit"""
    print(f"📊 /data/{subreddit} called")
    if subreddit not in subreddit_data:
        print(f"❌ Subreddit '{subreddit}' not found. Available: {list(subreddit_data.keys())}")
        raise HTTPException(status_code=404, detail=f"No data found for r/{subreddit}")
    print(f"✓ Returning data for r/{subreddit}")
    return subreddit_data[subreddit]["data"]

@app.get("/data/{subreddit}/metadata")
def get_metadata(subreddit: str):
    """Get metadata for a subreddit"""
    if subreddit not in subreddit_data:
        raise HTTPException(status_code=404, detail=f"No data found for r/{subreddit}")
    return subreddit_data[subreddit]["data"].get("metadata", {})

@app.get("/data/{subreddit}/categories")
def get_categories(subreddit: str):
    """Get categories for a subreddit"""
    if subreddit not in subreddit_data:
        raise HTTPException(status_code=404, detail=f"No data found for r/{subreddit}")
    return subreddit_data[subreddit]["data"].get("categories", [])

@app.get("/data/{subreddit}/insights")
def get_insights(subreddit: str):
    """Get all insights for a subreddit"""
    if subreddit not in subreddit_data:
        raise HTTPException(status_code=404, detail=f"No data found for r/{subreddit}")
    return subreddit_data[subreddit]["data"].get("insights", [])

@app.get("/data/{subreddit}/insights/{insight_id}")
def get_insight(subreddit: str, insight_id: str):
    """Get specific insight for a subreddit"""
    if subreddit not in subreddit_data:
        raise HTTPException(status_code=404, detail=f"No data found for r/{subreddit}")
    
    insights = subreddit_data[subreddit]["data"].get("insights", [])
    for insight in insights:
        if insight.get("id") == insight_id:
            return insight
    
    raise HTTPException(status_code=404, detail=f"Insight '{insight_id}' not found")

# === Startup: Load existing data ===
@app.on_event("startup")
def load_existing_data():
    """Load any existing pipeline outputs on startup"""
    print(f"🔍 Looking for existing data in: {PIPELINE_OUTPUT_DIR}")
    
    if not PIPELINE_OUTPUT_DIR.exists():
        print(f"⚠️  Pipeline output directory doesn't exist: {PIPELINE_OUTPUT_DIR}")
        PIPELINE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created pipeline output directory")
        return
    
    # Find all subreddit output directories
    subreddit_dirs = {}
    for item in PIPELINE_OUTPUT_DIR.iterdir():
        if item.is_dir() and "_" in item.name:
            # Extract subreddit name
            # Format: {subreddit}_{YYYYMMDD}_{HHMMSS}
            # We need everything before the last 2 underscore parts (date and time)
            parts = item.name.split("_")
            if len(parts) >= 3:
                # Last 2 parts are timestamp (YYYYMMDD and HHMMSS)
                # Everything before that is the subreddit name
                subreddit = "_".join(parts[:-2])
                if subreddit not in subreddit_dirs:
                    subreddit_dirs[subreddit] = []
                subreddit_dirs[subreddit].append(item)
                print(f"  Found directory for r/{subreddit}: {item.name}")
    
    # Load latest data for each subreddit
    for subreddit, dirs in subreddit_dirs.items():
        # Sort by modification time, newest first
        dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_dir = dirs[0]
        
        print(f"  Loading latest data for r/{subreddit} from: {latest_dir.name}")
        
        # Try to load dashboard data
        data = load_dashboard_data(latest_dir)
        if data:
            subreddit_data[subreddit] = {
                "data": data,
                "output_path": str(latest_dir),
                "generated_at": datetime.fromtimestamp(latest_dir.stat().st_mtime).isoformat()
            }
            print(f"✓ Loaded existing data for r/{subreddit} from {latest_dir.name}")
        else:
            print(f"⚠️  Failed to load dashboard_data.json from {latest_dir.name}")
    
    print(f"✓ Startup complete. Loaded {len(subreddit_data)} subreddit(s): {list(subreddit_data.keys())}")
