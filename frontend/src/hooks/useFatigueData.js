import { useState, useEffect } from "react";

export const useFatigueData = () => {
  const [data, setData] = useState({
    temperature: null,
    hr: null,
    spo2: null,
    perclos: null,
    ear: null,
    mar: null,
    status: "Loading...",
    yawn_status: "N/A",
    ml_fatigue_status: "Unknown",
    timestamp: null,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("http://localhost:5000/combined_data");
        const jsonData = await response.json();

        // jsonData structure: { sensor: {...}, perclos: {...}, prediction: {status, confidence, ...} }
        const sensor = jsonData.sensor || {};
        const perclos = jsonData.perclos || {};
        const mlData = jsonData.prediction || { status: "Unknown", confidence: 0 };

        setData({
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
          timestamp: Date.now(),
        });
      } catch (error) {
        console.error("Error fetching fatigue data:", error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000); // Poll faster (1s) for smoother updates
    return () => clearInterval(interval);
  }, []);

  return data;
};
