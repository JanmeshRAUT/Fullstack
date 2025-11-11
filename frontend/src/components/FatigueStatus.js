import React from "react";
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  Activity,
  Thermometer,
  Droplet,
  Eye,
  Smile,
  Headphones,
} from "lucide-react";
import { useFatigueData } from "../hooks/useFatigueData";
import "./Css/FatigueStatus.css";

const THRESHOLDS = {
  TEMP_HIGH: 38.0,
  PERCLOS_MEDIUM: 25,
  PERCLOS_HIGH: 50,
  SPO2_LOW: 60,
  HR_LOW: 50,
  HR_HIGH: 110,
};

export default function FatigueStatusPanel() {
  const data = useFatigueData();

  // Calculate individual risk indicators
  const evaluateFactors = () => {
    const reasons = [];
    let overall = "LOW";

    const temp = parseFloat(data.temperature) || 0;
    const perclos = parseFloat(data.perclos) || 0;
    const yawn = data.yawn_status || "Closed";
    const hr = parseFloat(data.hr) || 0;
    const spo2 = parseFloat(data.spo2) || 0;
    const eyeStatus = data.status || "Unknown";

    // Temperature check
    if (temp >= THRESHOLDS.TEMP_HIGH) {
      reasons.push("High body temperature");
      overall = "MEDIUM";
    }

    // PERCLOS check
    if (perclos >= THRESHOLDS.PERCLOS_HIGH) {
      reasons.push("High eye closure rate (PERCLOS)");
      overall = "HIGH";
    } else if (perclos >= THRESHOLDS.PERCLOS_MEDIUM && overall !== "HIGH") {
      reasons.push("Elevated eye closure rate");
      overall = "MEDIUM";
    }

    // Yawn detection
    if (yawn === "Yawning" || yawn === "Opening") {
      reasons.push("Frequent yawning detected");
      overall = "HIGH";
    }

    // SpO2 check
    if (spo2 && spo2 < THRESHOLDS.SPO2_LOW) {
      reasons.push("Low oxygen saturation");
      overall = "HIGH";
    }

    // Heart rate check
    if (hr && (hr < THRESHOLDS.HR_LOW || hr > THRESHOLDS.HR_HIGH)) {
      reasons.push("Abnormal heart rate");
      overall = "MEDIUM";
    }

    // Eye closed status
    if (eyeStatus === "Closed") {
      reasons.push("Eyes closed");
      overall = "HIGH";
    }

    return { overall, reasons };
  };

  const { overall, reasons } = evaluateFactors();

  const getIcon = (level) => {
    switch (level) {
      case "LOW":
        return <CheckCircle size={28} color="#16a34a" />;
      case "MEDIUM":
        return <AlertTriangle size={28} color="#ca8a04" />;
      case "HIGH":
        return <XCircle size={28} color="#dc2626" />;
      default:
        return <AlertTriangle size={28} color="#6b7280" />;
    }
  };

  return (
    <div className={`fatigue-panel ${overall.toLowerCase()}`}>
      <div className="header">
        <h2>Fatigue Monitoring Dashboard</h2>
        <div className="icon">{getIcon(overall)}</div>
      </div>

      <div className="metrics">
        <div className="metric">
          <Thermometer /> <span>Temperature:</span>
          <b>{data.temperature ? `${data.temperature.toFixed(1)} °C` : "—"}</b>
        </div>

        <div className="metric">
          <Activity /> <span>Heart Rate:</span>
          <b>{data.hr ? `${data.hr} bpm` : "—"}</b>
        </div>

        <div className="metric">
          <Droplet /> <span>SpO₂:</span>
          <b>{data.spo2 ? `${data.spo2}%` : "—"}</b>
        </div>

        <div className="metric">
          <Eye /> <span>PERCLOS:</span>
          <b>{data.perclos ? `${data.perclos.toFixed(1)}%` : "—"}</b>
        </div>

        <div className="metric">
          <Smile /> <span>Yawn:</span>
          <b>{data.yawn_status || "—"}</b>
        </div>

        <div className="metric">
          <Headphones /> <span>Eye Status:</span>
          <b>{data.status || "—"}</b>
        </div>
      </div>

      <div className="summary">
        <ul>
          {reasons.length > 0 ? (
            reasons.map((r, idx) => <li key={idx}>• {r}</li>)
          ) : (
            <li>All vitals normal</li>
          )}
        </ul>
      </div>
    </div>
  );
}
