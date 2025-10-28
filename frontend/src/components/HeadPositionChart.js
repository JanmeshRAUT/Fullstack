import React from "react";
import { useHeadPosition } from "../hooks/useHeadPosition";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { User } from 'lucide-react';

const HeadPositionChart = () => {
  const positions = useHeadPosition();

  // Convert head position labels to numeric values for the graph
  const data = positions.map((pos, i) => ({
    time: i + 1,
    position:
      pos === "Left" ? -1 : pos === "Right" ? 1 : 0, // -1 = Left, 0 = Center, 1 = Right
  }));

  return (
    <div className="card">
      <h4><User size={20} className="icon-mr" />
        Head Position{" "}
        <span style={{ color: "#64748b" }}>(Left ↔ Center ↔ Right)</span>
      </h4>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="time"
            label={{ value: "Time", position: "insideBottom", dy: 10 }}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            domain={[-1.2, 1.2]}
            ticks={[-1, 0, 1]}
            tickFormatter={(v) =>
              v === -1 ? "Down" : v === 0 ? "Center" : "UP"
            }
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            formatter={(v) =>
              v === -1 ? "Left Drift" : v === 0 ? "Center" : "Right Drift"
            }
          />
          <Line
            type="monotone"
            dataKey="position"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>

    
    </div>
  );
};

export default HeadPositionChart;
