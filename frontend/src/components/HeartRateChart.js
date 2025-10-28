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
  ReferenceLine, // Added for high/low indicators
} from "recharts";
import { Heart } from "lucide-react";

// Custom Tooltip component for a cleaner look
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip" style={{ 
          backgroundColor: '#fff', 
          padding: '10px', 
          border: '1px solid #ccc', 
          borderRadius: '4px' 
      }}>
        <p className="label" style={{ margin: 0 }}>
          {`Time: ${label} s`}
        </p>
        <p className="intro" style={{ margin: 0, color: '#ef4444' }}>
          {`BPM: ${payload[0].value.toFixed(0)}`}
        </p>
      </div>
    );
  }
  return null;
};

const HeartRateChart = () => {
  const heartRates = useHeartRate();

  return (
    <div className="card" style={{ 
        padding: '20px', 
        borderRadius: '8px', 
        boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        backgroundColor: '#f8fafc' // Subtle background
    }}>
      <h4 style={{ 
          display: 'flex', 
          alignItems: 'center', 
          color: '#334155' 
      }}>
        <Heart size={20} className="icon-mr" style={{ marginRight: '8px', color: '#ef4444' }} />
        Real-Time Heart Rate <span style={{ color: "#64748b", marginLeft: '5px' }}>(bpm)</span>
      </h4>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={heartRates} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
          {/* Enhanced Grid: Solid lines for Y-axis, dashes for X-axis */}
          <CartesianGrid 
            strokeDasharray="5 5" // Dashed X-axis lines
            vertical={false}       // Hide vertical lines
            stroke="#e2e8f0" 
          />
          
          {/* X-Axis: Time (s) */}
          <XAxis
            dataKey="time"
            label={{ value: "Time (s)", position: "insideBottom", dy: 15, fill: '#64748b' }}
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickLine={false} // Hide tick lines
          />

          {/* Y-Axis: BPM */}
          <YAxis
            domain={[60, 120]} // Tightened domain for better focus on normal range
            label={{ value: "BPM", angle: -90, position: "insideLeft", dx: -5, fill: '#64748b' }}
            tick={{ fontSize: 11, fill: '#64748b' }}
            axisLine={false} // Hide the main axis line
            tickLine={false} // Hide tick lines
          />

          {/* Reference Lines for Context */}
          <ReferenceLine y={100} stroke="#f97316" strokeDasharray="5 5" label={{ value: 'Target Max', position: 'top', fill: '#f97316', fontSize: 10 }} />
          <ReferenceLine y={60} stroke="#10b981" strokeDasharray="5 5" label={{ value: 'Resting Min', position: 'bottom', fill: '#10b981', fontSize: 10 }} />


          {/* Custom Tooltip */}
          <Tooltip content={<CustomTooltip />} />

          {/* Main Data Line */}
          <Line
            type="monotone"
            dataKey="bpm"
            stroke="#ef4444" // Bright red for a medical/urgent feel
            strokeWidth={3} // Thicker line
            dot={false}     // Hide dots for a cleaner, continuous look
            activeDot={{ r: 6, fill: '#ef4444', stroke: '#fff', strokeWidth: 2 }} // Highlight the hovered point
            isAnimationActive={true} // Keep animation active for smooth transitions (Crucial for real-time)
            animationDuration={150} // Faster transition for a 'live' look
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default HeartRateChart;