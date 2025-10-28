import { useState, useEffect } from 'react';

export const useSensorData = () => {
  const [sensorData, setSensorData] = useState({
    temperature: null,
    perclos: null,
    ax: null,
    ay: null,
    az: null,
    gz: null,
    status: 'Loading...',
    timestamp: null
  });

  const [dataHistory, setDataHistory] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:5000/sensor_data');
        const data = await response.json();

        // Create new data point with timestamp
        const newDataPoint = {
          time: new Date().toLocaleTimeString(),
          ...data
        };

        setSensorData(data);
        setDataHistory(prev => {
          const newHistory = [...prev, newDataPoint];
          return newHistory.slice(-20); // Keep last 20 points
        });

      } catch (error) {
        console.error('Error fetching sensor data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  return { sensorData, dataHistory };
};
