import React, { useState, useEffect } from "react";
import { Play, X, Loader2, RefreshCw } from "lucide-react";

export default function PipelineForm({ onSubmit, onClose, isRunning = false, updateMode = false, initialConfig = null }) {
  const defaultConfig = {
    subreddit: "MakeupAddiction",
    lookback_days: 365,
    max_posts: 700,
    min_cluster: 3,
    slice_days: 0,
    top_per_slice: 0,
    before_date: "",
  };

  const [config, setConfig] = useState(initialConfig || defaultConfig);

  useEffect(() => {
    if (initialConfig) {
      setConfig(initialConfig);
    }
  }, [initialConfig]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(config);
  };

  const handleChange = (field, value) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {updateMode ? (
                <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                  <RefreshCw className="w-5 h-5 text-emerald-600" />
                </div>
              ) : (
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Play className="w-5 h-5 text-blue-600" />
                </div>
              )}
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  {updateMode ? "Update Dashboard" : "New Reddit Pipeline"}
                </h2>
                <p className="text-xs text-gray-500">
                  {updateMode ? "Fetch latest posts and insights" : "Analyze a subreddit"}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg p-1.5 transition-colors"
              disabled={isRunning}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-5">
          {updateMode && (
            <div className="mb-5 p-4 bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-xl">
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  <div className="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs font-bold">✨</span>
                  </div>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-emerald-900 mb-1">
                    Smart Update Mode Active
                  </p>
                  <p className="text-xs text-emerald-700">
                    Automatically fetches posts since your last run for <strong>r/{config.subreddit}</strong>. 
                    Just set max posts - we'll calculate the optimal date range!
                  </p>
                </div>
              </div>
            </div>
          )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Subreddit */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Subreddit Name {!updateMode && <span className="text-red-500">*</span>}
            </label>
            <input
              type="text"
              value={config.subreddit}
              onChange={(e) => handleChange("subreddit", e.target.value)}
              className="w-full border-2 border-gray-300 rounded-lg px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500 transition-all"
              placeholder="e.g., MakeupAddiction"
              required
              disabled={isRunning || updateMode}
            />
            <p className="text-xs text-gray-500 mt-1.5">
              {updateMode ? "🔒 Subreddit is locked in update mode" : "Enter the subreddit name without \"r/\""}
            </p>
          </div>

          {/* Lookback Days - Only show in NEW mode */}
          {!updateMode && (
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Lookback Days
              </label>
              <input
                type="number"
                value={config.lookback_days}
                onChange={(e) =>
                  handleChange("lookback_days", parseInt(e.target.value))
                }
                className="w-full border-2 border-gray-300 rounded-lg px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                min="1"
                max="730"
                disabled={isRunning}
              />
              <p className="text-xs text-gray-500 mt-1.5">
                How many days back to analyze (1-730)
              </p>
            </div>
          )}

          {/* Auto-calculated info for UPDATE mode */}
          {updateMode && (
            <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
              <div className="flex items-center gap-2 text-blue-900 mb-2">
                <span className="font-semibold">📅 Date Range</span>
              </div>
              <div className="text-xs text-blue-700 space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                  <span>Automatically calculated from your last run</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                  <span>Fetches only new posts since last update</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                  <span>Includes 7-day buffer for safety</span>
                </div>
              </div>
            </div>
          )}

          {/* Max Posts */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Maximum Posts <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={config.max_posts}
              onChange={(e) =>
                handleChange("max_posts", parseInt(e.target.value))
              }
              className="w-full border-2 border-gray-300 rounded-lg px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              min="10"
              max="5000"
              disabled={isRunning}
            />
            <p className="text-xs text-gray-500 mt-1.5">
              Maximum number of posts to analyze (10-5000)
            </p>
          </div>

          {/* Min Cluster Size */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Minimum Cluster Size
            </label>
            <input
              type="number"
              value={config.min_cluster}
              onChange={(e) =>
                handleChange("min_cluster", parseInt(e.target.value))
              }
              className="w-full border-2 border-gray-300 rounded-lg px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              min="2"
              max="50"
              disabled={isRunning}
            />
            <p className="text-xs text-gray-500 mt-1.5">
              Minimum posts required per cluster (2-50)
            </p>
          </div>

          {/* Advanced Options Toggle */}
          {!updateMode && (
            <details className="text-sm border border-gray-200 rounded-lg p-4 bg-gray-50">
              <summary className="cursor-pointer text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-2">
                <span>⚙️</span> Advanced Options (Time Slicing)
              </summary>
              <div className="mt-4 space-y-4 pt-4 border-t border-gray-200">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Slice Days
                  </label>
                  <input
                    type="number"
                    value={config.slice_days}
                    onChange={(e) =>
                      handleChange("slice_days", parseInt(e.target.value))
                    }
                    className="w-full border-2 border-gray-300 rounded-lg px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    min="0"
                    disabled={isRunning}
                  />
                  <p className="text-xs text-gray-500 mt-1.5">
                    Time slice size in days (0 = disabled)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Top Posts Per Slice
                  </label>
                  <input
                    type="number"
                    value={config.top_per_slice}
                    onChange={(e) =>
                      handleChange("top_per_slice", parseInt(e.target.value))
                    }
                    className="w-full border-2 border-gray-300 rounded-lg px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    min="0"
                    disabled={isRunning}
                  />
                  <p className="text-xs text-gray-500 mt-1.5">
                    Top posts per slice by score (0 = disabled)
                  </p>
                </div>
              </div>
            </details>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-5 py-2.5 border-2 border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 hover:border-gray-400 transition-all"
              disabled={isRunning}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={`flex-1 px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed ${
                updateMode 
                  ? "bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700 text-white"
                  : "bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white"
              }`}
              disabled={isRunning}
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {updateMode ? "Updating..." : "Running..."}
                </>
              ) : (
                <>
                  {updateMode ? <RefreshCw className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  {updateMode ? "Update Dashboard" : "Run Pipeline"}
                </>
              )}
            </button>
          </div>
        </form>

        {/* Info Message */}
        <div className="mt-5 p-4 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
          <div className="flex items-start gap-2">
            <span className="text-base">ℹ️</span>
            <div>
              <p className="font-medium text-gray-900 mb-1">Pipeline Execution</p>
              <p className="text-gray-600 mb-2">
                Processing typically takes 5-15 minutes depending on the number of posts and API rate limits. 
                You can monitor progress in the status panel.
              </p>
              {updateMode && (
                <div className="mt-3 pt-3 border-t border-gray-300">
                  <p className="font-medium text-gray-900 mb-1">🔄 Update Behavior</p>
                  <p className="text-gray-600">
                    New posts will be analyzed independently and form their own clusters. 
                    The system generates fresh insights based on the latest discussions, 
                    allowing you to track how conversations evolve over time.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>
  );
}

