import React, { useState, useEffect, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine, // Added for visual context
} from "recharts";
import { Activity } from "lucide-react";

// Custom Tooltip for cleaner display
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ backgroundColor: '#fff', padding: '10px', border: '1px solid #ff5555', borderRadius: '4px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
        <p style={{ margin: 0, fontWeight: 'bold' }}>{`Time: ${label}`}</p>
        <p style={{ margin: 0, color: '#ff5555' }}>
          {`HRV (SDNN): ${payload[0].value.toFixed(0)} ms`}
        </p>
      </div>
    );
  }
  return null;
};

export default function HRV() {
  const [data, setData] = useState(() =>
    Array.from({ length: 10 }, (_, i) => ({
      time: `${i}s`, // Corrected initial time
      value: 50, // initial HRV ms
    }))
  );

  const rrRef = useRef([]); 
  const timeRef = useRef(data.length - 1); // Start time from 9 (last index)

  // Convert HR (bpm) to RR interval in ms
  const hrToRR = (hr) => (hr > 0 ? 60000 / hr : 1000);

  useEffect(() => {
    const fetchHR = async () => {
      try {
        const res = await fetch("http://localhost:5000/sensor_data");
        const json = await res.json();
        return json.hr ?? 70; // fallback if HR missing
      } catch (e) {
        console.error("Failed to fetch HR:", e);
        return 70;
      }
    };

    const interval = setInterval(async () => {
      // CORRECTED: Increment time by 1s to match 1000ms interval
      timeRef.current += 1; 
      const hr = await fetchHR();
      const rr = hrToRR(hr);

      // Increased to keep 20s of RR data for a slightly better SDNN base
      rrRef.current.push(rr);
      if (rrRef.current.length > 20) rrRef.current.shift(); 

      // Compute SDNN
      const meanRR =
        rrRef.current.reduce((acc, v) => acc + v, 0) / rrRef.current.length;
      const sdnn = Math.sqrt(
        rrRef.current.reduce((acc, v) => acc + (v - meanRR) ** 2, 0) /
          rrRef.current.length
      );

      setData((prev) => {
        const newPoint = {
          time: `${timeRef.current}s`,
          value: Math.round(sdnn),
        };
        // Use slice(-9) to keep the last 10 points (for 10s visibility)
        return [...prev.slice(-9), newPoint]; 
      });
    }, 1000); // 1 second update interval

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card p-4 shadow-md rounded-2xl bg-white" style={{ fontFamily: 'sans-serif' }}>
      <h4 style={{ display: 'flex', alignItems: 'center', color: '#333' }}>
        <Activity size={20} style={{ marginRight: '8px', color: '#ff5555' }} />
        Heart Rate Variability <span style={{ color: "#666", marginLeft: '5px', fontSize: '0.9em' }}>(SDNN in ms)</span>
      </h4>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
          
          {/* Enhanced Grid */}
          <CartesianGrid 
            strokeDasharray="4 4" 
            stroke="#e0e0e0" 
            vertical={false} // Hide vertical grid lines
          />
          
          {/* X-Axis: Time (s) */}
          <XAxis 
            dataKey="time" 
            tick={{ fontSize: 11, fill: '#666' }} 
            tickLine={false} 
            axisLine={{ stroke: '#999' }}
          />
          
          {/* Y-Axis: HRV (ms) */}
          <YAxis 
            domain={[20, 100]} // Tightened domain for better visualization of variance
            tick={{ fontSize: 11, fill: '#666' }} 
            tickLine={false} 
            axisLine={false}
          />
          
          {/* Reference Line for Good HRV Context */}
          <ReferenceLine y={50} stroke="#10b981" strokeDasharray="5 5" label={{ value: 'Good HRV baseline', position: 'top', fill: '#10b981', fontSize: 10 }} />

          {/* Custom Tooltip */}
          <Tooltip content={<CustomTooltip />} />
          
          {/* Main Data Line */}
          <Line
            type="monotone"
            dataKey="value"
            stroke="#ff5555" // Vibrant Red
            strokeWidth={3} // Thicker Line
            dot={false}     // No dots for a continuous trace
            activeDot={{ r: 5, fill: '#ff5555', stroke: '#fff', strokeWidth: 2 }} 
            isAnimationActive={true}
            animationDuration={300} // Much faster animation for 'live' feel
            animationEasing="linear" // Linear transition for ECG-like movement
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}