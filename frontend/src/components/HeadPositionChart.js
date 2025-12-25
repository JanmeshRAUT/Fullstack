import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { RoundedBox, Environment, ContactShadows } from "@react-three/drei";
import { useHeadPosition } from "../hooks/useHeadPosition";
import { useFatigueData } from "../hooks/useFatigueData";

function HeadModel({ angles, fatigueStatus, mar }) {
  const group = useRef();
  const jawRef = useRef(); // Reference to the Jaw
  
  useFrame(() => {
    // 1. Head Rotation
    if (group.current) {
      // MAPPING: PITCH(X), YAW(Y), ROLL(Z)
      const radX = (angles.x * Math.PI) / 180;
      const radY = (-angles.y * Math.PI) / 180;
      const radZ = (-angles.z * Math.PI) / 180;
      group.current.rotation.set(radX, radY, radZ, 'YXZ');
    }

    // 2. Jaw Animation (Yawning/talking)
    if (jawRef.current) {
        // Map MAR (0 to 1.0) to Rotation (0 to 0.5 radians)
        // Normal talk: MAR ~0.1 -> 0.05 rad
        // Yawn: MAR ~0.6 -> 0.3 rad
        // We act on 'X' axis rotation (opening mouth down)
        const jawOpen = Math.min(0.6, mar) * 1.5; // Scale factor
        jawRef.current.rotation.x = jawOpen;
    }
  });

  // Eye Color based on Fatigue
  const eyeColor = fatigueStatus === "Fatigued" ? "#ef4444" : (fatigueStatus === "Drowsy" ? "#f59e0b" : "#10b981");
  const eyeScale = fatigueStatus === "Fatigued" ? 0.2 : (fatigueStatus === "Drowsy" ? 0.5 : 1);

  return (
    <group ref={group}>
      {/* HEAD SHAPE */}
      <RoundedBox args={[1.4, 1.8, 1.2]} radius={0.3} smoothness={4}>
        <meshStandardMaterial color="#e2e8f0" roughness={0.3} metalness={0.1} />
      </RoundedBox>

      {/* FACE PLATE (Visor area) */}
      <RoundedBox args={[1.1, 0.8, 0.1]} radius={0.1} smoothness={2} position={[0, 0, 0.61]}>
        <meshStandardMaterial color="#1e293b" roughness={0.2} metalness={0.8} />
      </RoundedBox>

      {/* EYES */}
      <group position={[0, 0.1, 0.68]}>
         {/* Left Eye */}
         <mesh position={[-0.25, 0, 0]} scale={[1, eyeScale, 1]}>
            <capsuleGeometry args={[0.08, 0.2, 4, 8]} />
            <meshStandardMaterial color={eyeColor} emissive={eyeColor} emissiveIntensity={2} />
         </mesh>
         
         {/* Right Eye */}
         <mesh position={[0.25, 0, 0]} scale={[1, eyeScale, 1]}>
            <capsuleGeometry args={[0.08, 0.2, 4, 8]} />
            <meshStandardMaterial color={eyeColor} emissive={eyeColor} emissiveIntensity={2} />
         </mesh>
      </group>

      {/* MOUTH (Simple Line on Face Plate - Stays with Head) */}
      <mesh position={[0, -0.4, 0.61]}>
         <boxGeometry args={[0.3, 0.05, 0.02]} />
         <meshStandardMaterial color="#475569" />
      </mesh>
      
      {/* JAW (Moving Part) - Anchored at ears almost */}
      {/* We group it to pivot correctly */}
      <group position={[0, -0.3, 0]} ref={jawRef}>
          {/* Actual Jaw Mesh */}
          <group position={[0, -0.5, 0]}> 
               {/* Chin Area */}
              <RoundedBox args={[1.0, 0.4, 1.0]} radius={0.1} smoothness={2}>
                 <meshStandardMaterial color="#cbd5e1" roughness={0.4} />
              </RoundedBox>
          </group>
      </group>

      {/* EARS */}
      <RoundedBox args={[0.2, 0.6, 0.4]} radius={0.05} smoothness={2} position={[-0.75, 0, 0]}>
         <meshStandardMaterial color="#cbd5e1" />
      </RoundedBox>
      <RoundedBox args={[0.2, 0.6, 0.4]} radius={0.05} smoothness={2} position={[0.75, 0, 0]}>
         <meshStandardMaterial color="#cbd5e1" />
      </RoundedBox>
      
      {/* NECK (Static visual anchor - NOT in rotating group if we wanted realistic neck, but for this chart simpler to be in group or separate) */}
      {/* If we put it OUTSIDE this group, it won't rotate with head (realistic).
          If INSIDE, it tilts. Let's keep it minimal. */}
    </group>
  );
}

export default function HeadPositionChart() {
  const { position, angle_x, angle_y, angle_z, source, calibrated, mar } = useHeadPosition(); // Need MAR here now
  const { ml_fatigue_status } = useFatigueData();
  
  // Logic for display
  const showCalibration = source === "Vision (Fallback)" && calibrated === false;
  
  // Status Logic
  const isSafe = Math.abs(angle_x) < 20 && Math.abs(angle_y) < 30 && Math.abs(angle_z) < 20;
  const statusColor = isSafe ? "#10b981" : "#ef4444";
  const statusText = isSafe ? "SAFE" : "DISTRACTED";


  return (
    <div style={{ width: "100%", height: "100%", position: "relative", borderRadius: "12px", overflow: "hidden", background: "linear-gradient(to bottom, #f8fafc, #e2e8f0)" }}>
        
        {/* OVERLAYS */}
        <div style={{ position: "absolute", top: 12, left: 16, zIndex: 10 }}>
            <div style={{fontSize: "1.5rem", fontWeight: 800, color: "#334155", lineHeight: 1}}>{position.toUpperCase()}</div>
            <div style={{fontSize: "0.7rem", color: "#64748b", fontWeight: 600}}>HEAD POSE</div>
        </div>

        <div style={{ position: "absolute", top: 8, right: 8, padding: "2px 6px", borderRadius: "4px", background: "rgba(255,255,255,0.8)", border: "1px solid #cbd5e1", color: "#64748b", fontSize: "0.6rem", fontWeight: 700, zIndex: 10 }}>
            {source === "Vision (Fallback)" ? "VISION" : (source === "Sensor" ? "SENSOR" : "NONE")}
        </div>

        {/* CALIBRATION OVERLAY */}
        {showCalibration && (
            <div style={{ position: 'absolute', inset: 0, zIndex: 50, background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(4px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div className="animate-spin" style={{ width: 32, height: 32, border: '4px solid #e2e8f0', borderTopColor: '#3b82f6', borderRadius: '50%', marginBottom: 12 }}></div>
                <div style={{fontSize: '1rem', fontWeight: 800, color: '#0f172a'}}>CALIBRATING</div>
                <div style={{fontSize: '0.75rem', fontWeight: 500, color: '#64748b'}}>Look at screen...</div>
            </div>
        )}

        {/* 3D SCENE */}
        <Canvas camera={{ position: [0, 0, 4], fov: 50 }}>
            <ambientLight intensity={0.5} />
            <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />
            <pointLight position={[-10, -10, -10]} intensity={0.5} />
            
            <HeadModel 
                angles={{ x: angle_x, y: angle_y, z: angle_z }} 
                fatigueStatus={ml_fatigue_status} 
                mar={mar}
            />
            
            <ContactShadows position={[0, -1.4, 0]} opacity={0.4} scale={10} blur={2.5} far={4} />
            <Environment preset="city" />
        </Canvas>

        {/* BOTTOM HUD */}
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
