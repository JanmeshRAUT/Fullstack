import React, { useState, useEffect, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { Activity } from "lucide-react";
import { motion } from "framer-motion";

// Custom Tooltip
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="tooltip-box">
        <p className="tooltip-time">{`Time: ${label}`}</p>
        <p className="tooltip-value">{`HRV (SDNN): ${payload[0].value.toFixed(0)} ms`}</p>
      </div>
    );
  }
  return null;
};

export default function HRV() {
  const [data, setData] = useState(() =>
    Array.from({ length: 10 }, (_, i) => ({
      time: `${i}s`,
      value: 50,
    }))
  );

  const rrRef = useRef([]);
  const timeRef = useRef(data.length - 1);

  const hrToRR = (hr) => (hr > 0 ? 60000 / hr : 1000);

  useEffect(() => {
    const fetchHR = async () => {
      try {
        const res = await fetch("http://localhost:5000/sensor_data");
        const json = await res.json();
        return json.hr ?? 70;
      } catch (e) {
        console.error("Failed to fetch HR:", e);
        return 70;
      }
    };

    const interval = setInterval(async () => {
      timeRef.current += 1;
      const hr = await fetchHR();
      const rr = hrToRR(hr);

      rrRef.current.push(rr);
      if (rrRef.current.length > 20) rrRef.current.shift();

      const meanRR =
        rrRef.current.reduce((acc, v) => acc + v, 0) / rrRef.current.length;
      const sdnn = Math.sqrt(
        rrRef.current.reduce((acc, v) => acc + (v - meanRR) ** 2, 0) /
          rrRef.current.length
      );

      setData((prev) => {
        const newPoint = { time: `${timeRef.current}s`, value: Math.round(sdnn) };
        return [...prev.slice(-9), newPoint];
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      className="card hrv-card"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="card-header">
        <Activity size={20} className="icon activity-icon" />
        <h4 className="card-title">
          Heart Rate Variability <span className="unit">(SDNN in ms)</span>
        </h4>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12, fill: "#475569" }}
              tickLine={false}
              axisLine={{ stroke: "#cbd5e1" }}
            />
            <YAxis
              domain={[20, 100]}
              tick={{ fontSize: 12, fill: "#475569" }}
              tickLine={false}
              axisLine={false}
            />
            <ReferenceLine
              y={50}
              stroke="#10b981"
              strokeDasharray="5 5"
              label={{
                value: "Good HRV baseline",
                position: "top",
                fill: "#10b981",
                fontSize: 10,
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#ef4444"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: "#ef4444", stroke: "#fff", strokeWidth: 2 }}
              isAnimationActive={true}
              animationDuration={400}
              animationEasing="linear"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
