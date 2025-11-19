// // frontend/src/components/ChartPanel.jsx
// import React from "react";
// import {
//   LineChart,
//   Line,
//   BarChart,
//   Bar,
//   XAxis,
//   YAxis,
//   Tooltip,
//   ResponsiveContainer,
//   CartesianGrid,
// } from "recharts";

// export function SentimentOverTime({ data = [] }) {
//   if (!data || data.length === 0)
//     return (
//       <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100 text-gray-500 text-sm text-center">
//         No sentiment data available.
//       </div>
//     );

//   return (
//     <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100">
//       <h4 className="font-semibold mb-2">Sentiment Over Time</h4>
//       <ResponsiveContainer width="100%" height={250}>
//         <LineChart
//           data={data}
//           margin={{ top: 10, right: 20, bottom: 10, left: 0 }}
//         >
//           <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
//           <XAxis dataKey="date" tick={{ fontSize: 12 }} />
//           <YAxis
//             domain={[-1, 1]}
//             ticks={[-1, -0.5, 0, 0.5, 1]}
//             tick={{ fontSize: 12 }}
//           />
//           <Tooltip />
//           <Line
//             type="monotone"
//             dataKey="sentiment"
//             stroke="#86BC25"
//             strokeWidth={2}
//             dot={{ r: 3 }}
//           />
//         </LineChart>
//       </ResponsiveContainer>
//     </div>
//   );
// }

// export function EngagementOverTime({ data = [] }) {
//   if (!data || data.length === 0)
//     return (
//       <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100 text-gray-500 text-sm text-center">
//         No engagement data available.
//       </div>
//     );

//   return (
//     <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100">
//       <h4 className="font-semibold mb-2">Engagement Over Time</h4>
//       <ResponsiveContainer width="100%" height={250}>
//         <BarChart
//           data={data}
//           margin={{ top: 10, right: 20, bottom: 10, left: 0 }}
//         >
//           <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
//           <XAxis dataKey="date" tick={{ fontSize: 12 }} />
//           <YAxis tick={{ fontSize: 12 }} />
//           <Tooltip />
//           <Bar dataKey="engagement" fill="#5D9732" />
//         </BarChart>
//       </ResponsiveContainer>
//     </div>
//   );
// }

// export function SentimentDistribution({ pos, neu, neg }) {
//   const data = [
//     { name: "Positive", value: pos, fill: "#86BC25" },
//     { name: "Neutral", value: neu, fill: "#d1d5db" },
//     { name: "Negative", value: neg, fill: "#EF4444" },
//   ];

//   if (pos + neu + neg === 0)
//     return (
//       <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100 text-gray-500 text-sm text-center">
//         No sentiment distribution data.
//       </div>
//     );

//   return (
//     <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100">
//       <h4 className="font-semibold mb-2">Sentiment Distribution</h4>
//       <ResponsiveContainer width="100%" height={250}>
//         <BarChart
//           data={data}
//           margin={{ top: 10, right: 20, bottom: 10, left: 0 }}
//         >
//           <XAxis dataKey="name" tick={{ fontSize: 12 }} />
//           <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
//           <Tooltip />
//           <Bar dataKey="value">
//             {data.map((entry, index) => (
//               <cell key={`cell-${index}`} fill={entry.fill} />
//             ))}
//           </Bar>
//         </BarChart>
//       </ResponsiveContainer>
//     </div>
//   );
// }
import React from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const DeloitteGreen = "#0e6e66";
const DeloitteLightGreen = "#86bfa5";
const DeloitteGray = "#e5e7eb";

// === Sentiment Over Time ===
export const SentimentOverTime = ({ data }) => {
  const hasData = data && data.length > 0;

  return (
    <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100">
      <h4 className="font-semibold mb-2 text-[#0e6e66]">Sentiment Over Time</h4>
      {hasData ? (
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={DeloitteGray} />
            <XAxis dataKey="date" />
            <YAxis domain={[-1, 1]} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="sentiment"
              stroke={DeloitteGreen}
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <p className="text-gray-400 text-sm">No sentiment data available.</p>
      )}
    </div>
  );
};

// === Engagement Over Time ===
export const EngagementOverTime = ({ data }) => {
  const hasData = data && data.length > 0;

  return (
    <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100">
      <h4 className="font-semibold mb-2 text-[#0e6e66]">Engagement Over Time</h4>
      {hasData ? (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={DeloitteGray} />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="engagement" fill={DeloitteLightGreen} />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <p className="text-gray-400 text-sm">No engagement data available.</p>
      )}
    </div>
  );
};

// === Sentiment Distribution ===
// === Sentiment Distribution ===
// === Sentiment Distribution ===
export const SentimentDistribution = ({ pos, neu, neg }) => {
  const total = pos + neu + neg;

  const data = [
    {
      name: "Positive",
      value: pos,
      label: total > 0 ? `${Math.round((pos / total) * 100)}% (${pos} posts)` : "0%",
    },
    {
      name: "Neutral",
      value: neu,
      label: total > 0 ? `${Math.round((neu / total) * 100)}% (${neu} posts)` : "0%",
    },
    {
      name: "Negative",
      value: neg,
      label: total > 0 ? `${Math.round((neg / total) * 100)}% (${neg} posts)` : "0%",
    },
  ];

  const COLORS = ["#00a58a", "#d1d5db", "#ef4444"];

  return (
    <div className="bg-white rounded-xl shadow-card p-4 border border-gray-100">
      <h4 className="font-semibold mb-2 text-[#0e6e66]">
        Sentiment Distribution
      </h4>

      {total > 0 ? (
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              cx="50%"
              cy="50%"
              outerRadius={80}

              // ⬇️ LABEL NOW ONLY SHOWS % + POSTS  
              label={(entry) => entry.label}
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={COLORS[index]} />
              ))}
            </Pie>

            {/* Tooltip showing percentage + posts */}
            <Tooltip
              formatter={(value, name, props) => {
                const entry = data.find((d) => d.name === props.name);
                return entry ? entry.label : value;
              }}
            />

            {/* Legend shows only names */}
            <Legend formatter={(value) => value} />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <p className="text-gray-400 text-sm">
          No sentiment distribution data.
        </p>
      )}
    </div>
  );
};
