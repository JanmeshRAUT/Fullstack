import React from "react";
import { Clock, CheckCircle, AlertTriangle, XCircle } from "lucide-react"; // lightweight icons
import { useFatigueData } from "../hooks/useFatigueData";
import "./Css/FatigueStatus.css";

const THRESHOLDS = {
  TEMP_HIGH: 38.0,
  PERCLOS_HIGH: 50,
  PERCLOS_MEDIUM: 25
};

export default function FatigueStatus() {
  const data = useFatigueData();

  const calculateFatigueLevel = () => {
    if (!data.temperature && !data.perclos) {
      return { level: "UNKNOWN", reasons: ["No Sensor Data"] };
    }

    const reasons = [];
    let level = "LOW";

    if (data.temperature >= THRESHOLDS.TEMP_HIGH) {
      level = "HIGH";
      reasons.push("High Temperature");
    }

    if (data.perclos >= THRESHOLDS.PERCLOS_HIGH) {
      level = "HIGH";
      reasons.push("High PERCLOS");
    } else if (data.perclos >= THRESHOLDS.PERCLOS_MEDIUM && level !== "HIGH") {
      level = "MEDIUM";
      reasons.push("Elevated PERCLOS");
    }

    return { level };
  };

  const { level } = calculateFatigueLevel();

  const getIcon = () => {
    switch (level) {
      case "LOW":
        return <CheckCircle size={28} color="#16a34a" />;
      case "MEDIUM":
        return <AlertTriangle size={28} color="#ca8a04" />;
      case "HIGH":
        return <XCircle size={28} color="#dc2626" />;
      default:
        return <AlertTriangle size={28} color="#64748b" />;
    }
  };

  return (
    <div className={`fatigue-status-card ${level.toLowerCase()}`}>
      <div className="left-icon">
        <Clock size={24} />
      </div>

      <div className="status-texts">
        <span className="label">OVERALL STATUS</span>
        <span className="level">{level}</span>
      </div>

      <div className="right-icon">{getIcon()}</div>
    </div>
  );
}
