import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { useHeadPosition } from "../hooks/useHeadPosition";
import { User } from "lucide-react";
import { motion } from "framer-motion";

export default function HeadPositionChart() {
  const positions = useHeadPosition();

  // Convert head position labels to numeric values for the graph
  const data = positions.map((pos, i) => ({
    time: i + 1,
    position:
      pos === "Up" ? -1 : pos === "Down" ? 1 : 0, // -1 = Up, 0 = Center, 1 = Down
  }));

  // Determine current head position status
  const currentPos = positions[positions.length - 1];

  const getPositionStatus = (pos) => {
    if (pos === "Up") return { label: "Looking Up", color: "#0ea5e9" }; // Blue
    if (pos === "Down") return { label: "Looking Down (Drowsy)", color: "#dc2626" }; // Red
    return { label: "Centered", color: "#16a34a" }; // Green
  };

  const status = currentPos
    ? getPositionStatus(currentPos)
    : { label: "Loading", color: "#94a3b8" };

  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <h4 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <User size={20} className="icon-mr" />
        Head Position
        <span style={{ color: "#64748b" }}>(Down ↕ Center ↕ Up)</span>
      </h4>

      <div
        className="current-value"
        style={{ fontSize: "1.25rem", fontWeight: "700" }}
      >
        {currentPos ? currentPos : "Loading..."}
      </div>

      {currentPos && (
        <p
          style={{
            color: status.color,
            fontWeight: "600",
            fontSize: "0.9rem",
            marginTop: "-4px",
          }}
        >
          {status.label}
        </p>
      )}

      <div style={{ width: "100%", height: 200, marginTop: "10px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12, fill: "#475569" }}
              label={{ value: "Time", position: "insideBottom", dy: 10 }}
            />
            <YAxis
              domain={[-1.2, 1.2]}
              ticks={[-1, 0, 1]}
              reversed
              tickFormatter={(v) =>
                v === -1 ? "Down" : v === 0 ? "Center" : "Up"
              }
              tick={{ fontSize: 12, fill: "#475569" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                fontSize: "0.85rem",
              }}
              formatter={(v) =>
                v === -1
                  ? "Looking Down"
                  : v === 0
                  ? "Centered"
                  : "Looking Up"
              }
            />
            <Line
              type="monotone"
              dataKey="position"
              stroke={status.color}
              strokeWidth={2.5}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
