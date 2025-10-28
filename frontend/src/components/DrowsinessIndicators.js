  import React from "react";
  import { useFatigueData } from "../hooks/useFatigueData";
  import "./Css/DrowsinessIndicators.css";

  const THRESHOLDS = {
    TEMP_HIGH: 38.0,
    PERCLOS_HIGH: 50,
    PERCLOS_MEDIUM: 25,
  };
  

  export default function DrowsinessIndicators() {
    const data = useFatigueData();

    const getIndicatorClass = (type, value) => {
      if (value === null) return "unknown";
      switch (type) {
        case "temperature":
          return value >= THRESHOLDS.TEMP_HIGH ? "danger" : "normal";
        case "perclos":
          return value >= THRESHOLDS.PERCLOS_HIGH
            ? "danger"
            : value >= THRESHOLDS.PERCLOS_MEDIUM
            ? "warning"
            : "normal";
        default:
          return "normal";
      }
    };

    return (
      <div className="card indicators">
        <h4>Real-time Drowsiness Indicators</h4>

        <div className={`indicator ${getIndicatorClass("perclos", data.perclos)}`}>
          <span className="label">PERCLOS:</span>
          <span className="value">
            {data.perclos !== null && data.perclos !== undefined
              ? `${data.perclos.toFixed(1)}%`
              : "N/A"}
          </span>
          <span className="status">
            {data.perclos === null ? "No Data" : data.status}
          </span>
        </div>

        <div
          className={`indicator ${getIndicatorClass(
            "temperature",
            data.temperature
          )}`}
        >
          <span className="label">Temperature:</span>
          <span className="value">
            {data.temperature !== null && data.temperature !== undefined
              ? `${data.temperature.toFixed(1)}°C`
              : "N/A"}
          </span>
        </div>

        {/* === Yawn Detection Display === */}
        <div className="indicator normal">
          <span className="label">Yawn:</span>
          <span className="value">
            {data.yawn_status || "N/A"}
          </span>
        </div>

        <div className="update-time">
          Updated: {new Date().toLocaleTimeString()}
        </div>
      </div>
    );
  }
