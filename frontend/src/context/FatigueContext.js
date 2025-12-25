import React, { createContext, useContext, useState, useEffect } from 'react';

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
                // http://localhost:5000/combined_data contains sensor, perclos, head_position, prediction
                const response = await fetch("http://localhost:5000/combined_data");
                if (!response.ok) throw new Error("Network response was not ok");
                
                const json = await response.json();
                
                if (isMounted) {
                    setFullData(json);
                    
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

    // ---------------- EXPORT ----------------
    const value = {
        fullData,
        heartRateHistory,
        tempHistory
    };

    return (
        <FatigueContext.Provider value={value}>
            {children}
        </FatigueContext.Provider>
    );
};
