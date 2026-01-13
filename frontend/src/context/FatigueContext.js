import React, { createContext, useContext, useState, useEffect } from 'react';
import { API_BASE } from '../api';

const FatigueContext = createContext();

export const useFatigueContext = () => {
    return useContext(FatigueContext);
};

export const FatigueProvider = ({ children }) => {
    // ---------------- STATE ----------------
    // Centralized state for ALL components
    const [fullData, setFullData] = useState(null);
    
    // --- DERIVED / HISTORY STATES (Centralized Here) ---
    // Moved from useHeartRate
    const [heartRateHistory, setHeartRateHistory] = useState([]);
    
    // Moved from useSensorData
    const [tempHistory, setTempHistory] = useState([]);

    // ---------------- POLLING LOOP ----------------
    useEffect(() => {
        let isMounted = true;
        let timeTick = 0; // Relative time ticker

        const fetchData = async () => {
            try {
                // FETCH ONCE for the entire app!
                // Combined data contains sensor, perclos, head_position, prediction
                // Combined data contains sensor, perclos, head_position, prediction
                const response = await fetch(`${API_BASE}/combined_data`, {
                    headers: {
                        "ngrok-skip-browser-warning": "69420",
                        "Content-Type": "application/json"
                    }
                });
                if (!response.ok) throw new Error("Network response was not ok");
                
                const json = await response.json();
                
                if (isMounted) {
                    // Inject System Status
                    const richData = { ...json, status: "Active" };
                    setFullData(richData);
                    
                    // --- UPDATE HISTORIES ---
                    // 1. Heart Rate History
                    const hr = json.sensor?.hr ?? 0;
                    if (hr !== null) {
                         const newHrPoint = { time: timeTick, bpm: hr };
                         setHeartRateHistory(prev => {
                             // Keep last 20 points
                             const updated = [...prev, newHrPoint];
                             return updated.slice(-20);
                         });
                    }

                    // 2. Temperature History (formatted for Chart)
                    const temp = json.sensor?.temperature ?? 0;
                    const newTempPoint = {
                        time: new Date().toLocaleTimeString(),
                        temperature: temp
                    };
                    setTempHistory(prev => {
                        const updated = [...prev, newTempPoint];
                        return updated.slice(-20);
                    });
                    
                    timeTick += 1;
                }
            } catch (error) {
                console.error("[FatigueContext] Fetch Error:", error);
                if (isMounted) {
                    // Retain old data but mark as Offline if needed
                    // Or set a specific offline state
                     setFullData(prev => ({ ...prev, status: "Offline" }));
                }
            }
        };

        // Poll at 500ms (2Hz) - Good balance for Head Pose smoothness & Data Freshness
        // Previously: Sensor=3s, HR=2s, Head=100ms(!), Fatigue=1s
        // 100ms for Head was too aggressive for HTTP. 200-500ms is standard for HTTP polling.
        const interval = setInterval(fetchData, 500); 

        return () => {
             isMounted = false;
             clearInterval(interval);
        };
    }, []);

    // ---------------- REAL-TIME SOCKET HANDLER ----------------
    // Updates FAST data (CV: Perclos, HeadPose) without waiting for polling
    const updateRealTimeData = (wsData) => {
        setFullData(prev => {
            if (!prev) return prev; // Wait for initial poll to establish structure
            
            // Map WS data structure to FullData structure
            // WS returns: { ...perclos_fields, head_pose: { pitch, yaw, roll } }
            // FullData expects: { perclos: {...}, head_position: {...} }
            
            const newHeadPose = wsData.head_pose ? {
                angle_x: wsData.head_pose.pitch,
                angle_y: wsData.head_pose.yaw,
                angle_z: wsData.head_pose.roll,
                position: getPosLabel(wsData.head_pose.pitch, wsData.head_pose.yaw),
                source: "Vision (WS)",
                timestamp: Date.now()
            } : prev.head_position;

            return {
                ...prev,
                perclos: {
                    ...prev.perclos,
                    ...wsData, // Overwrite perclos fields (status, ear, mar, etc)
                    timestamp: wsData.timestamp || Date.now()
                },
                head_position: newHeadPose
            };
        });
    };

    // Helper for Head Position Label
    const getPosLabel = (pitch, yaw) => {
        let v = "";
        if (pitch > 10) v = "Down";
        else if (pitch < -10) v = "Up";
        
        let h = "";
        if (yaw > 10) h = "Right";
        else if (yaw < -10) h = "Left";
        
        const pos = `${v} ${h}`.trim();
        return pos || "Center";
    };

    // ---------------- EXPORT ----------------
    const value = {
        fullData,
        heartRateHistory,
        tempHistory,
        updateRealTimeData
    };

    return (
        <FatigueContext.Provider value={value}>
            {children}
        </FatigueContext.Provider>
    );
};
