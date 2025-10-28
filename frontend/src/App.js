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
      <h1 className="main-heading">Fatigue Detection System Dashboard</h1>
      <p className="subtitle">
        Real-time physiological monitoring, ML-driven drowsiness prediction, and{" "}
        <b>AI Interventions</b>
      </p>

      <div className="main-grid">
        <div className="left-section">
          <h2>Physiological Sensor Telemetry</h2>
          <div className="sensor-grid">
            <BodyTemperatureChart />
            <HeartRateChart />
            <HRVChart />
            <HeadPositionChart />
          </div>
        </div>

        <div className="right-section">
          <h2>ML & Camera Module</h2>
          <div className="ml-module">
            <CameraModule />
            <FatigueStatus />
            <DrowsinessIndicators />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
