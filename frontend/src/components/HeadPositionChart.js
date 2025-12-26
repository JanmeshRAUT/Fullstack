import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { RoundedBox, Environment, ContactShadows } from "@react-three/drei";
import { useHeadPosition } from "../hooks/useHeadPosition";
import { useFatigueData } from "../hooks/useFatigueData";

function HeadModel({ angles, fatigueStatus }) {
  const group = useRef();
  
  useFrame(() => {
    if (group.current) {
        const radX = (angles.x * Math.PI) / 180;
        const radY = (-angles.y * Math.PI) / 180;
        const radZ = (-angles.z * Math.PI) / 180;
        group.current.rotation.set(radX, radY, radZ, 'YXZ');
    }
  });

  const eyeColor = fatigueStatus === "Fatigued" ? "#ef4444" : (fatigueStatus === "Drowsy" ? "#f59e0b" : "#10b981");
  const eyeScale = fatigueStatus === "Fatigued" ? 0.2 : (fatigueStatus === "Drowsy" ? 0.5 : 1);

  return (
    <group ref={group}>
      <RoundedBox args={[1.4, 1.8, 1.2]} radius={0.3} smoothness={4}>
        <meshStandardMaterial color="#e2e8f0" roughness={0.3} metalness={0.1} />
      </RoundedBox>
      <RoundedBox args={[1.1, 0.8, 0.1]} radius={0.1} smoothness={2} position={[0, 0, 0.61]}>
        <meshStandardMaterial color="#1e293b" roughness={0.2} metalness={0.8} />
      </RoundedBox>

      <group position={[0, 0.1, 0.68]}>
         <mesh position={[-0.25, 0, 0]} scale={[1, eyeScale, 1]}>
            <capsuleGeometry args={[0.08, 0.2, 4, 8]} />
            <meshStandardMaterial color={eyeColor} emissive={eyeColor} emissiveIntensity={2} />
         </mesh>
         
         <mesh position={[0.25, 0, 0]} scale={[1, eyeScale, 1]}>
            <capsuleGeometry args={[0.08, 0.2, 4, 8]} />
            <meshStandardMaterial color={eyeColor} emissive={eyeColor} emissiveIntensity={2} />
         </mesh>
      </group>

      <mesh position={[0, -0.4, 0.68]}>
        <boxGeometry args={[0.3, 0.05, 0.02]} />
        <meshStandardMaterial color="#475569" />
      </mesh>

      <RoundedBox args={[0.2, 0.6, 0.4]} radius={0.05} smoothness={2} position={[-0.75, 0, 0]}>
         <meshStandardMaterial color="#cbd5e1" />
      </RoundedBox>
      <RoundedBox args={[0.2, 0.6, 0.4]} radius={0.05} smoothness={2} position={[0.75, 0, 0]}>
         <meshStandardMaterial color="#cbd5e1" />
      </RoundedBox>
      
      <cylinderGeometry args={[0.4, 0.5, 0.8, 32]} />
    </group>
  );
}

export default function HeadPositionChart() {
  const { position, angle_x, angle_y, angle_z, source, calibrated } = useHeadPosition();
  const { ml_fatigue_status } = useFatigueData();
  
  const showCalibration = source === "Vision (Fallback)" && calibrated === false;
  const isInitializing = source === "None" || source === "Unknown";
  const noFaceFound = ml_fatigue_status === "Unknown" && source === "Vision (Fallback)" && position === "Unknown";

  React.useEffect(() => {
    if (source === "Vision (Fallback)" && calibrated === true) {
        try {
            const audio = new Audio("/sounds/correct-356013.mp3");
            audio.volume = 0.5;
            audio.play().catch(e => console.error("Audio playback error:", e));
        } catch (e) {
            console.error("Audio initialization failed", e);
        }
    }
  }, [calibrated, source]);
  
  const isSafe = Math.abs(angle_x) < 20 && Math.abs(angle_y) < 30 && Math.abs(angle_z) < 20;
  const statusColor = isSafe ? "#10b981" : "#ef4444";
  const statusText = isSafe ? "SAFE" : "DISTRACTED";

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", borderRadius: "12px", overflow: "hidden", background: "linear-gradient(to bottom, #f8fafc, #e2e8f0)" }}>
        
        <div style={{ position: "absolute", top: 12, left: 16, zIndex: 10 }}>
            <div style={{fontSize: "1.5rem", fontWeight: 800, color: "#334155", lineHeight: 1}}>{position.toUpperCase()}</div>
            <div style={{fontSize: "0.7rem", color: "#64748b", fontWeight: 600}}>HEAD POSE</div>
        </div>

        <div style={{ position: "absolute", top: 8, right: 8, display: "flex", gap: "6px", alignItems: "center", zIndex: 10 }}>
            {/* RESET BUTTON for Cloud Calibration */}
            <button 
                onClick={async (e) => {
                    e.stopPropagation();
                    const { resetCalibration } = await import("../api");
                    await resetCalibration();
                }}
                title="Reset Calibration"
                style={{
                    background: "rgba(255,255,255,0.7)", 
                    border: "1px solid #cbd5e1", 
                    borderRadius: "4px", 
                    padding: "2px 6px", 
                    cursor: "pointer",
                    fontSize: "0.6rem", 
                    fontWeight: 700,
                    color: "#3b82f6",
                    transition: "all 0.2s"
                }}
                onMouseEnter={(e) => e.target.style.background = "#fff"}
                onMouseLeave={(e) => e.target.style.background = "rgba(255,255,255,0.7)"}
            >
                ↻
            </button> 

            <div style={{ padding: "2px 6px", borderRadius: "4px", background: "rgba(255,255,255,0.8)", border: "1px solid #cbd5e1", color: "#64748b", fontSize: "0.6rem", fontWeight: 700 }}>
                {source === "Vision (Fallback)" ? "VISION" : (source === "Sensor" ? "SENSOR" : "NONE")}
            </div>
        </div>

        {isInitializing && (
            <div style={{ position: 'absolute', inset: 0, zIndex: 55, background: 'rgba(241, 245, 249, 0.95)', backdropFilter: 'blur(8px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                <div className="animate-spin" style={{ width: 40, height: 40, border: '4px solid #e2e8f0', borderTopColor: '#6366f1', borderRadius: '50%' }}></div>
                <div style={{ textAlign: 'center' }}>
                    <div style={{fontSize: '0.9rem', fontWeight: 800, color: '#1e293b', letterSpacing: '1px'}}>INITIALIZING</div>
                    <div style={{fontSize: '0.65rem', fontWeight: 600, color: '#94a3b8'}}>WAITING FOR SENSORS...</div>
                </div>
            </div>
        )}

        {showCalibration && !isInitializing && (
            <div style={{ position: 'absolute', inset: 0, zIndex: 50, background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(4px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div className="animate-pulse" style={{ width: 32, height: 32, border: '4px solid #e2e8f0', borderTopColor: '#3b82f6', borderRadius: '50%', marginBottom: 12 }}></div>
                <div style={{fontSize: '1rem', fontWeight: 800, color: '#0f172a'}}>CALIBRATING</div>
                <div style={{fontSize: '0.75rem', fontWeight: 500, color: '#64748b'}}>Look straight at the camera...</div>
            </div>
        )}

        {noFaceFound && !isInitializing && !showCalibration && (
            <div style={{ position: 'absolute', inset: 0, zIndex: 45, background: 'rgba(248, 250, 252, 0.8)', backdropFilter: 'blur(4px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: '2px dashed #cbd5e1', margin: '12px', borderRadius: '12px' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>NO FACE DETECTED</div>
                <div style={{ fontSize: '0.65rem', fontWeight: 500, color: '#94a3b8', marginTop: '4px' }}>ENSURE FACE IS VISIBLE</div>
            </div>
        )}

        <Canvas camera={{ position: [0, 0, 4], fov: 50 }}>
            <ambientLight intensity={0.5} />
            <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />
            <pointLight position={[-10, -10, -10]} intensity={0.5} />
            
            <HeadModel 
                angles={{ x: angle_x, y: angle_y, z: angle_z }} 
                fatigueStatus={ml_fatigue_status} 
            />
            
            <ContactShadows position={[0, -1.4, 0]} opacity={0.4} scale={10} blur={2.5} far={4} />
            <Environment preset="city" />
        </Canvas>


        <div style={{ position: "absolute", bottom: 12, left: 12, right: 12, display: "flex", justifyContent: "space-between", alignItems: "flex-end", pointerEvents: "none" }}>
             <div style={{ display: "flex", flexDirection: "column", gap: 2, fontSize: "0.65rem", fontFamily: "monospace", color: "#64748b" }}>
                 <div>P: <span style={{color: '#334155', fontWeight: 700}}>{angle_x.toFixed(0)}°</span></div>
                 <div>Y: <span style={{color: '#334155', fontWeight: 700}}>{angle_y.toFixed(0)}°</span></div>
                 <div>R: <span style={{color: '#334155', fontWeight: 700}}>{angle_z.toFixed(0)}°</span></div>
             </div>
             <div style={{ padding: "4px 8px", borderRadius: "6px", background: isSafe ? "#d1fae5" : "#fee2e2", color: statusColor, fontSize: "0.7rem", fontWeight: 800, border: `1px solid ${isSafe ? '#a7f3d0' : '#fecaca'}` }}>
                 {statusText}
             </div>
        </div>
    </div>
  );
}
