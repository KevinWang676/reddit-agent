
// export default function InsightCard({ insight, onClick }) {
//   return (
//     <div className="card" onClick={onClick}>
//       <div className="flex items-start justify-between">
//         <div>
//           <div className="text-sm text-gray-500">{insight.category}</div>
//           <h3 className="font-semibold mt-1">{insight.theme || "Untitled Theme"}</h3>
//         </div>
//         <span className="badge">ID: {insight.id}</span>
//       </div>
//       <div className="mt-3 text-sm text-gray-700 line-clamp-3">{insight.key_insight}</div>
//       <div className="mt-4 flex justify-between text-sm">
//         <span>🧩 {insight.cluster_size} posts</span>
//         <span>📈 {insight.total_engagement} engagement</span>
//       </div>
//     </div>
//   );
// }


import React from "react";
import { Users, TrendingUp, MessageCircle } from "lucide-react";

export default function InsightCard({ insight, onClick }) {
  // Calculate sentiment color
  const getSentimentColor = (sentiment) => {
    if (sentiment > 0.2) return "text-emerald-600 bg-emerald-50";
    if (sentiment < -0.2) return "text-red-600 bg-red-50";
    return "text-gray-600 bg-gray-50";
  };

  const sentimentLabel = (sentiment) => {
    if (sentiment > 0.2) return "Positive";
    if (sentiment < -0.2) return "Negative";
    return "Neutral";
  };

  return (
    <div
      className="group bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md hover:border-blue-300 cursor-pointer transition-all duration-200"
      onClick={() => onClick && onClick(insight.id)}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 mb-1.5 line-clamp-2 group-hover:text-blue-700 transition-colors">
            {insight.theme || "Untitled Insight"}
          </h3>
          <p className="text-xs text-gray-500 mb-3">
            {insight.id}
          </p>
          
          {/* Metrics Row */}
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5 text-gray-600">
              <Users className="w-4 h-4" />
              <span className="font-medium text-gray-900">{insight.cluster_size}</span>
              <span className="text-gray-500">posts</span>
            </div>
            
            <div className="flex items-center gap-1.5 text-gray-600">
              <TrendingUp className="w-4 h-4" />
              <span className="font-medium text-gray-900">{insight.total_engagement}</span>
              <span className="text-gray-500">engagement</span>
            </div>
          </div>
        </div>

        {/* Sentiment Badge */}
        {insight.avg_sentiment !== undefined && (
          <div className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getSentimentColor(insight.avg_sentiment)}`}>
            {sentimentLabel(insight.avg_sentiment)}
          </div>
        )}
      </div>
    </div>
  );
}
