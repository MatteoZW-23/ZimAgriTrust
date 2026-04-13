import React, { useRef, useState } from "react";

/**
 * Robust SVG LineChart for AgriTrust Financial Dashboards.
 * Designed to handle small time series without external dependencies like Chart.js or D3.
 */

const formatValue = (v) => {
  if (v >= 1000000) return `${(v / 1000000).toFixed(1)}M`;
  if (v >= 1000) return `${(v / 1000).toFixed(1)}K`;
  return String(v);
};

const defaultData = [
  { timestamp: 1, revenue: 10, volume: 5, risk: 2 },
  { timestamp: 2, revenue: 20, volume: 8, risk: 4 },
  { timestamp: 3, revenue: 15, volume: 12, risk: 3 },
  { timestamp: 4, revenue: 25, volume: 7, risk: 5 },
  { timestamp: 5, revenue: 35, volume: 15, risk: 2 },
];

export default function LineChart({
  data = defaultData,
  xKey = "timestamp",
  yKey = "revenue",
  color = "#2f6f42",
  height = 200,
  showArea = true,
}) {
  const [hoveredData, setHoveredData] = useState(null);

  if (!data || data.length === 0) return <div>No data available</div>;

  const padding = { top: 20, right: 30, bottom: 40, left: 50 };
  const graphWidth = 600 - padding.left - padding.right;
  const graphHeight = 300 - padding.top - padding.bottom;

  const xValues = data.map((d) => d[xKey]);
  const yValues = data.map((d) => d[yKey]);

  const yMin = 0;
  const yMax = Math.max(...yValues) * 1.2 || 10;
  const xMin = 0;
  const xMax = data.length - 1;

  const points = data.map((d, i) => ({
    x: padding.left + (i / xMax) * graphWidth,
    y: padding.top + graphHeight - ((d[yKey] - yMin) / (yMax - yMin)) * graphHeight,
    data: d,
  }));

  const pathD = `M ${points.map((p) => `${p.x},${p.y}`).join(" L ")}`;
  const areaD = `${pathD} L ${points[points.length - 1].x},${padding.top + graphHeight} L ${points[0].x},${padding.top + graphHeight} Z`;

  return (
    <div style={{ position: "relative", width: "100%", height, minHeight: "240px" }}>
      <svg
        viewBox="0 0 600 300"
        preserveAspectRatio="xMidYMid meet"
        style={{ width: "100%", height: "100%", overflow: "visible" }}
      >
        {/* Y-Axis Grid */}
        {[0, 0.25, 0.5, 0.75, 1].map((p, i) => {
          const val = yMin + p * (yMax - yMin);
          const y = padding.top + graphHeight - (p * graphHeight);
          return (
            <g key={i}>
              <line x1={padding.left} x2={padding.left + graphWidth} y1={y} y2={y} stroke="var(--border)" strokeDasharray="4 4" />
              <text x={padding.left - 10} y={y} textAnchor="end" alignmentBaseline="middle" fontSize="11" fill="var(--muted)">
                {formatValue(val)}
              </text>
            </g>
          );
        })}

        {/* Path and Area */}
        {showArea && <path d={areaD} fill={color} fillOpacity="0.1" />}
        <path d={pathD} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

        {/* Points */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="5"
            fill={color}
            stroke="#fff"
            strokeWidth="2"
            onMouseEnter={() => setHoveredData(p)}
            onMouseLeave={() => setHoveredData(null)}
            style={{ cursor: "pointer", transition: 'r 0.2s' }}
          />
        ))}

        {/* X-Axis labels (every 2nd point to avoid crowding) */}
        {data.map((d, i) => (
          i % 2 === 0 && (
            <text
              key={i}
              x={padding.left + (i / xMax) * graphWidth}
              y={padding.top + graphHeight + 20}
              textAnchor="middle"
              fontSize="11"
              fill="var(--muted)"
            >
              {String(d[xKey])}
            </text>
          )
        ))}
      </svg>

      {hoveredData && (
        <div
          style={{
            position: "absolute",
            left: `${(hoveredData.x / 600) * 100}%`,
            top: `${(hoveredData.y / 300) * 100}%`,
            transform: 'translate(-50%, -120%)',
            background: "#222",
            color: "#fff",
            padding: "8px 12px",
            borderRadius: "8px",
            fontSize: "12px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
            zIndex: 10,
            pointerEvents: "none"
          }}
        >
          <div style={{ opacity: 0.7 }}>{String(hoveredData.data[xKey])}</div>
          <div style={{ fontWeight: 'bold', color: 'var(--success)' }}>${hoveredData.data[yKey].toLocaleString()}</div>
        </div>
      )}
    </div>
  );
}
