import React from "react";
import "./Dashboard.css";
import BodyTemperatureChart from "./components/BodyTemperatureChart";
import HeartRateChart from "./components/HeartRateChart";
import HRVChart from "./components/HRVChart";
import HeadPositionChart from "./components/HeadPositionChart";
import CameraModule from "./components/CameraModule";
import FatigueStatus from "./components/FatigueStatus";
import DrowsinessIndicators from "./components/DrowsinessIndicators";

function App() {
  return (
    <div className="dashboard">
      <DrowsinessIndicators />
      <h1 className="main-heading">Fatigue Detection System Dashboard</h1>
      <p className="subtitle">
        Real-time physiological monitoring, ML-driven drowsiness prediction, and{" "}
        <b>AI Interventions</b>
      </p>

      <div className="main-grid">
        {/* LEFT SECTION: SENSOR CHARTS */}
        <div className="left-section">
          <h2>Physiological Sensor Telemetry</h2>
          <div className="sensor-grid">
            <BodyTemperatureChart />
            <HeartRateChart />
            <HRVChart />
            <HeadPositionChart />
          </div>
        </div>

        {/* RIGHT SECTION: CAMERA + FATIGUE STATUS */}
        <div className="right-section">
          <h2>ML & Camera Module</h2>
          <div className="ml-module">
            <CameraModule />

            {/* Sticky Fatigue Card */}
            <div className="fatigue-status-wrapper">
              <FatigueStatus />
            </div>
          </div>
        </div>
      </div>

      <div className="footer">
        <p>
          &copy; 2025 Fatigue Detection System. Developed by Realtime Error. All rights reserved.
        </p>
      </div>
    </div>
  );
}

export default App;
