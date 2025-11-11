import React from "react";
import { useHeartRate } from "../hooks/useHeartRate";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { Heart } from "lucide-react";
import { motion } from "framer-motion";

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="tooltip-time">{`Time: ${label} s`}</p>
        <p className="tooltip-bpm">{`BPM: ${payload[0].value.toFixed(0)}`}</p>
      </div>
    );
  }
  return null;
};

const HeartRateChart = () => {
  const heartRates = useHeartRate();

  return (
    <motion.div
      className="card heart-rate-card"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <h4 className="chart-title">
        <Heart size={20} className="heart-icon" />
        Real-Time Heart Rate <span className="unit">(bpm)</span>
      </h4>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart
          data={heartRates}
          margin={{ top: 10, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="5 5"
            vertical={false}
            className="chart-grid"
          />

          <XAxis
            dataKey="time"
            label={{
              value: "Time (s)",
              position: "insideBottom",
              dy: 15,
              fill: "#64748b",
            }}
            tick={{ fontSize: 11, fill: "#64748b" }}
            tickLine={false}
          />

          <YAxis
            domain={[60, 120]}
            label={{
              value: "BPM",
              angle: -90,
              position: "insideLeft",
              dx: -5,
              fill: "#64748b",
            }}
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
          />

          <ReferenceLine
            y={100}
            stroke="#f97316"
            strokeDasharray="5 5"
            label={{
              value: "Target Max",
              position: "top",
              fill: "#f97316",
              fontSize: 10,
            }}
          />

          <ReferenceLine
            y={60}
            stroke="#10b981"
            strokeDasharray="5 5"
            label={{
              value: "Resting Min",
              position: "bottom",
              fill: "#10b981",
              fontSize: 10,
            }}
          />

          <Tooltip content={<CustomTooltip />} />

          <Line
            type="monotone"
            dataKey="bpm"
            stroke="#ef4444"
            strokeWidth={3}
            dot={false}
            activeDot={{
              r: 6,
              fill: "#ef4444",
              stroke: "#fff",
              strokeWidth: 2,
            }}
            animationDuration={150}
          />
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  );
};

export default HeartRateChart;
