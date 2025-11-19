import React, { useEffect, useState } from "react";
import { CheckCircle, XCircle, Loader2, Clock, RefreshCw } from "lucide-react";
import { getJobStatus } from "../api";

export default function JobStatusPanel({ jobId, onComplete, onError }) {
  const [job, setJob] = useState(null);
  const [polling, setPolling] = useState(true);

  useEffect(() => {
    if (!jobId || !polling) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId);
        setJob(status);

        if (status.status === "completed") {
          setPolling(false);
          if (onComplete) onComplete(status);
        } else if (status.status === "failed") {
          setPolling(false);
          if (onError) onError(status);
        }
      } catch (error) {
        console.error("Failed to poll job status:", error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [jobId, polling, onComplete, onError]);

  if (!job) return null;

  const getStatusIcon = () => {
    switch (job.status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-600" />;
      case "running":
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case "queued":
        return <Clock className="w-5 h-5 text-yellow-600" />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (job.status) {
      case "completed":
        return "bg-green-50 border-green-200";
      case "failed":
        return "bg-red-50 border-red-200";
      case "running":
        return "bg-blue-50 border-blue-200";
      case "queued":
        return "bg-yellow-50 border-yellow-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  return (
    <div className={`border-2 rounded-xl p-5 shadow-md ${getStatusColor()}`}>
      <div className="flex items-start gap-4">
        {getStatusIcon()}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-900 text-lg">
              r/{job.subreddit}
            </h3>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${
              job.status === "completed" ? "bg-green-100 text-green-700" :
              job.status === "failed" ? "bg-red-100 text-red-700" :
              job.status === "running" ? "bg-blue-100 text-blue-700" :
              "bg-yellow-100 text-yellow-700"
            }`}>
              {job.status}
            </span>
          </div>

          {job.status === "running" && (
            <div className="space-y-2">
              <p className="text-sm text-gray-700 font-medium">
                Processing posts and generating insights...
              </p>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div className="bg-blue-600 h-1.5 rounded-full animate-pulse" style={{width: '60%'}}></div>
              </div>
            </div>
          )}

          {job.status === "completed" && (
            <div className="flex items-center gap-2">
              <p className="text-sm text-green-700 font-medium">
                Pipeline completed successfully!
              </p>
            </div>
          )}

          {job.status === "failed" && (
            <div className="mt-2">
              <p className="text-sm text-red-700 font-medium mb-2">Pipeline execution failed</p>
              {job.error && (
                <details className="mt-2">
                  <summary className="text-xs text-red-600 cursor-pointer hover:underline font-medium">
                    View error details
                  </summary>
                  <pre className="text-xs bg-red-100 p-3 rounded-lg mt-2 overflow-auto max-h-40 border border-red-200">
                    {job.error}
                  </pre>
                </details>
              )}
            </div>
          )}

          {job.created_at && (
            <div className="mt-3 pt-3 border-t border-gray-200 flex items-center gap-4 text-xs text-gray-600">
              <div>
                <span className="font-medium">Started:</span> {new Date(job.created_at).toLocaleString()}
              </div>
              {job.completed_at && (
                <div>
                  <span className="font-medium">Completed:</span> {new Date(job.completed_at).toLocaleString()}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

