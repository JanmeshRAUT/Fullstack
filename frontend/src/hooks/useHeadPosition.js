import { useState, useEffect } from 'react';

export const useHeadPosition = () => {
  const [headPosition, setHeadPosition] = useState([]);

  useEffect(() => {
    const fetchHeadPosition = async () => {
      try {
        const response = await fetch('http://localhost:5000/sensor_data');
        const data = await response.json();
        
        // Calculate head position based on accelerometer data
        let position = "Center";
        if (data.ax > 0.3) position = "Right";
        else if (data.ax < -0.3) position = "Left";
        
        setHeadPosition(prev => [...prev.slice(-9), position]);
      } catch (error) {
        console.error('Error fetching head position:', error);
      }
    };

    fetchHeadPosition();
    const interval = setInterval(fetchHeadPosition, 5000);
    return () => clearInterval(interval);
  }, []);

  return headPosition;
};
