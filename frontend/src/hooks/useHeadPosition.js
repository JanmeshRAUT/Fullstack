import { useState, useEffect } from "react";
import { useFatigueContext } from "../context/FatigueContext";

export const useHeadPosition = () => {
    const { fullData } = useFatigueContext();

    // Target values from Context
    const targetX = fullData?.head_position?.angle_x || 0;
    const targetY = fullData?.head_position?.angle_y || 0;
    const targetZ = fullData?.head_position?.angle_z || 0;
    const targetSource = fullData?.head_position?.source || "Unknown";
    const targetCalibrated = fullData?.head_position?.calibrated !== undefined ? fullData.head_position.calibrated : true;
    const targetPos = fullData?.head_position?.position || "Center";
    
    // NEW: Get MAR (Mouth Aspect Ratio)
    // MAR is typically 0.0 (closed) to 1.0 (wide open). Normal talking is 0.1-0.3. Yawn > 0.5.
    const targetMar = fullData?.perclos?.mar || 0;

    const [current, setCurrent] = useState({
        x: 0, y: 0, z: 0, 
        source: "Unknown", 
        calibrated: true,
        position: "Center",
        targetX: 0, targetY: 0, targetZ: 0,
        mar: 0
    });

    useEffect(() => {
        let animationFrameId;

        const animate = () => {
            setCurrent(prev => {
                const ALPHA = 0.1; // Smooth factor
                const MAR_ALPHA = 0.2; // Jaw acts faster than head
                const DEADZONE = 1.0; 
                
                // ... (Existing Clamping Logic) ...
                const clampedTargetX = Math.max(-40, Math.min(40, targetX));
                const clampedTargetY = Math.max(-45, Math.min(45, targetY));
                const clampedTargetZ = Math.max(-20, Math.min(20, targetZ));

                // ... (Existing Deadzone Logic) ...
                const dx = Math.abs(clampedTargetX - prev.targetX);
                const dy = Math.abs(clampedTargetY - prev.targetY);
                const dz = Math.abs(clampedTargetZ - prev.targetZ);
                
                let effectiveX = prev.targetX;
                let effectiveY = prev.targetY;
                let effectiveZ = prev.targetZ;

                if (dx > DEADZONE) effectiveX = clampedTargetX;
                if (dy > DEADZONE) effectiveY = clampedTargetY;
                if (dz > DEADZONE) effectiveZ = clampedTargetZ;

                const visualTargetZ = effectiveZ * 0.5;

                // LERP
                let nextX = prev.x + (effectiveX - prev.x) * ALPHA;
                let nextY = prev.y + (effectiveY - prev.y) * ALPHA;
                let nextZ = prev.z + (visualTargetZ - prev.z) * ALPHA;
                
                // LERP MAR (Jaw)
                // Normalize visual opening: MAR 0.0 -> 0, MAR 0.6 -> 1 (Max open)
                const nextMar = prev.mar + (targetMar - prev.mar) * MAR_ALPHA;

                // Settle check
                if (Math.abs(nextX - effectiveX) < 0.1) nextX = effectiveX;
                if (Math.abs(nextY - effectiveY) < 0.1) nextY = effectiveY;
                if (Math.abs(nextZ - visualTargetZ) < 0.1) nextZ = visualTargetZ;
                
                // Stop rendering if absolutely nothing changed
                if (nextX === prev.x && nextY === prev.y && nextZ === prev.z && Math.abs(nextMar - prev.mar) < 0.001) {
                    return prev; 
                }

                return {
                    x: nextX,
                    y: nextY,
                    z: nextZ,
                    mar: nextMar,
                    source: targetSource,
                    calibrated: targetCalibrated,
                    position: targetPos,
                    targetX: effectiveX, 
                    targetY: effectiveY,
                    targetZ: effectiveZ
                };
            });
            animationFrameId = requestAnimationFrame(animate);
        };

        animate();

        return () => cancelAnimationFrame(animationFrameId);
    }, [targetX, targetY, targetZ, targetSource, targetCalibrated, targetPos, targetMar]);

    return {
        position: current.position,
        angle_x: current.x,
        angle_y: current.y,
        angle_z: current.z,
        mar: current.mar,
        source: current.source,
        calibrated: current.calibrated
    };

};
