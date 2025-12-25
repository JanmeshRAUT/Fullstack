import React, { useEffect, useState } from "react";
import "./Dashboard.css";
import { 
  Activity, 
  Thermometer, 
  BrainCircuit, 
  User,
  Heart
} from "lucide-react";

// Context
import { FatigueProvider } from "./context/FatigueContext";

// Components
import BodyTemperatureChart from "./components/BodyTemperatureChart";
import HeartRateChart from "./components/HeartRateChart";
import HRVChart from "./components/HRVChart";
import HeadPositionChart from "./components/HeadPositionChart";
import CameraModule from "./components/CameraModule";
import FatigueStatus from "./components/FatigueStatus";
import DrowsinessIndicators from "./components/DrowsinessIndicators";
import { useFatigueData } from "./hooks/useFatigueData";

// Wrapper Component to access Context for Theme
const DashboardContent = () => {
  const { ml_fatigue_status } = useFatigueData(); 
  
  // Determine Theme Class
  const themeClass = 
    ml_fatigue_status === "Fatigued" ? "theme-danger" : 
    (ml_fatigue_status === "Drowsy" ? "theme-warning" : "theme-safe");

  return (
    <div className={`dashboard-container ${themeClass}`}>
      {/* Floating Indicator */}
      <DrowsinessIndicators />

      {/* Top Header (Fixed Height) */}
      <header className="top-header">
        <div className="brand">
          <div className="brand-logo">
            <BrainCircuit size={20} />
          </div>
          <span className="brand-name">FatigueGuard Pro</span>
        </div>
        
        <div className="header-actions">
          <div className="status-badge">
            <span className="live-dot"></span>
            System Active
          </div>
          <div className="user-profile" style={{width: 32, height: 32, borderRadius: '50%', background: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <User size={16} color="#64748b" />
          </div>
        </div>
      </header>

      {/* Main Content (Fills remaining height) */}
      <main className="dashboard-content">
        
        <div className="grid-container">
          
          {/* Left Column: Data Charts */}
          <section className="charts-section">
            
            {/* Row 1: Vitals (Heart Rate & Temp) */}
            <div className="charts-row-1">
              <div className="card">
                <div className="card-header">
                  <span className="card-title"><Heart size={18} className="card-icon"/> Heart Rate</span>
                </div>
                <div className="chart-body-fill">
                   <HeartRateChart />
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                   <span className="card-title"><Thermometer size={18} className="card-icon"/> Temperature</span>
                </div>
                <div className="chart-body-fill">
                   <BodyTemperatureChart />
                </div>
              </div>
            </div>

            {/* Row 2: Secondary Metrics (HRV & Head) */}
            <div className="charts-row-2">
               <div className="card">
                  <div className="card-header">
                    <span className="card-title"><Activity size={18} className="card-icon"/> HRV Analysis</span>
                  </div>
                  <div className="chart-body-fill">
                    <HRVChart />
                  </div>
               </div>
               
               <div className="card">
                  <div className="card-header">
                    <span className="card-title"><User size={18} className="card-icon"/> Head Posture</span>
                  </div>
                  <div className="chart-body-fill">
                    <HeadPositionChart />
                  </div>
               </div>
            </div>

          </section>

          {/* Right Column: Status & Camera */}
          <aside className="side-panel">
            
            {/* Live Camera Feed (Now Top) */}
            <div className="card camera-card">
              <CameraModule />
            </div>

            {/* Fatigue Status Widget (Now Bottom) */}
            <div className="card fatigue-card">
               <div className="card-header">
                  <span className="card-title"><BrainCircuit size={18} className="card-icon"/> Fatigue Status</span>
               </div>
               <FatigueStatus />
            </div>

          </aside>

        </div>
      </main>
    </div>
  );
};

function App() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
      <FatigueProvider>
          <DashboardContent />
      </FatigueProvider>
  );
}

export default App;
