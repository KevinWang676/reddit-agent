import React, { useEffect, useState } from "react";
import Home from "./pages/Home.jsx";
import InsightDashboard from "./pages/InsightDashboard.jsx";
import PipelineForm from "./components/PipelineForm.jsx";
import JobStatusPanel from "./components/JobStatusPanel.jsx";
import { listSubreddits, runPipeline } from "./api";
import { Plus, RefreshCw } from "lucide-react";

// Use real Deloitte logo
import deloitteLogo from "./assets/deloitte_logo.png";

export default function App() {
  const [route, setRoute] = useState({ page: "home", id: null });
  const [subreddits, setSubreddits] = useState([]);
  const [activeSubreddit, setActiveSubreddit] = useState(null);
  const [showPipelineForm, setShowPipelineForm] = useState(false);
  const [pipelineMode, setPipelineMode] = useState({ type: "new", config: null }); // "new" or "update"
  const [currentJob, setCurrentJob] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  // Load available subreddits on mount
  useEffect(() => {
    loadSubreddits();
  }, []);

  // Auto-reload subreddits periodically (every 10 seconds) to catch new completions
  useEffect(() => {
    const interval = setInterval(() => {
      loadSubreddits();
    }, 10000); // 10 seconds

    return () => clearInterval(interval);
  }, []);

  // Set first subreddit as active by default
  useEffect(() => {
    if (subreddits.length > 0 && !activeSubreddit) {
      setActiveSubreddit(subreddits[0].name);
    }
  }, [subreddits, activeSubreddit]);

  const loadSubreddits = async () => {
    try {
      const response = await listSubreddits();
      setSubreddits(response.subreddits || []);
    } catch (error) {
      console.error("Failed to load subreddits:", error);
    }
  };

  const handleRunPipeline = async (config) => {
    setIsRunning(true);
    try {
      const response = await runPipeline(config);
      setCurrentJob(response.job_id);
      setShowPipelineForm(false);
    } catch (error) {
      console.error("Failed to run pipeline:", error);
      alert(`Failed to start pipeline: ${error.message}`);
      setIsRunning(false);
    }
  };

  const handleJobComplete = (job) => {
    setIsRunning(false);
    setCurrentJob(null);
    // Reload subreddits to include the new one
    loadSubreddits();
    // Switch to the newly created subreddit
    setActiveSubreddit(job.subreddit);
    // Reset route to home
    setRoute({ page: "home", id: null });
  };

  const handleJobError = (job) => {
    setIsRunning(false);
    alert(`Pipeline failed for r/${job.subreddit}. Check the status panel for details.`);
  };

  const handleNewPipeline = () => {
    setPipelineMode({ type: "new", config: null });
    setShowPipelineForm(true);
  };

  const handleUpdatePipeline = () => {
    // Get the current subreddit's info
    const currentSubreddit = subreddits.find(s => s.name === activeSubreddit);
    if (!currentSubreddit) return;

    // Pre-fill config for update (simpler - only max_posts needed)
    const updateConfig = {
      subreddit: activeSubreddit,
      max_posts: 700,
      min_cluster: 3,
      is_update: true, // Flag for backend to auto-calculate dates
      // These will be auto-calculated by backend:
      lookback_days: 365, // Placeholder (will be overridden)
      slice_days: 0,
      top_per_slice: 0,
      before_date: "", // Will be auto-calculated
    };

    setPipelineMode({ type: "update", config: updateConfig });
    setShowPipelineForm(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* HEADER */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* LEFT: Brand */}
            <div className="flex items-center gap-4">
              <img
                src={deloitteLogo}
                alt="Deloitte"
                className="h-7 cursor-pointer hover:opacity-80 transition"
                onClick={() => setRoute({ page: "home" })}
              />
              <div className="h-8 w-px bg-gray-300" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  ConvergeCONSUMER
                </h1>
                <p className="text-xs text-gray-500">Reddit Insights Platform</p>
              </div>
            </div>

        {/* RIGHT SIDE: Actions */}
        <div className="flex items-center gap-2">
          {/* Update button (only show if a subreddit is selected) */}
          {activeSubreddit && (
            <button
              onClick={handleUpdatePipeline}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-all shadow-sm hover:shadow text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isRunning}
              title={`Update r/${activeSubreddit} with new posts`}
            >
              <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
              Update
            </button>
          )}
          
          <button
            onClick={handleNewPipeline}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isRunning}
          >
            <Plus className="w-4 h-4" />
            New Pipeline
          </button>
        </div>
          </div>
        </div>
      </header>

      {/* SUBREDDIT TABS */}
      {subreddits.length > 0 && (
        <div className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide">
              {subreddits.map((sub) => (
                <button
                  key={sub.name}
                  onClick={() => {
                    setActiveSubreddit(sub.name);
                    setRoute({ page: "home", id: null });
                  }}
                  className={`px-5 py-3 text-sm font-medium border-b-3 transition-all whitespace-nowrap relative group ${
                    activeSubreddit === sub.name
                      ? "border-blue-600 text-blue-700 bg-blue-50"
                      : "border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                  title={sub.date_range ? `Data from ${sub.date_range.start} to ${sub.date_range.end}` : ""}
                >
                  <div className="flex flex-col items-start gap-0.5">
                    <span className="font-semibold">r/{sub.name}</span>
                    {sub.date_range && sub.date_range.start && (
                      <span className="text-xs text-gray-500">
                        {sub.date_range.start} to {sub.date_range.end}
                      </span>
                    )}
                  </div>
                  {activeSubreddit === sub.name && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"></div>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* JOB STATUS PANEL */}
      {currentJob && (
        <div className="max-w-7xl mx-auto px-6 pt-4">
          <JobStatusPanel
            jobId={currentJob}
            onComplete={handleJobComplete}
            onError={handleJobError}
          />
        </div>
      )}

      {/* MAIN CONTENT */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {!activeSubreddit && subreddits.length === 0 ? (
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="text-center max-w-md">
              <div className="mb-6">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center mx-auto shadow-lg">
                  <Plus className="w-10 h-10 text-white" />
                </div>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-3">
                Welcome to ConvergeCONSUMER
              </h2>
              <p className="text-gray-600 mb-8 leading-relaxed">
                Get started by analyzing Reddit discussions from any subreddit. 
                Generate AI-powered insights and track conversation trends.
              </p>
              <button
                onClick={() => setShowPipelineForm(true)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg hover:shadow-xl font-medium"
              >
                <Plus className="w-5 h-5" />
                Run Your First Pipeline
              </button>
            </div>
          </div>
        ) : activeSubreddit ? (
          <>
            {route.page === "home" && (
              <Home
                subreddit={activeSubreddit}
                onSelect={(id) => setRoute({ page: "insightDetail", id })}
              />
            )}

            {route.page === "insightDetail" && (
              <InsightDashboard
                subreddit={activeSubreddit}
                id={route.id}
                onBack={() => setRoute({ page: "home" })}
              />
            )}
          </>
        ) : null}
      </main>

      {/* PIPELINE FORM MODAL */}
      {showPipelineForm && (
        <PipelineForm
          onSubmit={handleRunPipeline}
          onClose={() => !isRunning && setShowPipelineForm(false)}
          isRunning={isRunning}
          updateMode={pipelineMode.type === "update"}
          initialConfig={pipelineMode.config}
        />
      )}
    </div>
  );
}
