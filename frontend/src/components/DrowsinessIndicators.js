import React, { useEffect, useRef } from "react";
import { CheckCircle, AlertTriangle, XCircle, Volume2, VolumeX } from "lucide-react";
import { useFatigueData } from "../hooks/useFatigueData";
import "./Css/DrowsinessIndicators.css";

const THRESHOLDS = {
  TEMP_HIGH: 38.0,
  PERCLOS_MEDIUM: 33,
  PERCLOS_HIGH: 75,
  SPO2_LOW: 60,
  HR_LOW: 50,
  HR_HIGH: 110,
};

export default function FatigueIndicator() {
  const data = useFatigueData();
  const prevLevelRef = useRef("LOW");
  const audioRef = useRef(null);

  useEffect(() => {
    audioRef.current = new Audio("/sounds/alert.mp3"); 
    audioRef.current.loop = true; 
    audioRef.current.volume = 1.0;
    audioRef.current.preload = "auto";

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    };
  }, []);

  const evaluateFatigue = () => {
    // 1. Check Initialization (Direct)
    if (data.system_status === "Initializing") return "LOW";

    // 2. Check Initialization (Implicit via Prediction Status)
    if (data.ml_fatigue_status && data.ml_fatigue_status.startsWith("Initializing")) return "LOW";

    if (data.ml_fatigue_status && data.ml_fatigue_status !== 'Unknown' && data.ml_fatigue_status !== 'Error') {
      const ml = data.ml_fatigue_status;
      if (ml === "Fatigued") return "HIGH";
      if (ml === "Drowsy") return "MEDIUM";
      if (ml === "Alert") return "LOW";
    }

    let level = "LOW";

    const temp = parseFloat(data.temperature) || 0;
    const perclos = parseFloat(data.perclos) || 0;
    const yawn = data.yawn_status || "Closed";
    const hr = parseFloat(data.hr) || 0;
    const spo2 = parseFloat(data.spo2) || 0;
    const eyeStatus = data.status || "Unknown";

    if (temp >= THRESHOLDS.TEMP_HIGH) level = "MEDIUM";
    if (perclos >= THRESHOLDS.PERCLOS_HIGH) level = "HIGH";
    else if (perclos >= THRESHOLDS.PERCLOS_MEDIUM && level !== "HIGH")
      level = "MEDIUM";
    if (yawn === "Yawning" || yawn === "Opening") level = "HIGH";
    if (spo2 && spo2 < THRESHOLDS.SPO2_LOW) level = "HIGH";
    if (hr && (hr < THRESHOLDS.HR_LOW || hr > THRESHOLDS.HR_HIGH)) {
      if (level !== "HIGH") level = "MEDIUM";
    }
    if (eyeStatus === "Closed") level = "HIGH";

    return level;
  };

  const level = evaluateFatigue();

  const handleUserInteraction = () => {
    if (audioRef.current) {
      audioRef.current.play().then(() => {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        console.log("Audio Context Unlocked");
      }).catch(err => console.log("Audio unlock failed (harmless if already unlocked):", err));
    }
  };

  const [isMuted, setIsMuted] = React.useState(false);

  useEffect(() => {
    const prevLevel = prevLevelRef.current;
    
    // Safety check: Audio ref might be null if component unmounts
    const audio = audioRef.current;
    if (!audio) return;

    if (level === "HIGH" && prevLevel !== "HIGH") {
      if (!isMuted) {
          console.log("🚨 TRIGGERING ALARM SOUND!");
          audio.currentTime = 0;
          audio.play().catch((err) => console.error("Audio play BLOCKED:", err));
      }
    }

    // Force Stop if not HIGH or Muted
    if ((level !== "HIGH" || isMuted) && !audio.paused) {
         audio.pause();
         audio.currentTime = 0;
    }

    prevLevelRef.current = level;
  }, [level, isMuted]);

  const getConfig = (lvl) => {
    switch (lvl) {
      case "LOW":
        return { label: "NOMINAL", icon: <CheckCircle color="#16a34a" size={24} /> }; // Industry Term
      case "MEDIUM":
        return { label: "CAUTION", icon: <AlertTriangle color="#ca8a04" size={24} /> };
      case "HIGH":
        return { label: "CRITICAL", icon: <XCircle color="#dc2626" size={24} /> };
      default:
        return { label: "UNKNOWN", icon: <AlertTriangle color="#6b7280" size={24} /> };
    }
  };

  const { label, icon } = getConfig(level);

  return (
    <div className="fatigue-indicator-container">
      <div 
        className={`fatigue-indicator ${level.toLowerCase()}`} 
        onClick={handleUserInteraction}
        title="Status Indicator"
      >
        <div className="indicator-icon">{icon}</div>
        <span className="indicator-label" style={{marginRight: '8px'}}>{label}</span>
        
        <div 
            onClick={(e) => { 
                e.stopPropagation(); 
                setIsMuted(!isMuted); 
                // Don't call handleUserInteraction here to avoid double-trigger logic if needed, 
                // but actually we want to ensure Audio Context is unlocked, so it's fine.
                handleUserInteraction();
            }}
            title={isMuted ? "Unmute Alarm" : "Mute Alarm"}
            style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                padding: '4px',
                borderRadius: '4px',
                background: 'rgba(255,255,255,0.2)',
                cursor: 'pointer',
                transition: 'background 0.2s'
            }}
            className="mute-btn"
        >
            {isMuted ? <VolumeX size={14} color="white" /> : <Volume2 size={14} color="white" />}
        </div>
      </div>
    </div>
  );
}
