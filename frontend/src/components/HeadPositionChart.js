import React from "react";
import { useHeadPosition } from "../hooks/useHeadPosition";
import { useFatigueData } from "../hooks/useFatigueData";

export default function HeadPositionChart() {
  const { position, angle_x, angle_y, angle_z, source } = useHeadPosition();
  const { ml_fatigue_status } = useFatigueData();

  // Determine Safety Status
  const isSafe = Math.abs(angle_x) < 20 && Math.abs(angle_y) < 25 && Math.abs(angle_z) < 20;
  const statusColor = isSafe ? "#10b981" : "#ef4444";
  const statusText = isSafe ? "SAFE" : "DISTRACTED";
  
  // Drowsiness Visuals (Eye Opening)
  let eyeOpening = 4; // Default fully open (px height)
  if (ml_fatigue_status === "Drowsy") eyeOpening = 2; // Half open
  if (ml_fatigue_status === "Fatigued") eyeOpening = 0.5; // Almost closed
  
  // Source Logic
  const isSensor = source === "Sensor";
  const sourceColor = isSensor ? "#10b981" : (source === "Vision (Fallback)" ? "#f59e0b" : "#94a3b8");

  // CSS 3D Transforms
  const rotationStyle = {
    transform: `rotateX(${-angle_x}deg) rotateY(${angle_y}deg) rotateZ(${angle_z}deg)`,
    transition: "transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)" // Bouncy spring effect
  };

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", overflow: "hidden", borderRadius: "12px", background: "linear-gradient(to bottom, #f8fafc, #f1f5f9)" }}>
      
      {/* Background Radar Grid */}
      <div style={{
          position: "absolute", inset: 0, 
          backgroundImage: "radial-gradient(#cbd5e1 1px, transparent 1px)", 
          backgroundSize: "20px 20px", opacity: 0.5
      }}></div>

      {/* Source Badge */}
      <div style={{
          position: "absolute", top: 8, right: 8, 
          padding: "2px 6px", borderRadius: "4px",
          background: "rgba(255,255,255,0.8)", border: `1px solid ${sourceColor}`,
          color: sourceColor, fontSize: "0.6rem", fontWeight: 700, zIndex: 10
      }}>
          {source === "Vision (Fallback)" ? "VISION" : (source === "Sensor" ? "SENSOR" : "NONE")}
      </div>
      
      {/* POSITION METRIC OVERLAY (Like Temp Chart) */}
      <div style={{
          position: "absolute", top: 12, left: 16, zIndex: 1
      }}>
        <div style={{fontSize: "1.5rem", fontWeight: 800, color: "#334155", lineHeight: 1, letterSpacing: '-0.5px'}}>
            {position.toUpperCase()}
        </div>
        <div style={{fontSize: "0.7rem", color: "#94a3b8", fontWeight: 600}}>
            HEAD POSE
        </div>
      </div>
      
      {/* Central Crosshair */}
      <div style={{
          position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)",
          width: "120px", height: "120px", border: `2px dashed ${isSafe ? '#cbd5e1' : '#fecaca'}`, borderRadius: "50%",
          pointerEvents: "none", zIndex: 0
      }}></div>

      {/* 3D Scene */}
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", perspective: "800px", zIndex: 1 }}>
        
        {/* REAL STRUCTURED Head Model */}
        <div className="head-model-container" style={{ position: "relative", width: 80, height: 100, transformStyle: "preserve-3d", ...rotationStyle }}>
          
          {/* 1. CRANIUM (Top/Back) */}
          <div style={{
              position: "absolute", top: 0, left: 10, width: 60, height: 60,
              background: "#e2e8f0", borderRadius: "30px 30px 0 0",
              border: `1px solid ${statusColor}`, borderBottom: "none",
              transform: "translateZ(-10px)", opacity: 0.8
          }}></div>

          {/* 2. FACE PLATE (Front) */}
          <div style={{
             position: "absolute", top: 10, left: 10, width: 60, height: 50,
             background: isSafe ? "white" : "#fef2f2",
             border: `2px solid ${statusColor}`, borderRadius: "12px 12px 4px 4px",
             backfaceVisibility: "hidden",
             transform: "translateZ(20px)",
             display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 15,
             boxShadow: `0 0 10px ${statusColor}40`
          }}>
             {/* Eyes */}
             <div style={{display: 'flex', gap: 12}}>
                 <div style={{width: 14, height: eyeOpening, background: "#334155", borderRadius: 2, transition: "height 0.3s"}}></div>
                 <div style={{width: 14, height: eyeOpening, background: "#334155", borderRadius: 2, transition: "height 0.3s"}}></div>
             </div>
             {/* Nose Bridge */}
             <div style={{width: 4, height: 12, background: "#cbd5e1", margin: "4px 0", borderRadius: 2}}></div>
          </div>

          {/* 3. JAW (Bottom) */}
          <div style={{
             position: "absolute", bottom: 0, left: 15, width: 50, height: 35,
             background: "#cbd5e1",
             border: `1px solid ${statusColor}`, borderRadius: "4px 4px 16px 16px",
             transform: "translateZ(15px) rotateX(-10deg)",
             display: 'flex', justifyContent: 'center', alignItems: 'center'
          }}>
             {/* Mouth */}
             <div style={{width: 20, height: 3, background: "#94a3b8", borderRadius: 2, marginTop: 10}}></div>
          </div>

          {/* 4. SIDE PROFILE (Ears/Side Head) - Left */}
          <div style={{
             position: "absolute", top: 20, left: -5, width: 20, height: 50,
             background: "#cbd5e1", borderRadius: "10px 0 0 15px",
             border: `1px solid #94a3b8`, borderRight: 'none',
             transform: "rotateY(-90deg) translateZ(10px)"
          }}></div>

          {/* 5. SIDE PROFILE - Right */}
          <div style={{
             position: "absolute", top: 20, right: -5, width: 20, height: 50,
             background: "#cbd5e1", borderRadius: "0 10px 15px 0",
             border: `1px solid #94a3b8`, borderLeft: 'none',
             transform: "rotateY(90deg) translateZ(10px)"
          }}></div>

          {/* 6. BACK OF HEAD */}
          <div style={{
             position: "absolute", top: 10, left: 10, width: 60, height: 80,
             background: "#cbd5e1", borderRadius: "24px",
             border: "1px dashed #94a3b8",
             transform: "translateZ(-25px) rotateY(180deg)"
          }}></div>

        </div>
        
      </div>

      {/* Modern Overlay HUD */}
      <div style={{ position: "absolute", bottom: 12, left: 12, right: 12, display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
         
         {/* Live Metrics */}
         <div style={{ display: "flex", flexDirection: "column", gap: 2, fontSize: "0.65rem", fontFamily: "monospace", color: "#64748b" }}>
             <div style={{display:'flex', gap: 6}}> <span style={{width:10}}>P:</span> <span style={{color: '#334155', fontWeight: 700}}>{angle_x.toFixed(0)}°</span></div>
             <div style={{display:'flex', gap: 6}}> <span style={{width:10}}>Y:</span> <span style={{color: '#334155', fontWeight: 700}}>{angle_y.toFixed(0)}°</span></div>
             <div style={{display:'flex', gap: 6}}> <span style={{width:10}}>R:</span> <span style={{color: '#334155', fontWeight: 700}}>{angle_z.toFixed(0)}°</span></div>
         </div>

         {/* Status Badge */}
         <div style={{ 
             padding: "4px 8px", borderRadius: "6px", 
             background: isSafe ? "#d1fae5" : "#fee2e2", 
             color: statusColor, fontSize: "0.7rem", fontWeight: 800,
             border: `1px solid ${isSafe ? '#a7f3d0' : '#fecaca'}`
         }}>
             {statusText}
         </div>

      </div>

    </div>
  );
}
