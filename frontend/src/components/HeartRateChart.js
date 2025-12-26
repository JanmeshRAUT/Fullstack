import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";
import { useHeartRate } from "../hooks/useHeartRate";

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: '#fff',
        border: '1px solid #e2e8f0',
        padding: '8px 12px',
        borderRadius: '8px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
      }}>
        <p style={{margin: 0, fontSize: '0.85rem', color: '#64748b'}}>Time: {label}s</p>
        <p style={{margin: 0, fontSize: '0.95rem', fontWeight: 600, color: '#0f172a'}}>
          {payload[0].value.toFixed(0)} BPM
        </p>
      </div>
    );
  }
  return null;
};

export default function HeartRateChart() {
  const heartRates = useHeartRate();

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={heartRates} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorBpm" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#000" strokeOpacity={0.05} />
          <XAxis 
             dataKey="time" 
             tick={{fontSize: 10, fill: '#cbd5e1'}} 
             tickLine={false}
             axisLine={false}
             interval="preserveStartEnd"
          />
          <YAxis 
            domain={[40, 140]} 
            hide={true}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#ef4444', strokeWidth: 1, strokeDasharray: '4 4' }}/>
          
          <ReferenceLine y={100} stroke="#fecaca" strokeDasharray="3 3" />
          
          <Area
            type="monotone"
            dataKey="bpm"
            stroke="#ef4444"
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#colorBpm)"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>

      <div style={{
          position: 'absolute', top: 10, right: 20, 
          textAlign: 'right', pointerEvents: 'none'
      }}>
          <div style={{fontSize: '2rem', fontWeight: 800, color: '#ef4444', lineHeight: 1, letterSpacing: '-1px'}}>
             {heartRates.length > 0 ? (heartRates[heartRates.length-1].bpm > 0 ? heartRates[heartRates.length-1].bpm : "--") : "--"}
          </div>
          <div style={{fontSize: '0.75rem', fontWeight: 700, color: '#ef4444', opacity: 0.8}}>BPM</div>
      </div>
    </div>
  );
}
