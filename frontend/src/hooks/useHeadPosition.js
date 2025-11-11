import { useState, useEffect } from "react";

export const useHeadPosition = () => {
  const [positions, setPositions] = useState([]);

  useEffect(() => {
    const fetchPosition = async () => {
      try {
        const res = await fetch("http://127.0.0.1:5000/head_position");
        const data = await res.json();

        if (data && data.position) {
          setPositions((prev) => {
            const newData = [...prev, data.position];
            if (newData.length > 20) newData.shift(); // keep recent 20 readings
            return newData;
          });
        }
      } catch (error) {
        console.error("Error fetching head position:", error);
      }
    };

    fetchPosition();
    const interval = setInterval(fetchPosition, 1500); // fetch every 1.5 sec

    return () => clearInterval(interval);
  }, []);

  return positions;
};
