import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useSensorData } from "../hooks/useSensorData";
import { Thermometer } from "lucide-react";
import { motion } from "framer-motion";

export default function BodyTemperatureChart() {
  const { sensorData, dataHistory } = useSensorData();

  const temp = sensorData?.temperature;
  const getTempStatus = (value) => {
    if (value < 36.0) return { label: "Low", color: "#0ea5e9" }; // Blue
    if (value >= 36.0 && value <= 37.5) return { label: "Normal", color: "#16a34a" }; // Green
    return { label: "High", color: "#dc2626" }; // Red
  };

  const status = temp ? getTempStatus(temp) : { label: "Loading", color: "#94a3b8" };

  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <h4 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <Thermometer size={20} className="icon-mr" />
        Body Temperature
        <span style={{ color: "#64748b" }}>(°C)</span>
      </h4>

      <div className="current-value" style={{ fontSize: "1.25rem", fontWeight: "700" }}>
        {temp ? `${temp.toFixed(2)}°C` : "Loading..."}
      </div>

      {temp && (
        <p
          style={{
            color: status.color,
            fontWeight: "600",
            fontSize: "0.9rem",
            marginTop: "-4px",
          }}
        >
          {status.label} Temperature
        </p>
      )}

      <div style={{ width: "100%", height: 200, marginTop: "10px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={dataHistory}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12, fill: "#475569" }}
              tickFormatter={(time) => time.split(":").slice(0, 2).join(":")}
            />
            <YAxis
              domain={[32, 40]}
              tick={{ fontSize: 12, fill: "#475569" }}
              tickFormatter={(value) => value.toFixed(1)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                fontSize: "0.85rem",
              }}
            />
            <Line
              type="monotone"
              dataKey="temperature"
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
