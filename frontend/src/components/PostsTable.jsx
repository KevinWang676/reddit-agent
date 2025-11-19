

// import React from "react";

// export default function PostsTable({ posts }) {
//   if (!posts || posts.length === 0) {
//     return (
//       <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100 text-center text-gray-400">
//         No post data available.
//       </div>
//     );
//   }

//   return (
//     <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100 overflow-x-auto">
//       <h4 className="font-semibold mb-2 text-[#0e6e66]">Linked Posts</h4>
//       <table className="min-w-full text-sm text-left border-t border-gray-100">
//         <thead>
//           <tr className="bg-gray-50">
//             <th className="p-2 font-medium text-gray-600">Date</th>
//             <th className="p-2 font-medium text-gray-600">Title</th>
//             <th className="p-2 font-medium text-gray-600">Score</th>
//             <th className="p-2 font-medium text-gray-600">Comments</th>
//             <th className="p-2 font-medium text-gray-600">Sentiment</th>
//           </tr>
//         </thead>
//         <tbody>
//           {posts.map((p, i) => (
//             <tr key={i} className="hover:bg-gray-50">
//               {/* Date */}
//               <td className="py-2 px-3 text-sm text-gray-500 whitespace-nowrap">
//                 {new Date(p.created_iso || p.created_utc * 1000).toLocaleDateString()}
//               </td>

//               {/* Title — now clickable */}
//               <td className="py-2 px-3 text-sm">
//                 <a
//                   href={p.permalink?.startsWith("http") ? p.permalink : `https://reddit.com${p.permalink}`}
//                   target="_blank"
//                   rel="noopener noreferrer"
//                   className="text-blue-600 underline hover:text-blue-800"
//                 >
//                   {p.title || "(No Title)"}
//                 </a>
//               </td>

//               {/* Score */}
//               <td className="py-2 px-3 text-sm text-gray-700">{p.score}</td>

//               {/* Comments */}
//               <td className="py-2 px-3 text-sm text-gray-700">{p.num_comments}</td>

//               {/* Sentiment */}
//               <td className="py-2 px-3 text-sm text-gray-700">
//                 {typeof p.sentiment === "number"
//                   ? p.sentiment.toFixed(2)
//                   : p.sentiment || "—"}
//               </td>
//             </tr>
//           ))}
//         </tbody>

//       </table>
//     </div>
//   );
// }
import React, { useState } from "react";
import { ArrowUp, ArrowDown, Minus } from "lucide-react";

export default function PostsTable({ posts }) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: null });

  const handleSort = (key) => {
    setSortConfig((prev) => {
      // Cycle through: none → ascending → descending → none
      if (prev.key !== key) {
        return { key, direction: "asc" };
      } else if (prev.direction === "asc") {
        return { key, direction: "desc" };
      } else {
        return { key: null, direction: null };
      }
    });
  };

  const sortedPosts = React.useMemo(() => {
    if (!posts || !Array.isArray(posts)) return [];
    if (!sortConfig.key || !sortConfig.direction) return posts;

    return [...posts].sort((a, b) => {
      const aVal =
        sortConfig.key === "engagement"
          ? (a.score || 0) + (a.num_comments || 0)
          : a[sortConfig.key] || 0;
      const bVal =
        sortConfig.key === "engagement"
          ? (b.score || 0) + (b.num_comments || 0)
          : b[sortConfig.key] || 0;

      if (aVal < bVal) return sortConfig.direction === "asc" ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === "asc" ? 1 : -1;
      return 0;
    });
  }, [posts, sortConfig]);

  const getSortIcon = (key) => {
    if (sortConfig.key !== key) return <Minus size={14} color="#000000" />;
    if (sortConfig.direction === "asc") return <ArrowUp size={14} color="#0e6e66" />;
    if (sortConfig.direction === "desc") return <ArrowDown size={14} color="#d63636" />;
    return <Minus size={14} color="#000000" />;
  };

  if (!posts || posts.length === 0) {
    return (
      <div className="text-gray-500 text-center py-8">
        <p className="text-sm">No post data available.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50">
            <th className="py-3 px-4 text-left font-semibold text-gray-700">Date</th>
            <th className="py-3 px-4 text-left font-semibold text-gray-700">Title</th>
            <th className="py-3 px-4 text-left font-semibold text-gray-700">
              <button
                className="flex items-center gap-1 hover:text-blue-600 transition-colors"
                onClick={() => handleSort("score")}
              >
                Score {getSortIcon("score")}
              </button>
            </th>
            <th className="py-3 px-4 text-left font-semibold text-gray-700">
              <button
                className="flex items-center gap-1 hover:text-blue-600 transition-colors"
                onClick={() => handleSort("engagement")}
              >
                Engagement {getSortIcon("engagement")}
              </button>
            </th>
            <th className="py-3 px-4 text-left font-semibold text-gray-700">Sentiment</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {sortedPosts.map((p, idx) => {
            const date = new Date(p.created_iso || p.created_utc * 1000 || 0)
              .toISOString()
              .slice(0, 10);

            const engagement = (p.score || 0) + (p.num_comments || 0);

            const getSentimentStyle = () => {
              const sent = p.sentiment?.toLowerCase() || "";
              if (sent.startsWith("pos")) return "text-emerald-700 bg-emerald-50 border-emerald-200";
              if (sent.startsWith("neg")) return "text-red-700 bg-red-50 border-red-200";
              return "text-gray-700 bg-gray-50 border-gray-200";
            };

            return (
              <tr key={idx} className="hover:bg-blue-50 transition-colors">
                <td className="py-3 px-4 text-gray-600 whitespace-nowrap">{date}</td>
                <td className="py-3 px-4">
                  {p.permalink ? (
                    <a
                      href={p.permalink.startsWith("http") ? p.permalink : `https://reddit.com${p.permalink}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                    >
                      {p.title || "(untitled post)"}
                    </a>
                  ) : (
                    <span className="text-gray-900">{p.title || "(untitled post)"}</span>
                  )}
                </td>

                <td className="py-3 px-4 text-gray-900 font-medium">{p.score ?? 0}</td>
                <td className="py-3 px-4 text-gray-900 font-medium">{engagement}</td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-1 rounded-md text-xs font-medium border ${getSentimentStyle()}`}>
                    {p.sentiment || "Neutral"}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
