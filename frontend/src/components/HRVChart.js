import React, { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";

export default function HRVChart() {
  const [hrvHistory, setHrvHistory] = useState([]);
  const [rawHrBuffer, setRawHrBuffer] = useState([]);

  useEffect(() => {
    const fetchHR = async () => {
      try {
        const res = await fetch("http://127.0.0.1:5000/combined_data");
        const data = await res.json();
        
        // Get Heart Rate (0 if invalid)
        const currentHr = data.sensor?.hr || 0;

        // 1. Update Raw Buffer (Keep last 20 readings ~ 10-20 seconds)
        let newBuffer = [...rawHrBuffer, currentHr];
        if (newBuffer.length > 20) newBuffer.shift(); 
        setRawHrBuffer(newBuffer);

        // 2. Calculate Standard Deviation (HRV Proxy)
        // Filter out zeros/noise for calculation
        const validReadings = newBuffer.filter(h => h > 40 && h < 200);
        
        let sdnn = 0;
        if (validReadings.length > 2) {
            const mean = validReadings.reduce((sum, val) => sum + val, 0) / validReadings.length;
            const variance = validReadings.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / validReadings.length;
            sdnn = Math.sqrt(variance);
        }

        // 3. Update Chart Data
        setHrvHistory(prev => {
           const time = prev.length > 0 ? prev[prev.length-1].time + 1 : 0;
           const newData = [...prev, { time, value: sdnn }];
           if (newData.length > 30) newData.shift();
           return newData;
        });

      } catch (err) {
        console.error("HRV Fetch Error", err);
      }
    };

    const interval = setInterval(fetchHR, 1000); // 1Hz update
    return () => clearInterval(interval);
  }, [rawHrBuffer]);

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={hrvHistory} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorHrv" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#000" strokeOpacity={0.05} />
          <XAxis 
             dataKey="time" 
             tick={{fontSize: 10, fill: '#cbd5e1'}} 
             tickLine={false}
             axisLine={false}
          />
          <YAxis 
            domain={[0, 20]} 
            hide={true}
          />
          <Tooltip 
             contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                fontSize: '12px'
             }}
             formatter={(val) => [`${val.toFixed(1)}`, 'HRV (SDNN)']}
             labelStyle={{display: 'none'}}
             cursor={{ stroke: '#8b5cf6', strokeWidth: 1, strokeDasharray: '4 4' }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#8b5cf6"
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#colorHrv)"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
      
      {/* METRIC OVERLAY */}
      <div style={{
          position: 'absolute', top: 10, right: 20, 
          textAlign: 'right', pointerEvents: 'none'
      }}>
          <div style={{fontSize: '1.8rem', fontWeight: 800, color: '#8b5cf6', lineHeight: 1}}>
             {hrvHistory.length > 0 ? hrvHistory[hrvHistory.length-1].value.toFixed(1) : "--"}
          </div>
          <div style={{fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8'}}>ms (SDNN)</div>
      </div>
    </div>
  );
}
