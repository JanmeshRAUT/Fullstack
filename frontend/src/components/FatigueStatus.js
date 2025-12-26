import React from "react";
import { 
  Activity,
  Cpu
} from "lucide-react";
import { useFatigueData } from "../hooks/useFatigueData";

export default function FatigueStatus() {
  const data = useFatigueData();
  
  // Destructure Data
  const { 
    temperature = 0, 
    perclos = 0, 
    yawn_status = "None", 
    hr = 0,
    ml_fatigue_status = "Unknown",
    ml_confidence = 0 
  } = data || {};

  const safePerclos = typeof perclos === 'number' ? perclos : 0;
  const safeHR = typeof hr === 'number' ? hr : 0;
  const safeTemp = typeof temperature === 'number' ? temperature : 0;
  const safeYawn = yawn_status || "None";
  
  const normPerclos = Math.min(safePerclos / 100, 1);
  const normYawn = safeYawn === "Yawning" ? 1.0 : (safeYawn === "Opening" ? 0.5 : 0.0);
  const normHR = safeHR > 0 ? (safeHR > 100 ? (safeHR - 100)/50 : (safeHR < 60 ? (60-safeHR)/30 : 0)) : 0;
  
  const features = [
    { id: "f_perclos", label: "PERCLOS", value: normPerclos, raw: `${safePerclos.toFixed(1)}%` },
    { id: "f_yawn", label: "Yawn_Seq", value: normYawn, raw: safeYawn },
    { id: "f_hr", label: "HR_Var", value: Math.min(Math.max(normHR, 0), 1), raw: `${safeHR} bpm` },
    { id: "f_temp", label: "Temp_Delta", value: safeTemp > 37 ? (safeTemp - 37) : 0, raw: `${safeTemp.toFixed(1)}°C` }
  ];
  
  const sortedFeatures = [
      features.find(f => f.id === "f_perclos"),
      features.find(f => f.id === "f_yawn"),
      ...features.filter(f => f.id !== "f_perclos" && f.id !== "f_yawn").sort((a,b) => b.value - a.value)
  ];

  let predictedClass = "NORMAL";
  let confidence = ml_confidence; 
  let color = "low"; 

  const isNoFace = data.status === "No Face";

  if (ml_fatigue_status !== "Unknown" && ml_fatigue_status !== "Error") {
      if (isNoFace) {
          predictedClass = "SEARCHING";
          color = "medium";
          confidence = 0.0;
      } else if (ml_fatigue_status === "Waiting...") {
          predictedClass = "WAITING";
          color = "low";
          confidence = 0.0;
      } else {
          predictedClass = ml_fatigue_status.toUpperCase();
          
          if (predictedClass === "DROWSY") color = "medium";
          if (predictedClass === "FATIGUED") color = "high";
      }
  } else {
      predictedClass = "OFFLINE"; 
      confidence = 0.00; 
      color = "low"; 
  }

  const confidencePct = (confidence * 100).toFixed(1);

  return (
    <div style={{display: 'flex', flexDirection: 'column', height: '100%', gap: '16px'}}>
      
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
             <Cpu size={16} color="#6366f1" />
             <span style={{fontSize: '0.75rem', fontWeight: 700, color: '#64748b', letterSpacing: '1px'}}>RF_V3 INFERENCE</span>
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem', color: predictedClass === "OFFLINE" ? '#94a3b8' : '#16a34a', fontWeight: 600}}>
             <span style={{width: 6, height: 6, borderRadius: '50%', background: predictedClass === "OFFLINE" ? '#94a3b8' : '#16a34a', boxShadow: predictedClass === "OFFLINE" ? 'none' : '0 0 4px #16a34a'}}></span>
             {predictedClass === "OFFLINE" ? "OFFLINE" : "ONLINE"}
          </div>
      </div>

      <div className={`prediction-box ${color}`} style={{
          background: color === 'high' ? '#fef2f2' : (color === 'medium' ? '#fffbeb' : '#f0fdf4'),
          border: `1px solid ${color === 'high' ? '#fecaca' : (color === 'medium' ? '#fde68a' : '#bbf7d0')}`,
          borderRadius: '12px',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
      }}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
             <span style={{fontSize: '0.8rem', color: '#64748b', fontWeight: 600}}>PREDICTED CLASS</span>
             <span style={{fontSize: '2rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-1px', lineHeight: 1}}>
                {predictedClass}
             </span>
          </div>
          
          <div>
            <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '4px'}}>
               <span style={{fontSize: '0.7rem', color: '#64748b'}}>MODEL CONFIDENCE</span>
               <span style={{fontSize: '0.75rem', fontWeight: 700, color: '#0f172a'}}>{confidencePct}%</span>
            </div>
            <div style={{width: '100%', height: '6px', background: 'rgba(0,0,0,0.05)', borderRadius: '4px', overflow: 'hidden'}}>
               <div style={{
                   width: `${confidencePct}%`, 
                   height: '100%', 
                   background: color === 'high' ? '#ef4444' : (color === 'medium' ? '#f59e0b' : '#22c55e'),
                   borderRadius: '4px',
                   transition: 'width 0.5s ease'
               }}></div>
            </div>
          </div>
      </div>

      <div style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column'}}>
        <div style={{fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', marginBottom: '8px', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '6px'}}>
           <Activity size={12} /> LIVE FEATURE WEIGHTS
        </div>
        
        <div className="risk-list-container">
          <ul className="risk-factor-list">
             {sortedFeatures.map((feat) => (
                <li key={feat.id} className="risk-factor-item" style={{display: 'block'}}>
                   <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '4px'}}>
                       <span style={{fontSize: '0.75rem', fontWeight: 600, color: '#475569'}}>{feat.label}</span>
                       <span style={{fontSize: '0.7rem', fontFamily: 'monospace', color: '#0f172a'}}>{feat.raw}</span>
                   </div>
                   <div style={{width: '100%', display: 'flex', alignItems: 'center', gap: '8px'}}>
                       <div style={{flex: 1, height: '4px', background: '#f1f5f9', borderRadius: '2px'}}>
                          <div style={{
                             width: `${Math.min(feat.value * 100, 100)}%`, 
                             height: '100%', 
                             background: feat.value > 0.5 ? '#6366f1' : '#94a3b8', 
                             borderRadius: '2px',
                             transition: 'width 0.3s'
                          }}></div>
                       </div>
                       <span style={{fontSize: '0.65rem', fontFamily: 'monospace', color: '#cbd5e1', width: '30px', textAlign: 'right'}}>
                          {feat.value.toFixed(2)}
                       </span>
                   </div>
                </li>
             ))}
          </ul>
        </div>
      </div>

    </div>
  );
}
