import { useState, useEffect, useRef } from "react";

export const useHeartRate = () => {
  const [heartRates, setHeartRates] = useState([]);
  const timeRef = useRef(0);

  useEffect(() => {
    const fetchHeartRate = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5000/combined_data");
        const result = await response.json();

        const hr = result.sensor?.hr ?? 0; 
        if (hr !== null) {
          timeRef.current += 2;
          const newData = { time: timeRef.current, bpm: hr };
          setHeartRates((prev) => [...prev.slice(-19), newData]); 
        }
      } catch (error) {
        console.error("Error fetching heart rate:", error);
      }
    };

    const interval = setInterval(fetchHeartRate, 2000); 
    return () => clearInterval(interval);
  }, []);

  return heartRates;
};
