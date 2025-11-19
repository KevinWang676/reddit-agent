
// import React, { useEffect, useMemo, useState } from "react";
// import { fetchInsight } from "../api";
// import MetricTile from "../components/MetricTile.jsx";
// import PostsTable from "../components/PostsTable.jsx";
// import {
//   SentimentOverTime,
//   EngagementOverTime,
//   SentimentDistribution,
// } from "../components/ChartPanel.jsx";

// export default function InsightDashboard({ id, onBack }) {
//   const [insight, setInsight] = useState(null);

//   // === Fetch insight data ===
//   useEffect(() => {
//     fetchInsight(id).then(setInsight).catch(console.error);
//   }, [id]);

//   // === Derived post time series ===
//   const timeSeries = useMemo(() => {
//     if (!insight?.linked_posts_full?.length) return [];

//     return [...insight.linked_posts_full]
//       .filter((p) => p.created_iso || p.created_utc)
//       .sort((a, b) => {
//         const da = new Date(a.created_iso || a.created_utc * 1000);
//         const db = new Date(b.created_iso || b.created_utc * 1000);
//         return da - db;
//       })
//       .map((p) => {
//         const date = new Date(p.created_iso || p.created_utc * 1000)
//           .toISOString()
//           .slice(0, 10);

//         let sentimentVal = 0;
//         if (typeof p.sentiment === "string") {
//           const s = p.sentiment.toLowerCase();
//           if (s.startsWith("pos")) sentimentVal = 1;
//           else if (s.startsWith("neg")) sentimentVal = -1;
//         } else if (typeof p.sentiment === "number") {
//           sentimentVal = Math.max(-1, Math.min(1, p.sentiment));
//         }

//         return {
//           date,
//           sentiment: sentimentVal,
//           engagement: (p.score || 0) + (p.num_comments || 0),
//         };
//       });
//   }, [insight]);

//   // === Sentiment distribution counts ===
//   const { pos, neu, neg } = useMemo(() => {
//     if (!insight?.linked_posts_full?.length)
//       return { pos: 0, neu: 0, neg: 0 };

//     let pos = 0,
//       neg = 0,
//       neu = 0;

//     for (const p of insight.linked_posts_full) {
//       const s = p.sentiment;
//       if (typeof s === "string") {
//         if (s.toLowerCase().startsWith("pos")) pos++;
//         else if (s.toLowerCase().startsWith("neg")) neg++;
//         else neu++;
//       } else if (typeof s === "number") {
//         if (s > 0.2) pos++;
//         else if (s < -0.2) neg++;
//         else neu++;
//       } else neu++;
//     }
//     return { pos, neu, neg };
//   }, [insight]);

//   // === Dominant Sentiment ===
//   const total = pos + neg + neu;
//   let dominantLabel = "Neutral";
//   let dominantColor = "text-gray-500";
//   let dominantPercent = 0;

//   if (total > 0) {
//     if (pos >= neg && pos >= neu) {
//       dominantLabel = "Positive";
//       dominantColor = "text-green-600";
//       dominantPercent = Math.round((pos / total) * 100);
//     } else if (neg >= pos && neg >= neu) {
//       dominantLabel = "Negative";
//       dominantColor = "text-red-600";
//       dominantPercent = Math.round((neg / total) * 100);
//     } else {
//       dominantLabel = "Neutral";
//       dominantColor = "text-gray-500";
//       dominantPercent = Math.round((neu / total) * 100);
//     }
//   }

//   // === Handle loading ===
//   if (!insight) {
//     return (
//       <div className="p-6 text-gray-700 text-center">Loading insight data...</div>
//     );
//   }

//   // === Format timespan ===
//   const formatDate = (d) => {
//     if (!d) return "";
//     try {
//       return new Date(d).toLocaleDateString();
//     } catch {
//       return d;
//     }
//   };
//   const startDate = formatDate(insight.time_range?.[0]);
//   const endDate = formatDate(insight.time_range?.[1]);

//   // === Avg sentiment color ===
//   let avgColor = "text-gray-800";
//   const avg = insight.avg_sentiment;
//   if (avg > 0.2) avgColor = "text-green-600";
//   else if (avg < -0.2) avgColor = "text-red-600";

//   // === Render ===
//   return (
//     <div className="space-y-6">
//       {/* Back button */}
//       <button
//         className="px-3 py-2 bg-white rounded-lg border border-gray-200 shadow-sm hover:bg-gray-50 transition"
//         onClick={onBack}
//       >
//         ← Back
//       </button>

//       {/* Header */}
//       <div>
//         <div className="text-sm text-gray-500">{insight.category}</div>
//         <h2 className="text-2xl font-semibold mt-1 text-[#0e6e66]">
//           {insight.theme || "Insight"}
//         </h2>
//         <p className="text-gray-500 text-sm mt-1">
//           Timespan: {startDate} → {endDate}
//         </p>
//         <p className="text-gray-700 mt-2 leading-relaxed max-w-3xl">
//           {insight.key_insight}
//         </p>
//       </div>

//       {/* Metrics Row */}
//       <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
//         <MetricTile label="Cluster Size" value={insight.cluster_size} />
//         <MetricTile
//           label="Avg Sentiment"
//           value={Number(insight.avg_sentiment).toFixed(2)}
//           color={avgColor}
//         />
//         <MetricTile label="Total Engagement" value={insight.total_engagement} />
//         <MetricTile
//           label="Dominant Sentiment"
//           value={`${dominantLabel} (${dominantPercent}%)`}
//           color={dominantColor}
//         />
//       </div>

//       {/* Charts */}
//       <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
//         <SentimentOverTime data={timeSeries} />
//         <EngagementOverTime data={timeSeries} />
//       </div>

//       {/* Distribution + Evidence */}
//       <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
//         <SentimentDistribution pos={pos} neu={neu} neg={neg} />
//         <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100">
//           <h4 className="font-semibold mb-2 text-[#0e6e66]">
//             Supporting Evidence
//           </h4>
//           {insight.supporting_evidence?.length > 0 ? (
//             <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
//               {insight.supporting_evidence.map((e, i) => (
//                 <li key={i}>{e}</li>
//               ))}
//             </ul>
//           ) : (
//             <p className="text-gray-400 text-sm">No supporting evidence.</p>
//           )}
//         </div>
//       </div>

//       {/* Posts Table */}
//       <PostsTable posts={insight.linked_posts_full || []} />
//     </div>
//   );
// }











// import React, { useEffect, useMemo, useState } from "react";
// import { fetchInsight } from "../api";
// import MetricTile from "../components/MetricTile.jsx";
// import PostsTable from "../components/PostsTable.jsx";
// import {
//   SentimentOverTime,
//   EngagementOverTime,
//   SentimentDistribution,
// } from "../components/ChartPanel.jsx";

// export default function InsightDashboard({ id, onBack }) {
//   const [insight, setInsight] = useState(null);

//   useEffect(() => {
//     fetchInsight(id).then(setInsight);
//   }, [id]);

//   const timeSeries = useMemo(() => {
//   if (!insight) return [];
//   const posts = insight.linked_posts_full || [];

//   // Sort posts chronologically
//   const sorted = [...posts].sort((a, b) => {
//     const da = new Date(a.created_iso || a.created_utc * 1000 || 0);
//     const db = new Date(b.created_iso || b.created_utc * 1000 || 0);
//     return da - db;
//   });

//   // Group by date
//   const grouped = {};
//   sorted.forEach((p) => {
//     const date = new Date(p.created_iso || p.created_utc * 1000 || 0)
//       .toISOString()
//       .slice(0, 10);

//     if (!grouped[date]) grouped[date] = { sentiments: [], engagements: [] };

//     let sentimentVal = 0;
//     if (typeof p.sentiment === "string") {
//       if (p.sentiment.toLowerCase().startsWith("pos")) sentimentVal = 1;
//       else if (p.sentiment.toLowerCase().startsWith("neg")) sentimentVal = -1;
//     } else if (typeof p.sentiment === "number") {
//       sentimentVal = Math.max(-1, Math.min(1, p.sentiment));
//     }

//     grouped[date].sentiments.push(sentimentVal);
//     grouped[date].engagements.push((p.score || 0) + (p.num_comments || 0));
//   });

//   // Aggregate per day: average sentiment, total engagement
//   const aggregated = Object.entries(grouped).map(([date, vals]) => ({
//     date,
//     sentiment:
//       vals.sentiments.reduce((a, b) => a + b, 0) / vals.sentiments.length,
//     engagement: vals.engagements.reduce((a, b) => a + b, 0),
//   }));

//   return aggregated;
// }, [insight]);


//   const pos =
//     insight?.linked_posts_full?.filter((p) =>
//       p.sentiment?.toLowerCase().startsWith("pos")
//     ).length || 0;
//   const neg =
//     insight?.linked_posts_full?.filter((p) =>
//       p.sentiment?.toLowerCase().startsWith("neg")
//     ).length || 0;
//   const total = insight?.linked_posts_full?.length || 0;
//   const neu = total - pos - neg;

//   const dominantSentiment =
//     pos > neg && pos > neu
//       ? { label: "Positive", pct: ((pos / total) * 100).toFixed(0) }
//       : neg > pos && neg > neu
//       ? { label: "Negative", pct: ((neg / total) * 100).toFixed(0) }
//       : { label: "Neutral", pct: ((neu / total) * 100).toFixed(0) };

//   if (!insight) {
//     return (
//       <div className="p-6 text-gray-700 text-center">
//         Loading insight data...
//       </div>
//     );
//   }

//   const formatDate = (d) => {
//     if (!d) return "";
//     try {
//       return new Date(d).toLocaleDateString();
//     } catch {
//       return d;
//     }
//   };

//   const startDate = formatDate((insight.time_range || [])[0]);
//   const endDate = formatDate((insight.time_range || [])[1]);

//   const avg = Number(insight.avg_sentiment);
//   let avgColor = "text-gray-800";
//   if (avg > 0.2) avgColor = "text-green-600";
//   else if (avg < -0.2) avgColor = "text-red-600";

//   const domColor =
//     dominantSentiment.label === "Positive"
//       ? "text-green-600"
//       : dominantSentiment.label === "Negative"
//       ? "text-red-600"
//       : "text-gray-500";

//   return (
//     <div className="space-y-6">
//       <button
//         className="px-3 py-2 bg-white rounded-lg border border-gray-200 shadow-sm hover:bg-gray-50 transition"
//         onClick={onBack}
//       >
//         ← Back
//       </button>

//       <div className="flex flex-col lg:flex-row justify-between gap-8">
//         {/* Left Section */}
//         <div className="flex-1">
//           <div className="text-sm text-gray-500">{insight.category}</div>
//           <h2 className="text-2xl font-semibold mt-1 text-green-800">
//             {insight.theme || "Insight"}
//           </h2>
//           <div className="text-sm text-gray-500 mt-1">
//             Timespan: {startDate} → {endDate}
//           </div>
//           <p className="text-gray-700 mt-3 leading-relaxed">
//             {insight.key_insight}
//           </p>
//         </div>

//         {/* Right Section (Metrics Grid 2x2) */}
//         <div className="grid grid-cols-2 gap-4 w-full lg:w-1/3">
//           <MetricTile label="Total Engagement" value={insight.total_engagement} />
//           <MetricTile label="Number of Posts" value={insight.cluster_size} />
//           <MetricTile
//             label="Avg Sentiment"
//             value={<span className={avgColor}>{avg.toFixed(2)}</span>}
//           />
//           <MetricTile
//             label="Dominant Sentiment"
//             value={
//               <span className={domColor}>
//                 {dominantSentiment.label} ({dominantSentiment.pct}%)
//               </span>
//             }
//           />
//         </div>
//       </div>

//       {/* Charts - Reordered Layout */}
//       <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
//         {/* Top row */}
//         <EngagementOverTime data={timeSeries} />
//         <SentimentDistribution pos={pos} neu={neu} neg={neg} />

//         {/* Bottom row */}
//         <SentimentOverTime data={timeSeries} />
//         <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100">
//           <h4 className="font-semibold mb-2">Supporting Evidence</h4>
//           <ul className="list-disc pl-5 text-sm text-gray-800">
//             {(insight.supporting_evidence || []).map((e, i) => (
//               <li key={i}>{e}</li>
//             ))}
//           </ul>
//         </div>
//       </div>

//       <PostsTable posts={insight.linked_posts_full} />
//     </div>
//   );
// }
















// import React, { useEffect, useState } from "react";
// import { fetchInsights, fetchCategories } from "../api";
// import InsightCard from "../components/InsightCard.jsx";
// import { Plus, Minus } from "lucide-react";

// export default function InsightDashboard({ onSelect }) {
//   const [insights, setInsights] = useState([]);
//   const [categories, setCategories] = useState([]);
//   const [expanded, setExpanded] = useState({});
//   const [visibleCount, setVisibleCount] = useState({});

//   useEffect(() => {
//     fetchInsights().then(setInsights);
//     fetchCategories().then(setCategories);
//   }, []);

//   // Group insights by category
//   const grouped = categories.map((cat) => ({
//     ...cat,
//     insights: insights.filter((i) => i.category === cat.name),
//   }));

//   const toggleExpand = (catName) => {
//     setExpanded((prev) => ({ ...prev, [catName]: !prev[catName] }));
//     setVisibleCount((prev) => ({
//       ...prev,
//       [catName]: prev[catName] || 5,
//     }));
//   };

//   const toggleSeeMore = (catName, total) => {
//     setVisibleCount((prev) => ({
//       ...prev,
//       [catName]: prev[catName] >= total ? 5 : total,
//     }));
//   };

//   return (
//     <div className="space-y-6">
//       {grouped.map((cat) => (
//         <div
//           key={cat.name}
//           className="bg-white rounded-xl shadow-card border border-gray-100 overflow-hidden"
//         >
//           {/* Category header */}
//           <div
//             className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
//             onClick={() => toggleExpand(cat.name)}
//           >
//             <div>
//               <h2 className="text-lg font-semibold text-gray-800">
//                 {cat.name}
//               </h2>
//               <p className="text-sm text-gray-500">
//                 {cat.num_clusters || cat.insights.length} insights •{" "}
//                 {cat.num_posts || 0} posts
//               </p>
//             </div>
//             <button className="text-gray-600 hover:text-black">
//               {expanded[cat.name] ? <Minus size={20} /> : <Plus size={20} />}
//             </button>
//           </div>

//           {/* Insights list */}
//           {expanded[cat.name] && (
//             <div className="border-t border-gray-100 divide-y divide-gray-100">
//               {cat.insights
//                 .slice(0, visibleCount[cat.name] || 5)
//                 .map((insight) => (
//                   <InsightCard
//                     key={insight.id}
//                     insight={insight}
//                     onClick={() => onSelect(insight.id)}
//                   />
//                 ))}

//               {cat.insights.length > 5 && (
//                 <div className="text-center py-3">
//                   <button
//                     className="text-sm text-blue-600 hover:underline"
//                     onClick={(e) => {
//                       e.stopPropagation();
//                       toggleSeeMore(cat.name, cat.insights.length);
//                     }}
//                   >
//                     {visibleCount[cat.name] >= cat.insights.length
//                       ? "See less"
//                       : "See more"}
//                   </button>
//                 </div>
//               )}
//             </div>
//           )}
//         </div>
//       ))}
//     </div>
//   );
// }

import React, { useEffect, useMemo, useState } from "react";
import { fetchInsight } from "../api";
import MetricTile from "../components/MetricTile.jsx";
import PostsTable from "../components/PostsTable.jsx";
import {
  SentimentOverTime,
  EngagementOverTime,
  SentimentDistribution,
} from "../components/ChartPanel.jsx";

export default function InsightDashboard({ subreddit, id, onBack }) {
  const [insight, setInsight] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // === Fetch insight data ===
  useEffect(() => {
    if (!subreddit || !id) return;
    
    setLoading(true);
    setError(null);
    
    fetchInsight(subreddit, id)
      .then((data) => {
        setInsight(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load insight:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [subreddit, id]);

  // === Build daily aggregated time series ===
  const timeSeries = useMemo(() => {
    if (!insight?.linked_posts_full) return [];

    const dateMap = {};

    insight.linked_posts_full.forEach((p) => {
      const d = new Date(p.created_iso || p.created_utc * 1000 || 0)
        .toISOString()
        .slice(0, 10);

      // normalize sentiment to -1 / 0 / 1
      let s = 0;
      if (typeof p.sentiment === "string") {
        const low = p.sentiment.toLowerCase();
        if (low.startsWith("pos")) s = 1;
        else if (low.startsWith("neg")) s = -1;
      } else if (typeof p.sentiment === "number") {
        s = Math.max(-1, Math.min(1, p.sentiment));
      }

      const engagement = (p.score || 0) + (p.num_comments || 0);

      if (!dateMap[d]) {
        dateMap[d] = { count: 0, sentimentTotal: 0, engagementTotal: 0 };
      }
      dateMap[d].count += 1;
      dateMap[d].sentimentTotal += s;
      dateMap[d].engagementTotal += engagement;
    });

    return Object.entries(dateMap)
      .map(([date, v]) => ({
        date,
        sentiment: v.sentimentTotal / v.count,
        engagement: v.engagementTotal / v.count,
      }))
      .sort((a, b) => (a.date < b.date ? -1 : 1));
  }, [insight]);

  // === Sentiment breakdown ===
  const pos =
    insight?.linked_posts_full?.filter((p) =>
      p.sentiment?.toLowerCase().startsWith("pos")
    ).length || 0;

  const neg =
    insight?.linked_posts_full?.filter((p) =>
      p.sentiment?.toLowerCase().startsWith("neg")
    ).length || 0;

  const neu =
    (insight?.linked_posts_full?.length || 0) - pos - neg;

  // === Avg sentiment + dominant sentiment color logic ===
  const avg = Number(insight?.avg_sentiment || 0);

  let avgColor = "text-gray-800";
  if (avg > 0.2) avgColor = "text-green-600";
  else if (avg < -0.2) avgColor = "text-red-600";

  const totalCount = pos + neg + neu;

  let dominantLabel = "Neutral";
  let dominantPct = totalCount ? Math.round((neu / totalCount) * 100) : 0;
  let domColor = "text-gray-500";

  if (totalCount > 0) {
    if (pos >= neg && pos >= neu) {
      dominantLabel = "Positive";
      dominantPct = Math.round((pos / totalCount) * 100);
      domColor = "text-green-600";
    } else if (neg >= pos && neg >= neu) {
      dominantLabel = "Negative";
      dominantPct = Math.round((neg / totalCount) * 100);
      domColor = "text-red-600";
    }
  }

  // === Loading state ===
  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading insight details...</p>
      </div>
    );
  }

  // === Error state ===
  if (error) {
    return (
      <div className="text-center py-20">
        <div className="text-red-600 text-xl mb-4">⚠️</div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Failed to load insight</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            ← Back
          </button>
        )}
      </div>
    );
  }

  // === No insight loaded ===
  if (!insight) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-600">No insight data available</p>
      </div>
    );
  }

  // === Timespan formatting ===
  const formatDate = (d) => {
    if (!d) return "";
    try {
      return new Date(d).toLocaleDateString();
    } catch {
      return d;
    }
  };
  const startDate = formatDate((insight.time_range || [])[0]);
  const endDate = formatDate((insight.time_range || [])[1]);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Back button */}
      <button
        className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg border border-gray-300 shadow-sm hover:bg-gray-50 hover:border-gray-400 transition-all font-medium text-gray-700"
        onClick={onBack}
      >
        <span>←</span> Back to Overview
      </button>

      {/* Header Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2 text-sm font-medium text-blue-700 mb-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            {insight.category}
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">{insight.theme}</h1>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-1.5">
              <span className="font-medium">📅</span>
              <span>{startDate} → {endDate}</span>
            </div>
          </div>
        </div>

        <div className="p-6">
          <p className="text-gray-700 leading-relaxed text-base">
            {insight.key_insight}
          </p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricTile label="Total Posts" value={insight.cluster_size} />
        <MetricTile label="Total Engagement" value={insight.total_engagement} />
        <MetricTile
          label="Avg Sentiment"
          value={avg.toFixed(2)}
          color={avgColor}
        />
        <MetricTile
          label="Dominant Sentiment"
          value={`${dominantLabel} (${dominantPct}%)`}
          color={domColor}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <EngagementOverTime data={timeSeries} />
        </div>

        {/* Chart 2 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <SentimentDistribution pos={pos} neg={neg} neu={neu} />
        </div>

        {/* Chart 3 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <SentimentOverTime data={timeSeries} />
        </div>

        {/* Supporting Evidence (4th tile) */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h4 className="font-semibold mb-4 text-gray-900 flex items-center gap-2">
            <span>📌</span> Supporting Evidence
          </h4>
          <ul className="text-sm text-gray-700 space-y-2">
            {(insight.supporting_evidence || []).map((e, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-blue-500 mt-1">•</span>
                <span className="flex-1">{e}</span>
              </li>
            ))}
          </ul>
        </div>

      </div>

      {/* Posts Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h4 className="font-semibold text-gray-900 flex items-center gap-2">
            <span>📄</span> Linked Posts ({(insight.linked_posts_full || []).length})
          </h4>
          <p className="text-xs text-gray-500 mt-1">All posts analyzed in this cluster</p>
        </div>
        <div className="p-6">
          <PostsTable posts={insight.linked_posts_full} />
        </div>
      </div>
    </div>
  );
}
