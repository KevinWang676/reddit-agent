// import React from "react";

// export default function MetricTile({ label, value }) {
//   return (
//     <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100 text-center">
//       <div className="text-sm text-gray-500 mb-1">{label}</div>
//       <div className="text-2xl font-semibold text-[#0e6e66]">{value}</div>
//     </div>
//   );
// }

// import React from "react";

// export default function MetricTile({ label, value, color }) {
//   return (
//     <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100 text-center">
//       <div className="text-sm text-gray-500 mb-1">{label}</div>
//       <div className={`text-2xl font-semibold ${color || "text-[#0e6e66]"}`}>
//         {value}
//       </div>
//     </div>
//   );
// }

// import React from "react";

// export default function MetricTile({ label, value, color }) {
//   return (
//     <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-3 flex flex-col items-center justify-center text-center">
//       <div className="text-sm text-gray-500 mb-1">{label}</div>
//       <div className={`text-xl font-semibold ${color || "text-gray-800"}`}>
//         {value}
//       </div>
//     </div>
//   );
// }
import React, { useState, useRef, useEffect } from "react";
import { Info } from "lucide-react";

const DEFINITIONS = {
  "Total Engagement":
    "Total Engagement measures how much interaction the posts within this insight received. It combines each post’s Reddit score (upvotes minus downvotes) with its number of comments, capturing both visibility and discussion intensity.",

  "Number of Posts":
    "Number of Posts is the total number of Reddit posts included in this insight cluster. More posts generally indicate a widely discussed theme.",

  "Average Sentiment":
    "Average Sentiment reflects the overall emotional tone of the posts on a scale from −1 (negative) to +1 (positive), summarizing how users generally feel about the topic.",

  "Dominant Sentiment":
    "Dominant Sentiment identifies whether Positive, Neutral, or Negative emotion is discussed the most within the cluster, showing the prevailing mood."
};

export default function MetricTile({ label, value, color }) {
  const [showTip, setShowTip] = useState(false);
  const tipRef = useRef(null);

  // === CLOSE TOOLTIP WHEN CLICKING OUTSIDE ===
  useEffect(() => {
    function handleClickOutside(e) {
      if (tipRef.current && !tipRef.current.contains(e.target)) {
        setShowTip(false);
      }
    }

    if (showTip) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showTip]);

  // === Calculate tooltip shift if near window edge ===
  const getTooltipShift = () => {
    if (!tipRef.current) return "translateX(-50%) translateY(-8px)";

    const rect = tipRef.current.getBoundingClientRect();
    const rightEdge = rect.right + 40;

    // If near right side → shift tooltip left
    if (rightEdge > window.innerWidth) {
      return "translateX(-90%) translateY(-8px)";
    }

    return "translateX(-70%) translateY(-8px)";
  };

  return (
    <div className="relative bg-gradient-to-br from-white to-gray-50 rounded-xl border-2 border-gray-200 shadow-sm p-4 flex flex-col items-center justify-center text-center hover:shadow-md transition-all">

      {/* Label + Info Icon */}
      <div className="flex items-center gap-1.5 text-sm font-medium text-gray-600 mb-2">
        <span>{label}</span>

        <div className="relative" ref={tipRef}>
          <Info
            className="w-4 h-4 cursor-pointer text-gray-400 hover:text-blue-600 transition-colors"
            onClick={() => setShowTip((prev) => !prev)}
          />

          {/* Tooltip (auto-shifts when near right screen edge) */}
          {showTip && (
            <div
              className="
                absolute
                bottom-6 left-1/2
                w-72
                bg-white
                border-2 border-blue-200
                rounded-xl
                shadow-2xl
                p-4
                text-xs text-gray-700
                leading-relaxed
                z-50
              "
              style={{
                transform: getTooltipShift(),
              }}
            >
              <div className="font-semibold text-blue-700 mb-2">{label}</div>
              {DEFINITIONS[label]}
            </div>
          )}
        </div>
      </div>

      {/* Value */}
      <div className={`text-2xl font-bold ${color || "text-gray-900"}`}>
        {value}
      </div>
    </div>
  );
}
