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
import { Thermometer } from 'lucide-react';

export default function BodyTemperatureChart() {
  const { sensorData, dataHistory } = useSensorData();

  return (
    <div className="card">
      <h4><Thermometer size={20} className="icon-mr" />Body Temperature<span style={{ color: "#64748b" }}>(°C)</span> </h4>
      <div className="current-value">
        {sensorData.temperature ? 
          `${sensorData.temperature.toFixed(2)}°C` : 
          "Loading..."
        }
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={dataHistory}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="time"
            tickFormatter={(time) => time.split(':')[0] + ':' + time.split(':')[1]}
          />
          <YAxis domain={[32, 40]} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="temperature"
            stroke="#ef4444"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
