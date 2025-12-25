import { useState, useEffect } from "react";

export const useHeadPosition = () => {
  const [headData, setHeadData] = useState({
    position: "Center",
    angle_x: 0,
    angle_y: 0,
    angle_z: 0
  });

  useEffect(() => {
    const fetchPosition = async () => {
      try {
        const res = await fetch("http://127.0.0.1:5000/combined_data");
        const json = await res.json();
        const data = json.head_position || {};

        if (data) {
          setHeadData(prev => ({
            position: data.position || "Center",
            // Smoothing (Lerp): 0.7 * prev + 0.3 * target
            angle_x: (prev.angle_x * 0.7) + ((data.angle_x || 0) * 0.3),
            angle_y: (prev.angle_y * 0.7) + ((data.angle_y || 0) * 0.3),
            angle_z: (prev.angle_z * 0.7) + ((data.angle_z || 0) * 0.3),
            source: data.source || "Unknown"
          }));
        }
      } catch (error) {
        console.error("Error fetching head position:", error);
      }
    };

    fetchPosition();
    const interval = setInterval(fetchPosition, 100); // 10Hz update for smoother animation

    return () => clearInterval(interval);
  }, []);

  return headData;
};
