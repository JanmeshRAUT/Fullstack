import { useFatigueContext } from "../context/FatigueContext";

export const useFatigueData = () => {
    const { fullData } = useFatigueContext();

    if (!fullData) {
        return {
            temperature: 0,
            hr: 0,
            spo2: 0,
            perclos: 0,
            ear: 0,
            mar: 0,
            status: "Loading...",
            yawn_status: "N/A",
            ml_fatigue_status: "Unknown",
            ml_confidence: 0,
            timestamp: null,
        };
    }

    const sensor = fullData.sensor || {};
    const perclos = fullData.perclos || {};
    const mlData = fullData.prediction || { status: "Unknown", confidence: 0 };

    return {
        temperature: sensor.temperature,
        hr: sensor.hr,
        spo2: sensor.spo2,
        perclos: perclos.perclos,
        ear: perclos.ear,
        mar: perclos.mar,
        status: perclos.status, // "Open" / "Closed"
        yawn_status: perclos.yawn_status,
        // Extract Detailed ML Data
        ml_fatigue_status: mlData.status || "Unknown",
        ml_confidence: mlData.confidence || 0,
        timestamp: fullData.server_time || Date.now(),
    };
};
