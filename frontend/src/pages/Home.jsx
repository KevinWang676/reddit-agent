
// import React, { useEffect, useState } from "react";
// import { fetchInsights, fetchCategories } from "../api";
// import InsightCard from "../components/InsightCard.jsx";

// export default function Home({ onSelect }) {
//   const [insights, setInsights] = useState([]);
//   const [categories, setCategories] = useState([]);
//   const [filter, setFilter] = useState("All");

//   useEffect(() => {
//     fetchInsights().then(setInsights);
//     fetchCategories().then(setCategories);
//   }, []);

//   const filtered = filter === "All" ? insights : insights.filter(i => i.category === filter);

//   return (
//     <div className="space-y-4">
//       <div className="flex items-center gap-3">
//         <label className="text-sm text-gray-600">Category:</label>
//         <select className="border rounded-lg p-2" value={filter} onChange={(e)=> setFilter(e.target.value)}>
//           <option>All</option>
//           {categories.map(c => <option key={c.name}>{c.name}</option>)}
//         </select>
//         <span className="ml-auto text-sm text-gray-500">{filtered.length} insights</span>
//       </div>

//       <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
//         {filtered.map(ins => (
//           <InsightCard key={ins.id} insight={ins} onClick={()=> onSelect(ins.id)} />
//         ))}
//       </div>
//     </div>
//   );
// }



















// import React, { useEffect, useState } from "react";
// import { fetchInsights, fetchCategories } from "../api";
// import InsightCard from "../components/InsightCard.jsx";

// export default function Home({ onSelect }) {
//   const [insights, setInsights] = useState([]);
//   const [categories, setCategories] = useState([]);
//   const [filter, setFilter] = useState("All");
//   const [sortOption, setSortOption] = useState("Newest");

//   useEffect(() => {
//     fetchInsights().then(setInsights);
//     fetchCategories().then(setCategories);
//   }, []);

//   // === Filter logic ===
//   let filtered =
//     filter === "All" ? insights : insights.filter((i) => i.category === filter);

//   // === Sorting logic ===
//   filtered = [...filtered].sort((a, b) => {
//     switch (sortOption) {
//       case "Cluster Size ↑":
//         return a.cluster_size - b.cluster_size;
//       case "Cluster Size ↓":
//         return b.cluster_size - a.cluster_size;
//       case "Sentiment ↑":
//         return a.avg_sentiment - b.avg_sentiment;
//       case "Sentiment ↓":
//         return b.avg_sentiment - a.avg_sentiment;
//       case "Engagement ↑":
//         return a.total_engagement - b.total_engagement;
//       case "Engagement ↓":
//         return b.total_engagement - a.total_engagement;
//       case "Newest":
//       default:
//         return new Date(b.last_updated) - new Date(a.last_updated);
//     }
//   });

//   return (
//     <div className="space-y-4">
//       {/* === Top Filter & Sort Row === */}
//       <div className="flex items-center gap-3">
//         <label className="text-sm text-gray-600">Category:</label>
//         <select
//           className="border rounded-lg p-2"
//           value={filter}
//           onChange={(e) => setFilter(e.target.value)}
//         >
//           <option>All</option>
//           {categories.map((c) => (
//             <option key={c.name}>{c.name}</option>
//           ))}
//         </select>

//         {/* Sort Dropdown (next to Category) */}
//         <label className="text-sm text-gray-600 ml-2">Sort by:</label>
//         <select
//           className="border rounded-lg p-2"
//           value={sortOption}
//           onChange={(e) => setSortOption(e.target.value)}
//         >
//           <option value="Newest">Newest</option>
//           <option value="Cluster Size ↑">Cluster Size ↑</option>
//           <option value="Cluster Size ↓">Cluster Size ↓</option>
//           <option value="Sentiment ↑">Sentiment ↑</option>
//           <option value="Sentiment ↓">Sentiment ↓</option>
//           <option value="Engagement ↑">Engagement ↑</option>
//           <option value="Engagement ↓">Engagement ↓</option>
//         </select>

//         {/* Insight Count aligned to right */}
//         <span className="ml-auto text-sm text-gray-500">
//           {filtered.length} Insight{filtered.length !== 1 && "s"}
//         </span>
//       </div>

//       {/* === Insights Grid === */}
//       <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
//         {filtered.map((ins) => (
//           <InsightCard key={ins.id} insight={ins} onClick={() => onSelect(ins.id)} />
//         ))}
//       </div>
//     </div>
//   );
// }








// import React, { useEffect, useState } from "react";
// import { fetchInsights, fetchCategories } from "../api";
// import InsightCard from "../components/InsightCard.jsx";
// import { Plus, Minus } from "lucide-react";

// export default function Home({ onSelect }) {
//   const [insights, setInsights] = useState([]);
//   const [categories, setCategories] = useState([]);
//   const [expandedCategory, setExpandedCategory] = useState(null);
//   const [visibleCount, setVisibleCount] = useState({});

//   useEffect(() => {
//     fetchInsights().then(setInsights);
//     fetchCategories().then(setCategories);
//   }, []);

//   const toggleCategory = (cat) => {
//     if (expandedCategory === cat) setExpandedCategory(null);
//     else setExpandedCategory(cat);
//   };

//   const toggleSeeMore = (cat) => {
//     setVisibleCount((prev) => ({
//       ...prev,
//       [cat]: prev[cat] === "all" ? 5 : "all",
//     }));
//   };

//   return (
//     <div className="space-y-4">
//       <div className="flex items-center justify-between">
//         <h2 className="text-xl font-semibold text-gray-800">All Categories</h2>
//         <span className="text-sm text-gray-500">{insights.length} insights</span>
//       </div>

//       <div className="divide-y border rounded-lg">
//         {categories.map((cat) => {
//           const catInsights = insights.filter(
//             (i) => i.category === cat.name
//           );
//           const visible =
//             visibleCount[cat.name] === "all"
//               ? catInsights
//               : catInsights.slice(0, 5);

//           return (
//             <div key={cat.name} className="p-4">
//               <div
//                 className="flex justify-between items-center cursor-pointer hover:bg-gray-50 p-2 rounded-lg"
//                 onClick={() => toggleCategory(cat.name)}
//               >
//                 <h3 className="text-lg font-medium text-gray-800">
//                   {cat.name}
//                 </h3>
//                 {expandedCategory === cat.name ? (
//                   <Minus className="w-5 h-5 text-gray-600" />
//                 ) : (
//                   <Plus className="w-5 h-5 text-gray-600" />
//                 )}
//               </div>

//               {expandedCategory === cat.name && (
//                 <div className="mt-3 space-y-2">
//                   {visible.map((ins) => (
//                     <InsightCard
//                       key={ins.id}
//                       insight={ins}
//                       onClick={() => onSelect(ins.id)}
//                     />
//                   ))}

//                   {catInsights.length > 5 && (
//                     <button
//                       className="text-sm text-blue-600 hover:underline mt-2"
//                       onClick={() => toggleSeeMore(cat.name)}
//                     >
//                       {visibleCount[cat.name] === "all"
//                         ? "See less"
//                         : "See more"}
//                     </button>
//                   )}
//                 </div>
//               )}
//             </div>
//           );
//         })}
//       </div>
//     </div>
//   );
// }

import React, { useEffect, useState } from "react";
import { fetchInsights, fetchCategories } from "../api";
import InsightCard from "../components/InsightCard.jsx";
import { Plus, Minus } from "lucide-react";

export default function Home({ subreddit, onSelect }) {
  const [insights, setInsights] = useState([]);
  const [categories, setCategories] = useState([]);
  const [expandedCategory, setExpandedCategory] = useState(null);
  const [visibleCount, setVisibleCount] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sorting state
  const [sortBy, setSortBy] = useState("default"); // "default" | "posts" | "engagement"
  const [sortOrder, setSortOrder] = useState("desc"); // "asc" | "desc"

  useEffect(() => {
    if (!subreddit) return;
    
    setLoading(true);
    setError(null);
    
    Promise.all([
      fetchInsights(subreddit),
      fetchCategories(subreddit)
    ])
      .then(([insightsData, categoriesData]) => {
        setInsights(insightsData);
        setCategories(categoriesData);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load data:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [subreddit]);

  const toggleCategory = (cat) => {
    if (expandedCategory === cat) setExpandedCategory(null);
    else setExpandedCategory(cat);
  };

  const toggleSeeMore = (cat) => {
    setVisibleCount((prev) => ({
      ...prev,
      [cat]: prev[cat] === "all" ? 5 : "all",
    }));
  };

  // Apply sorting to insights inside each category
  const applySorting = (arr) => {
    if (sortBy === "default") return arr;

    return [...arr].sort((a, b) => {
      let valA, valB;

      if (sortBy === "posts") {
        valA = a.cluster_size;
        valB = b.cluster_size;
      } else if (sortBy === "engagement") {
        valA = a.total_engagement;
        valB = b.total_engagement;
      }

      return sortOrder === "asc" ? valA - valB : valB - valA;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading insights for r/{subreddit}...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-red-600 text-2xl">⚠️</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Failed to load data</h2>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Header Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Insights Overview</h2>
            <p className="text-sm text-gray-500 mt-1">Explore {insights.length} AI-generated insights across all categories</p>
          </div>
          <div className="px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
            <span className="text-2xl font-bold text-blue-700">{insights.length}</span>
            <p className="text-xs text-blue-600 mt-0.5">Total Insights</p>
          </div>
        </div>

        {/* Sorting Controls */}
        <div className="flex gap-4 items-center pt-4 border-t border-gray-200">
          {/* Sort By */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="default">Default</option>
              <option value="posts">Posts</option>
              <option value="engagement">Engagement</option>
            </select>
          </div>

          {/* Order (only shown when sortBy is NOT default) */}
          {sortBy !== "default" && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Order:</span>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Categories Accordion */}
      <div className="space-y-4">
        {categories.map((cat) => {
          // All insights in category
          let catInsights = insights.filter((i) => i.category === cat.name);

          // Apply sorting inside the category
          catInsights = applySorting(catInsights);

          const visible =
            visibleCount[cat.name] === "all"
              ? catInsights
              : catInsights.slice(0, 5);

          return (
            <div key={cat.name} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div
                className="flex justify-between items-center cursor-pointer hover:bg-gray-50 p-5 transition-colors"
                onClick={() => toggleCategory(cat.name)}
              >
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {cat.name}
                  </h3>
                  <span className="px-2.5 py-0.5 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
                    {catInsights.length}
                  </span>
                </div>
                {expandedCategory === cat.name ? (
                  <Minus className="w-5 h-5 text-gray-500" />
                ) : (
                  <Plus className="w-5 h-5 text-gray-500" />
                )}
              </div>

              {expandedCategory === cat.name && (
                <div className="border-t border-gray-200 bg-gray-50 p-4">
                  <div className="space-y-3">
                    {visible.map((ins) => (
                      <InsightCard
                        key={ins.id}
                        insight={ins}
                        onClick={() => onSelect(ins.id)}
                      />
                    ))}
                  </div>

                  {catInsights.length > 5 && (
                    <button
                      className="mt-4 text-sm font-medium text-blue-600 hover:text-blue-700 hover:underline"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSeeMore(cat.name);
                      }}
                    >
                      {visibleCount[cat.name] === "all"
                        ? "Show less"
                        : `Show ${catInsights.length - 5} more`}
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="flex items-center gap-2 mt-10 opacity-70">
        <img
          src="/src/assets/northwestern_logo.png"
          alt="Northwestern University"
          className="h-6 w-auto"
        />
        <span className="text-sm text-gray-600">
          Powered by Northwestern University
        </span>
      </div>
    </div>
  );
}
