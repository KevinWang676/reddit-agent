
// import React, { useEffect, useState } from "react";
// import { fetchCategories, fetchInsights } from "../api";
// import MetricTile from "../components/MetricTile.jsx";

// export default function CategoryOverview() {
//   const [categories, setCategories] = useState(["All"]);
//   const [selectedCategory, setSelectedCategory] = useState("All");
//   const [insights, setInsights] = useState([]);

//   // === Fetch categories and insights ===
//   useEffect(() => {
//     fetchCategories().then((data) => {
//       if (Array.isArray(data)) {
//         setCategories(["All", ...data.map((c) => c.name)]);
//       }
//     });

//     fetchInsights().then((data) => {
//       if (Array.isArray(data)) {
//         setInsights(data);
//       }
//     });
//   }, []);

//   // === Filter insights by selected category ===
//   const filteredInsights =
//     selectedCategory === "All"
//       ? insights
//       : insights.filter((i) => i.category === selectedCategory);

//   return (
//     <div className="space-y-6">
//       {/* Header */}
//       <div className="flex justify-between items-center">
//         <h2 className="text-2xl font-semibold text-gray-800">
//           Category Overview
//         </h2>
//         <select
//           className="border border-gray-300 rounded-md px-3 py-1 text-gray-700 shadow-sm"
//           value={selectedCategory}
//           onChange={(e) => setSelectedCategory(e.target.value)}
//         >
//           {categories.map((c, idx) => (
//             <option key={idx} value={c}>
//               {c}
//             </option>
//           ))}
//         </select>
//       </div>

//       {/* Category Tiles */}
//       <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
//         {categories
//           .filter((c) => c !== "All")
//           .map((c, idx) => (
//             <div
//               key={idx}
//               className={`p-4 rounded-xl border shadow-sm ${
//                 selectedCategory === c
//                   ? "border-green-600 bg-green-50"
//                   : "border-gray-200 bg-white"
//               }`}
//             >
//               <h3 className="text-lg font-semibold text-gray-800 mb-2">{c}</h3>
//               <p className="text-sm text-gray-600">
//                 {
//                   insights.filter((i) => i.category === c).length
//                 }{" "}
//                 insights
//               </p>
//             </div>
//           ))}
//       </div>

//       {/* Filtered Insight List */}
//       <div>
//         <h3 className="text-lg font-semibold text-gray-800 mt-6 mb-3">
//           Insights in “{selectedCategory}”
//         </h3>
//         {filteredInsights.length === 0 ? (
//           <p className="text-gray-500">No insights available.</p>
//         ) : (
//           <ul className="divide-y divide-gray-200">
//             {filteredInsights.map((i) => (
//               <li key={i.id} className="py-3">
//                 <div className="font-medium text-gray-800">{i.theme}</div>
//                 <div className="text-sm text-gray-600">{i.key_insight}</div>
//               </li>
//             ))}
//           </ul>
//         )}
//       </div>
//     </div>
//   );
// }

import React, { useEffect, useState } from "react";
import { fetchCategories, fetchInsights } from "../api";
import MetricTile from "../components/MetricTile.jsx";

export default function CategoryOverview() {
  const [categories, setCategories] = useState(["All"]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [insights, setInsights] = useState([]);
  const [sortOption, setSortOption] = useState("Newest");

  // === Fetch categories and insights ===
  useEffect(() => {
    fetchCategories().then((data) => {
      if (Array.isArray(data)) {
        setCategories(["All", ...data.map((c) => c.name)]);
      }
    });

    fetchInsights().then((data) => {
      if (Array.isArray(data)) {
        setInsights(data);
      }
    });
  }, []);

  // === Filter insights ===
  let filteredInsights =
    selectedCategory === "All"
      ? insights
      : insights.filter((i) => i.category === selectedCategory);

  // === Apply sorting ===
  filteredInsights = [...filteredInsights].sort((a, b) => {
    switch (sortOption) {
      case "Cluster Size ↑":
        return a.cluster_size - b.cluster_size;
      case "Cluster Size ↓":
        return b.cluster_size - a.cluster_size;
      case "Sentiment ↑":
        return a.avg_sentiment - b.avg_sentiment;
      case "Sentiment ↓":
        return b.avg_sentiment - a.avg_sentiment;
      case "Engagement ↑":
        return a.total_engagement - b.total_engagement;
      case "Engagement ↓":
        return b.total_engagement - a.total_engagement;
      case "Newest":
      default:
        return new Date(b.last_updated) - new Date(a.last_updated);
    }
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-semibold text-gray-800">
            Category Overview
          </h2>
          <select
            className="border border-gray-300 rounded-md px-3 py-1 text-gray-700 shadow-sm"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            {categories.map((c, idx) => (
              <option key={idx} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        {/* Sort dropdown */}
        <div>
          <select
            className="border border-gray-300 rounded-md px-3 py-1 text-gray-700 shadow-sm"
            value={sortOption}
            onChange={(e) => setSortOption(e.target.value)}
          >
            <option value="Newest">Newest</option>
            <option value="Cluster Size ↑">Cluster Size ↑</option>
            <option value="Cluster Size ↓">Cluster Size ↓</option>
            <option value="Sentiment ↑">Sentiment ↑</option>
            <option value="Sentiment ↓">Sentiment ↓</option>
            <option value="Engagement ↑">Engagement ↑</option>
            <option value="Engagement ↓">Engagement ↓</option>
          </select>
        </div>
      </div>

      {/* Category Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories
          .filter((c) => c !== "All")
          .map((c, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border shadow-sm ${
                selectedCategory === c
                  ? "border-green-600 bg-green-50"
                  : "border-gray-200 bg-white"
              }`}
            >
              <h3 className="text-lg font-semibold text-gray-800 mb-2">{c}</h3>
              <p className="text-sm text-gray-600">
                {insights.filter((i) => i.category === c).length} insights
              </p>
            </div>
          ))}
      </div>

      {/* Sorted Insight List */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mt-6 mb-3">
          Insights in “{selectedCategory}”
        </h3>
        {filteredInsights.length === 0 ? (
          <p className="text-gray-500">No insights available.</p>
        ) : (
          <ul className="divide-y divide-gray-200">
            {filteredInsights.map((i) => (
              <li key={i.id} className="py-3">
                <div className="font-medium text-gray-800">{i.theme}</div>
                <div className="text-sm text-gray-600">{i.key_insight}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
