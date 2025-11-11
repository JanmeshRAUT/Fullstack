import React from "react";
import { CheckCircle, AlertTriangle, XCircle } from "lucide-react";
import { useFatigueData } from "../hooks/useFatigueData";
import "./Css/DrowsinessIndicators.css"; // your posted CSS file

const THRESHOLDS = {
  TEMP_HIGH: 38.0,
  PERCLOS_MEDIUM: 25,
  PERCLOS_HIGH: 50,
  SPO2_LOW: 60,
  HR_LOW: 50,
  HR_HIGH: 110,
};

export default function FatigueIndicator() {
  const data = useFatigueData();

  // === EVALUATE FATIGUE LEVEL ===
  const evaluateFatigue = () => {
    let level = "LOW";

    const temp = parseFloat(data.temperature) || 0;
    const perclos = parseFloat(data.perclos) || 0;
    const yawn = data.yawn_status || "Closed";
    const hr = parseFloat(data.hr) || 0;
    const spo2 = parseFloat(data.spo2) || 0;
    const eyeStatus = data.status || "Unknown";

    // Temperature
    if (temp >= THRESHOLDS.TEMP_HIGH) level = "MEDIUM";

    // PERCLOS
    if (perclos >= THRESHOLDS.PERCLOS_HIGH) level = "HIGH";
    else if (perclos >= THRESHOLDS.PERCLOS_MEDIUM && level !== "HIGH")
      level = "MEDIUM";

    // Yawn detection
    if (yawn === "Yawning" || yawn === "Opening") level = "HIGH";

    // SpO₂ check
    if (spo2 && spo2 < THRESHOLDS.SPO2_LOW) level = "HIGH";

    // Heart rate
    if (hr && (hr < THRESHOLDS.HR_LOW || hr > THRESHOLDS.HR_HIGH)) {
      if (level !== "HIGH") level = "MEDIUM";
    }

    // Eye closed
    if (eyeStatus === "Closed") level = "HIGH";

    return level;
  };

  const level = evaluateFatigue();

  // === ICONS AND COLORS ===
  const getConfig = (lvl) => {
    switch (lvl) {
      case "LOW":
        return { label: "Alert", icon: <CheckCircle color="#16a34a" size={24} /> };
      case "MEDIUM":
        return { label: "Drowsy", icon: <AlertTriangle color="#ca8a04" size={24} /> };
      case "HIGH":
        return { label: "Fatigued", icon: <XCircle color="#dc2626" size={24} /> };
      default:
        return { label: "Unknown", icon: <AlertTriangle color="#6b7280" size={24} /> };
    }
  };

  const { label, icon } = getConfig(level);

  return (
    <div className="fatigue-indicator-container">
      <div className={`fatigue-indicator ${level.toLowerCase()}`}>
        <div className="indicator-icon">{icon}</div>
        <span className="indicator-label">{label}</span>
      </div>
    </div>
  );
}
