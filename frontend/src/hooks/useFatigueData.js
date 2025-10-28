import { useState, useEffect } from 'react';

export const useFatigueData = () => {
  const [data, setData] = useState({
    temperature: null,
    perclos: null,
    status: 'Loading...',
    yawn_status: 'N/A',   // ✅ Added
    timestamp: null,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sensorRes, perclosRes] = await Promise.all([
          fetch('http://localhost:5000/sensor_data'),
          fetch('http://localhost:5000/perclos')
        ]);

        const sensorData = await sensorRes.json();
        const perclosData = await perclosRes.json();

        setData({
          temperature: sensorData.temperature,
          perclos: perclosData.perclos,
          status: perclosData.status,
          yawn_status: perclosData.yawn_status, // ✅ Added this line
          timestamp: Date.now(),
        });
      } catch (error) {
        console.error('Error fetching fatigue data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  return data;
};
